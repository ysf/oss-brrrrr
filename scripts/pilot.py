#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = tuple(path.stem for path in sorted((ROOT / "manifests").glob("*.json")))
PATH = "/usr/bin:/bin:/usr/local/bin"


def require_hosted():
    if not (os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.environ.get("GITHUB_REPOSITORY") == "ysf/oss-brrrrr"
            and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and os.environ.get("GITHUB_REF") == "refs/heads/main"
            and platform.system() == "Linux" and platform.machine() == "x86_64"):
        raise RuntimeError("Run only in ysf/oss-brrrrr on GitHub-hosted Linux x86-64")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def record(path):
    return {"sha256": digest(path), "size_bytes": path.stat().st_size}


def dump(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def command(*args):
    return subprocess.check_output(args, text=True, env={"PATH": PATH, "LC_ALL": "C"})


def recipe_identity(spec):
    paths = [f"manifests/{spec['project']}.json", spec["recipe"], "scripts/pilot.py",
             ".github/workflows/pilot.yml", "tests/test_integrity.py"]
    paths.extend(dependency["recipe"] for dependency in spec.get("dependencies", []))
    return {name: digest(ROOT / name) for name in sorted(set(paths))}


def identity(spec):
    image = os.environ.get("ImageVersion")
    if not image:
        raise RuntimeError("Missing GitHub runner ImageVersion; cannot identify toolchain")
    return {
        "inputs": recipe_identity(spec), "runner": spec["runner"],
        "image_version": image, "image_os": os.environ.get("ImageOS"),
        "os_release": Path("/etc/os-release").read_text(),
        "architecture": platform.machine(),
        "compiler": command("gcc", "--version"),
        "linker": command("ld", "--version"),
        "make": command("make", "--version"),
        "cmake": command("cmake", "--version") if spec["project"] in ("libpng", "harfbuzz", "simdjson", "wasm3", "c-ares", "c-blosc2", "libjxl", "muparser") else None,
        "binutils": command("objcopy", "--version"),
        "packages": command("dpkg-query", "-W", "-f=${Package}=${Version}\n")
    }


def origin():
    run = os.environ["GITHUB_RUN_ID"]
    return {"repository": "ysf/oss-brrrrr", "commit": os.environ["GITHUB_SHA"],
            "workflow": ".github/workflows/pilot.yml", "run_id": run,
            "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
            "url": f"https://github.com/ysf/oss-brrrrr/actions/runs/{run}"}


def stem(spec, version):
    return f"{spec['project']}-{version['version']}-linux-x86_64"


def dependency_stem(spec, dependency):
    return f"{spec['project']}-dependency-{dependency['name']}-{dependency['version']}"


def artifact_entries(spec):
    return [{"side": version["side"], "manifest": stem(spec, version) + ".json"}
            for version in spec["versions"]]


def adjacent_pairs(spec):
    return [{"pair_id": f"{spec['project']}-{before['version']}-{after['version']}",
             "before": stem(spec, before) + ".json", "after": stem(spec, after) + ".json",
             "pair_validation": "not-performed"}
            for before, after in zip(spec["versions"], spec["versions"][1:])]


def dependency_entries(spec):
    return [{"name": dependency["name"], "manifest": dependency_stem(spec, dependency) + ".json"}
            for dependency in spec.get("dependencies", [])]


def relative_path(value):
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or ".." in path.parts or "\\" in value
            or str(path) != value or value == "."):
        raise ValueError("Unsafe relative source path")
    return path


def validate_source(source, repository):
    revision = source["revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Source revision must be a full commit hash")
    repo = urllib.parse.urlsplit(repository)
    if (repo.scheme != "https" or repo.netloc != "github.com" or repo.query or repo.fragment
            or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo.path)):
        raise ValueError("Expected a GitHub source repository")
    expected_url = f"https://codeload.github.com{repo.path}/tar.gz/{revision}"
    if source["source_archive_url"] != expected_url:
        raise ValueError("Source archive URL must identify the repository's pinned commit")
    root = source["archive_root"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", root):
        raise ValueError("Unsafe source archive root")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", source["version"]):
        raise ValueError("Unsafe source version")
    relative_path(source["target"])
    if not isinstance(source["source_date_epoch"], int) or source["source_date_epoch"] < 0:
        raise ValueError("Invalid source timestamp")


def validate_spec(spec):
    if (spec["schema_version"] != 1 or spec["project"] not in PROJECTS
            or len(spec["versions"]) < 2
            or spec["runner"] != "ubuntu-24.04" or spec["architecture"] != "x86_64"
            or spec["format"] != "ELF64-little-endian" or spec["role"] != "library"
            or spec["parallel_jobs"] != 2):
        raise ValueError("Expected at least two releases of a Linux x86-64 library")
    for field in ("side", "version", "revision"):
        if len({version[field] for version in spec["versions"]}) != len(spec["versions"]):
            raise ValueError("Release identifiers must be unique")
    for version in spec["versions"]:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", version["side"]):
            raise ValueError("Unsafe release identifier")
        validate_source(version, spec["repository"])
    dependencies = spec.get("dependencies", [])
    if len({dependency["name"] for dependency in dependencies}) != len(dependencies):
        raise ValueError("Dependency names must be unique")
    for dependency in dependencies:
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", dependency["name"])
                or dependency["name"] == "install"):
            raise ValueError("Unsafe dependency name")
        validate_source(dependency, dependency["repository"])
    for component in [spec, *dependencies]:
        relative_path(component["recipe"])
        if not component["license"]["notice_sources"]:
            raise ValueError("At least one license notice is required")
        for name in component["license"]["notice_sources"]:
            relative_path(name)
    if any(not isinstance(limit, int) or limit <= 0 for limit in spec["limits"].values()):
        raise ValueError("Build limits must be positive integers")


def inventory_checksums(directory, files):
    names = sorted([*files, "pair.json"])
    return "".join(f"{digest(directory / name)}  {name}\n" for name in names)


def verify_inventory(directory, pair):
    files = pair["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("Empty or invalid inventory")
    for name, expected in files.items():
        if (not isinstance(name, str) or PurePosixPath(name).name != name
                or name in {".", "..", "pair.json", "SHA256SUMS"} or "\\" in name):
            raise ValueError("Unsafe inventory name")
        path = directory / name
        if path.is_symlink() or not path.is_file() or record(path) != expected:
            raise ValueError(f"Integrity mismatch: {name}")
    if {p.name for p in directory.iterdir()} != set(files) | {"pair.json", "SHA256SUMS"}:
        raise ValueError("Missing or unexpected files")
    for name in ("pair.json", "SHA256SUMS"):
        if (directory / name).is_symlink() or not (directory / name).is_file():
            raise ValueError("Invalid index file")
    if (directory / "SHA256SUMS").read_text() != inventory_checksums(directory, files):
        raise ValueError("Checksum index mismatch")


def inspect(binary, version):
    with binary.open("rb") as stream:
        header = stream.read(20)
    if (header[:6] != b"\x7fELF\x02\x01" or int.from_bytes(header[16:18], "little") != 3
            or int.from_bytes(header[18:20], "little") != 62):
        raise ValueError("Expected little-endian x86-64 ELF shared library")
    symbols = command("nm", "-D", "--defined-only", str(binary))
    names = {line.split()[-1].split("@")[0] for line in symbols.splitlines() if line.split()}
    if not set(version["required_defined_symbols"]) <= names:
        raise ValueError("Required library symbols not defined")
    if set(version["absent_defined_symbols"]) & names:
        raise ValueError("Unexpected library symbols defined")
    return command("readelf", "-h", "-d", "-n", "-S", str(binary)) + "\n" + symbols


def verify_provenance(meta, component, version, prefix, pair, spec):
    archive = meta["source"]["archive"]
    if (archive["archive_url"] != version["source_archive_url"]
            or archive["archive_root"] != version["archive_root"]
            or not re.fullmatch(r"[0-9a-f]{64}", archive["sha256"])
            or not isinstance(archive["size_bytes"], int)
            or not 0 < archive["size_bytes"] <= spec["limits"]["source_archive_bytes"]):
        raise ValueError("Source archive provenance mismatch")
    expected_source = {"repository": component["repository"], "revision": version["revision"],
                       "version": version["version"], "tag": version["tag"],
                       "source_date_epoch": version["source_date_epoch"], "archive": archive}
    expected_license = {**component["license"], "notice_file": prefix + ".LICENSE.txt",
                        "artifact_redistribution": "pending-release-review"}
    if (meta["schema_version"] != 1 or meta["pair_id"] != spec["pair_id"]
            or meta["project"] != spec["project"] or meta["source"] != expected_source
            or meta["build"]["identity"] != pair["identity"]
            or meta["build"]["origin"] != pair["build_origin"]
            or meta["build"]["recipe"] != component["recipe"]
            or meta["build"]["target"] != version["target"]
            or meta["build"]["parallel_jobs"] != spec["parallel_jobs"]
            or meta["build"]["log"] != prefix + ".build.log"
            or meta["license"] != expected_license):
        raise ValueError("Component provenance mismatch")


def verify(directory, spec, expected_identity=None):
    validate_spec(spec)
    pair = json.loads((directory / "pair.json").read_text())
    verify_inventory(directory, pair)
    if (pair["schema_version"] != 1 or pair["pair_id"] != spec["pair_id"]
            or pair["project"] != spec["project"] or pair["release_status"] != "provisional"
            or pair["pair_validation"] != "not-performed"
            or pair["artifacts"] != artifact_entries(spec) or pair["pairs"] != adjacent_pairs(spec)
            or pair["dependencies"] != dependency_entries(spec)):
        raise ValueError("Incomplete or inconsistent release series")
    if pair["identity"]["inputs"] != recipe_identity(spec):
        raise ValueError("Different build recipe or manifest")
    if expected_identity is not None and pair["identity"] != expected_identity:
        raise ValueError("Toolchain/image mismatch: reuse refused; dispatch a fresh build explicitly")
    build_origin = pair["build_origin"]
    if (build_origin["repository"] != "ysf/oss-brrrrr"
            or build_origin["workflow"] != ".github/workflows/pilot.yml"
            or not re.fullmatch(r"[0-9a-f]{40}", build_origin["commit"])
            or not re.fullmatch(r"[0-9]+", build_origin["run_id"])
            or not re.fullmatch(r"[0-9]+", build_origin["run_attempt"])
            or build_origin["url"] !=
            f"https://github.com/ysf/oss-brrrrr/actions/runs/{build_origin['run_id']}"):
        raise ValueError("Invalid build origin")
    expected_names = set()
    for dependency in spec.get("dependencies", []):
        prefix = dependency_stem(spec, dependency)
        expected_names.update(prefix + suffix for suffix in (".json", ".LICENSE.txt", ".build.log"))
        meta = json.loads((directory / (prefix + ".json")).read_text())
        verify_provenance(meta, dependency, dependency, prefix, pair, spec)
        if meta["name"] != dependency["name"] or meta["role"] != "build-dependency":
            raise ValueError("Dependency metadata mismatch")
        output = meta["built_output"]
        if (output["file"] != dependency["target"]
                or not re.fullmatch(r"[0-9a-f]{64}", output["sha256"])
                or not isinstance(output["size_bytes"], int) or output["size_bytes"] <= 0
                or any(meta.get(field) != dependency.get(field) for field in ("linkage", "bundled", "purpose"))):
            raise ValueError("Dependency build output mismatch")
    for version in spec["versions"]:
        prefix = stem(spec, version)
        expected_names.update(prefix + suffix for suffix in
                              (".so", ".so.debug", ".json", ".LICENSE.txt", ".elf.txt", ".build.log"))
        meta = json.loads((directory / (prefix + ".json")).read_text())
        verify_provenance(meta, spec, version, prefix, pair, spec)
        if (meta["side"] != version["side"] or meta["role"] != "library"
                or meta["architecture"] != "x86_64" or meta["format"] != spec["format"]
                or meta["change"] != spec["change"]
                or meta["dependencies"] != dependency_entries(spec)
                or meta["verification"] != {
                    "source_revision": "pinned-codeload-url",
                    "code_presence": "defined-dynamic-symbols-confirmed",
                    "required_defined_symbols": version["required_defined_symbols"],
                    "absent_defined_symbols": version["absent_defined_symbols"],
                    "pair_validation": "not-performed", "evidence": prefix + ".elf.txt"}):
            raise ValueError("Artifact provenance or status mismatch")
        for field, suffix in (("binary", ".so"), ("debug_symbols", ".so.debug")):
            name = prefix + suffix
            if meta[field] != {"file": name, **record(directory / name)}:
                raise ValueError("Artifact manifest hash mismatch")
        inspect(directory / (prefix + ".so"), version)
        debug_sections = command("readelf", "-S", str(directory / (prefix + ".so.debug")))
        if ".debug_info" not in debug_sections:
            raise ValueError("Missing separate DWARF information")
        debuglink = command("readelf", "--debug-dump=links", "--debug-dump=no-follow-links",
                            "--debug-dump=do-not-use-debuginfod", str(directory / (prefix + ".so")))
        if prefix + ".so.debug" not in debuglink:
            raise ValueError("Missing debug companion link")
    if set(pair["files"]) != expected_names:
        raise ValueError("Unexpected series contents")
    if sum(path.stat().st_size for path in directory.iterdir()) > spec["limits"]["corpus_bytes"]:
        raise ValueError("Corpus exceeds upload budget")
    return pair


def fetch_source(version, destination, limits):
    url = version["source_archive_url"]
    archive = destination / "source.tar.gz"
    with urllib.request.urlopen(url, timeout=60) as response, archive.open("xb") as output:
        if response.geturl() != url:
            raise ValueError("Unexpected source archive redirect")
        total = 0
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > limits["source_archive_bytes"]:
                raise ValueError("Source archive exceeds pilot budget")
            output.write(block)
    source = destination / "source"
    source.mkdir()
    expanded = 0
    with tarfile.open(archive) as bundle:
        for count, member in enumerate(bundle):
            parts = PurePosixPath(member.name).parts
            if (not parts or parts[0] != version["archive_root"] or ".." in parts
                    or "\\" in member.name or member.size < 0 or count >= 4096):
                raise ValueError("Unsupported source archive member")
            if member.issym():
                link = PurePosixPath(member.linkname)
                resolved = list(parts[:-1])
                if link.is_absolute() or "\\" in member.linkname:
                    raise ValueError("Unsafe source archive symlink")
                for part in link.parts:
                    if part == "..":
                        if len(resolved) == 1:
                            raise ValueError("Unsafe source archive symlink")
                        resolved.pop()
                    elif part != ".":
                        resolved.append(part)
                if not resolved or resolved[0] != version["archive_root"]:
                    raise ValueError("Unsafe source archive symlink")
                continue
            if not (member.isdir() or member.isfile()):
                raise ValueError("Unsupported source archive member")
            expanded += member.size
            if expanded > limits["source_expanded_bytes"]:
                raise ValueError("Expanded source exceeds pilot budget")
            target = source.joinpath(*parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as data, target.open("xb") as output:
                    shutil.copyfileobj(data, output)
                target.chmod(member.mode & 0o777)
    if not any(source.iterdir()):
        raise ValueError("Empty source archive")
    return source, {"archive_url": url, "archive_root": version["archive_root"], **record(archive)}


def build_component(spec, version, out, work, toolchain, build_origin, *, dependency=False):
    started = time.monotonic()
    component = version if dependency else spec
    location = work / "dependencies" / version["name"] if dependency else work / version["side"]
    location.mkdir()
    source, archive = fetch_source(version, location, spec["limits"])
    prefix = dependency_stem(spec, version) if dependency else stem(spec, version)
    with (out / (prefix + ".LICENSE.txt")).open("xb") as notice:
        for name in component["license"]["notice_sources"]:
            notice.write(f"===== {name} =====\n".encode())
            with (source / name).open("rb") as original:
                shutil.copyfileobj(original, notice)
            notice.write(b"\n")
    env = {"PATH": PATH, "HOME": str(location), "LC_ALL": "C", "TZ": "UTC",
           "CFLAGS": component["cflags"].format(source=source),
           "CXXFLAGS": component["cflags"].format(source=source),
           "LDFLAGS": component.get("ldflags", spec["ldflags"]),
           "SOURCE_DATE_EPOCH": str(version["source_date_epoch"]),
           "DEPENDENCY_PREFIX": str(work / "dependencies" / "install"),
           "GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted",
           "GITHUB_REPOSITORY": "ysf/oss-brrrrr"}
    log_path = ROOT / "diagnostics" / (prefix + ".build.log")
    with log_path.open("x") as log:
        subprocess.run(["sh", str(ROOT / component["recipe"]), version["target"]],
                       cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    shutil.copyfile(log_path, out / log_path.name)
    used = int(command("du", "-s", "-B1", str(work)).split()[0])
    if used > spec["limits"]["workspace_checkpoint_bytes"]:
        raise ValueError("Workspace checkpoint exceeds pilot budget")
    meta = {
        "schema_version": 1, "pair_id": spec["pair_id"], "project": spec["project"],
        "source": {"repository": component["repository"], "revision": version["revision"],
                   "version": version["version"], "tag": version["tag"],
                   "source_date_epoch": version["source_date_epoch"], "archive": archive},
        "build": {"identity": toolchain, "origin": build_origin, "recipe": component["recipe"],
                  "target": version["target"], "environment": env, "parallel_jobs": spec["parallel_jobs"],
                  "elapsed_seconds": round(time.monotonic() - started, 3),
                  "workspace_checkpoint_bytes": used, "log": log_path.name},
        "license": {**component["license"], "notice_file": prefix + ".LICENSE.txt",
                    "artifact_redistribution": "pending-release-review"}
    }
    if dependency:
        meta.update(name=version["name"], role="build-dependency",
                    built_output={"file": version["target"], **record(source / version["target"])})
        meta.update({field: version[field] for field in ("linkage", "bundled", "purpose") if field in version})
    else:
        binary = out / (prefix + ".so")
        debug = out / (prefix + ".so.debug")
        shutil.copyfile(source / version["target"], binary)
        command("objcopy", "--only-keep-debug", str(binary), str(debug))
        command("objcopy", "--strip-debug", str(binary))
        command("objcopy", "--add-gnu-debuglink=" + str(debug), str(binary))
        (out / (prefix + ".elf.txt")).write_text(inspect(binary, version))
        meta.update(
            side=version["side"], role=spec["role"], architecture=spec["architecture"],
            format=spec["format"], change=spec["change"], dependencies=dependency_entries(spec),
            binary={"file": binary.name, **record(binary)},
            debug_symbols={"file": debug.name, **record(debug)},
            verification={"source_revision": "pinned-codeload-url",
                          "code_presence": "defined-dynamic-symbols-confirmed",
                          "required_defined_symbols": version["required_defined_symbols"],
                          "absent_defined_symbols": version["absent_defined_symbols"],
                          "pair_validation": "not-performed", "evidence": prefix + ".elf.txt"},
            limitations=["Adjacent upstream releases, not single-change pairs; no vulnerability or correctness claim",
                         "No target binary execution, fuzzing or performance validation",
                         "Runner image and packages recorded, not a hermetic toolchain archive",
                         "Disk checkpoint is not a high-water mark; no whole-runner disk peak measured",
                         "Symbol presence is not proof of behavioral effect or code-path execution"])
    dump(out / (prefix + ".json"), meta)


def sample_disk(stop, metrics):
    while True:
        try:
            paths = [ROOT / name for name in ("build-work", "out", "reuse", "diagnostics")
                     if (ROOT / name).exists()]
            used = sum(int(command("du", "-s", "-B1", str(path)).split()[0]) for path in paths)
            metrics["workspace_sampled_peak_bytes"] = max(metrics.get("workspace_sampled_peak_bytes", 0), used)
            metrics["filesystem_min_free_bytes"] = min(
                metrics.get("filesystem_min_free_bytes", shutil.disk_usage(ROOT).free),
                shutil.disk_usage(ROOT).free)
            metrics["samples"] = metrics.get("samples", 0) + 1
        except (OSError, subprocess.SubprocessError) as error:
            metrics["sampling_error"] = str(error)
        if stop.wait(1):
            return


def build(spec):
    validate_spec(spec)
    started = time.monotonic()
    diagnostics = ROOT / "diagnostics"
    diagnostics.mkdir()
    report = {"status": "failed", "project": spec["project"], "current_run": origin(), "reuse": False}
    stop = threading.Event()
    metrics = {"sampling_interval_seconds": 1}
    sampler = threading.Thread(target=sample_disk, args=(stop, metrics), daemon=True)
    sampler.start()
    try:
        toolchain = identity(spec)
        out = ROOT / "out"
        reuse_run = os.environ.get("REUSE_RUN_ID", "")
        if reuse_run:
            if not reuse_run.isdecimal():
                raise ValueError("Invalid reuse run ID")
            pair = verify(ROOT / "reuse", spec, toolchain)
            shutil.copytree(ROOT / "reuse", out)
            report.update(reuse=True, reused_from_run_id=reuse_run,
                          original_build=pair["build_origin"])
        else:
            out.mkdir()
            work = ROOT / "build-work"
            work.mkdir()
            (work / "dependencies" / "install").mkdir(parents=True)
            build_origin = origin()
            for dependency in spec.get("dependencies", []):
                build_component(spec, dependency, out, work, toolchain, build_origin, dependency=True)
            for version in spec["versions"]:
                build_component(spec, version, out, work, toolchain, build_origin)
            files = {path.name: record(path) for path in sorted(out.iterdir())}
            pair = {"schema_version": 1, "pair_id": spec["pair_id"], "project": spec["project"],
                    "identity": toolchain, "build_origin": build_origin, "release_status": "provisional",
                    "pair_validation": "not-performed", "artifacts": artifact_entries(spec),
                    "pairs": adjacent_pairs(spec), "dependencies": dependency_entries(spec), "files": files}
            dump(out / "pair.json", pair)
            (out / "SHA256SUMS").write_text(inventory_checksums(out, files))
            verify(out, spec, toolchain)
        total = sum(p.stat().st_size for p in out.iterdir())
        if total > spec["limits"]["corpus_bytes"]:
            raise ValueError("Corpus exceeds pilot upload budget")
        report.update(status="passed", corpus_bytes=total)
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        stop.set()
        sampler.join()
        sample_disk(stop, metrics)
        report["disk"] = metrics
        report["script_elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["runner_job_seconds"] = None
        report["runner_disk_peak_bytes"] = None
        dump(diagnostics / "run.json", report)
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write("```json\n" + json.dumps(report, indent=2) + "\n```\n")


if __name__ == "__main__":
    require_hosted()
    if len(sys.argv) != 3 or sys.argv[1] not in ("build", "verify") or sys.argv[2] not in PROJECTS:
        raise SystemExit(f"usage: pilot.py build|verify {'|'.join(PROJECTS)} (GitHub-hosted Actions only)")
    spec = json.loads((ROOT / "manifests" / (sys.argv[2] + ".json")).read_text())
    if spec["project"] != sys.argv[2]:
        raise ValueError("Manifest project mismatch")
    if sys.argv[1] == "build":
        build(spec)
    else:
        verify(ROOT / "out", spec)
        print("Verified complete release series, inventory, pinned inputs, ELF symbols and separate debug information.")
