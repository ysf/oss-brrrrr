import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch

MODULE = importlib.util.spec_from_file_location("pilot", Path(__file__).resolve().parents[1] / "scripts/pilot.py")
pilot = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(pilot)
pilot.require_hosted()


class Integrity(unittest.TestCase):
    def test_reuse_rejects_corruption_extra_files_and_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            payload = directory / "sample.so"
            payload.write_bytes(b"not executed")
            pair = {"files": {payload.name: pilot.record(payload)}}
            (directory / "pair.json").write_text(json.dumps(pair))
            (directory / "SHA256SUMS").write_text(pilot.inventory_checksums(directory, pair["files"]))
            pilot.verify_inventory(directory, pair)
            payload.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                pilot.verify_inventory(directory, pair)
            payload.write_bytes(b"not executed")
            extra = directory / "extra"
            extra.write_text("unlisted")
            with self.assertRaises(ValueError):
                pilot.verify_inventory(directory, pair)
            extra.unlink()
            with self.assertRaises(ValueError):
                pilot.verify_inventory(directory, {"files": {"../escape": pilot.record(payload)}})

    def test_adjacent_pairs_share_one_middle_artifact(self):
        spec = {"project": "lz4", "versions": [
            {"side": "v1", "version": "1.9.2"},
            {"side": "v2", "version": "1.9.3"},
            {"side": "v3", "version": "1.9.4"}]}
        pairs = pilot.adjacent_pairs(spec)
        self.assertEqual([(pair["before"], pair["after"]) for pair in pairs], [
            ("lz4-1.9.2-linux-x86_64.json", "lz4-1.9.3-linux-x86_64.json"),
            ("lz4-1.9.3-linux-x86_64.json", "lz4-1.9.4-linux-x86_64.json")])
        self.assertEqual({pair[side] for pair in pairs for side in ("before", "after")},
                         {artifact["manifest"] for artifact in pilot.artifact_entries(spec)})

    def test_identity_ignores_other_projects_but_tracks_dependency_recipe(self):
        spec = {"project": "libpng", "recipe": "recipes/libpng.sh",
                "dependencies": [{"recipe": "recipes/zlib-dependency.sh"}]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(pilot, "ROOT", Path(temporary)):
            for name in ("manifests/libpng.json", "manifests/lz4.json", "recipes/lz4.sh",
                         "recipes/libpng.sh", "recipes/zlib-dependency.sh", "scripts/pilot.py",
                         ".github/workflows/pilot.yml", "tests/test_integrity.py"):
                path = pilot.ROOT / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            original = pilot.recipe_identity(spec)
            (pilot.ROOT / "manifests/lz4.json").write_text("unrelated manifest update")
            (pilot.ROOT / "recipes/lz4.sh").write_text("unrelated recipe update")
            self.assertEqual(pilot.recipe_identity(spec), original)
            (pilot.ROOT / "recipes/zlib-dependency.sh").write_text("changed dependency build")
            self.assertNotEqual(pilot.recipe_identity(spec), original)

    def test_source_requires_pinned_repository_url_and_safe_root(self):
        source = {"revision": "a" * 40, "version": "1.0", "target": "lib.so",
                  "source_date_epoch": 1, "archive_root": "library-" + "a" * 40,
                  "source_archive_url": "https://codeload.github.com/owner/library/tar.gz/" + "a" * 40}
        pilot.validate_source(source, "https://github.com/owner/library")
        for field, value in (
                ("source_archive_url", "https://codeload.github.com/other/library/tar.gz/" + "a" * 40),
                ("archive_root", "../library"), ("target", "/tmp/library.so")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                pilot.validate_source({**source, field: value}, "https://github.com/owner/library")

    def test_archive_extraction_rejects_escape_links_and_resource_overruns(self):
        source = {"source_archive_url": "https://codeload.github.com/owner/library/tar.gz/" + "a" * 40,
                  "archive_root": "library-" + "a" * 40}
        limits = {"source_archive_bytes": 65536, "source_expanded_bytes": 1024}
        cases = [
            ("valid", source["archive_root"] + "/notice", tarfile.REGTYPE, "", limits, True),
            ("safe-symlink", source["archive_root"] + "/nested/link", tarfile.SYMTYPE,
             "../notice", limits, True),
            ("wrong-root", "other/notice", tarfile.REGTYPE, "", limits, False),
            ("traversal", source["archive_root"] + "/../escape", tarfile.REGTYPE, "", limits, False),
            ("escape-symlink", source["archive_root"] + "/link", tarfile.SYMTYPE,
             "../escape", limits, False),
            ("archive-budget", source["archive_root"] + "/notice", tarfile.REGTYPE, "",
             {**limits, "source_archive_bytes": 1}, False),
            ("expanded-budget", source["archive_root"] + "/notice", tarfile.REGTYPE, "",
             {**limits, "source_expanded_bytes": 1}, False),
        ]
        for name, member_name, member_type, linkname, budget, valid in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                payload = io.BytesIO()
                with tarfile.open(fileobj=payload, mode="w:gz") as bundle:
                    if name == "safe-symlink":
                        notice = tarfile.TarInfo(source["archive_root"] + "/notice")
                        notice.size = 6
                        bundle.addfile(notice, io.BytesIO(b"notice"))
                    member = tarfile.TarInfo(member_name)
                    member.type = member_type
                    member.linkname = linkname
                    member.size = 6 if member_type == tarfile.REGTYPE else 0
                    bundle.addfile(member, io.BytesIO(b"notice") if member.size else None)
                response = io.BytesIO(payload.getvalue())
                response.geturl = lambda: source["source_archive_url"]
                directory = Path(temporary)
                with patch.object(pilot.urllib.request, "urlopen", return_value=response):
                    if valid:
                        extracted, archive = pilot.fetch_source(source, directory, budget)
                        self.assertEqual((extracted / "notice").read_bytes(), b"notice")
                        self.assertEqual(archive["sha256"], pilot.digest(directory / "source.tar.gz"))
                        self.assertFalse((extracted / "nested" / "link").exists())
                    else:
                        with self.assertRaises(ValueError):
                            pilot.fetch_source(source, directory, budget)
                        self.assertFalse((directory / "escape").exists())

    def test_series_rejects_duplicate_releases_and_dependency_names(self):
        spec = json.loads((pilot.ROOT / "manifests/libpng.json").read_text())
        pilot.validate_spec(spec)
        duplicate_release = copy.deepcopy(spec)
        duplicate_release["versions"][2] = copy.deepcopy(duplicate_release["versions"][1])
        with self.assertRaises(ValueError):
            pilot.validate_spec(duplicate_release)
        duplicate_dependency = copy.deepcopy(spec)
        duplicate_dependency["dependencies"].append(copy.deepcopy(duplicate_dependency["dependencies"][0]))
        with self.assertRaises(ValueError):
            pilot.validate_spec(duplicate_dependency)

    def test_all_project_manifests_are_valid(self):
        self.assertEqual(set(pilot.PROJECTS),
                         {path.stem for path in (pilot.ROOT / "manifests").glob("*.json")})
        for project in pilot.PROJECTS:
            with self.subTest(project=project):
                spec = json.loads((pilot.ROOT / "manifests" / f"{project}.json").read_text())
                pilot.validate_spec(spec)
                self.assertEqual(spec["project"], project)
                self.assertTrue((pilot.ROOT / spec["recipe"]).is_file())

    def test_series_requires_a_pair_and_covers_every_adjacent_release(self):
        spec = json.loads((pilot.ROOT / "manifests/zlib.json").read_text())
        versions = spec["versions"]
        for count in (0, 1):
            with self.subTest(count=count), self.assertRaises(ValueError):
                pilot.validate_spec({**spec, "versions": versions[:count]})
        for selected in (versions[:2], versions):
            series = {**spec, "versions": selected}
            pilot.validate_spec(series)
            pairs = pilot.adjacent_pairs(series)
            chain = [pairs[0]["before"], *[pair["after"] for pair in pairs]]
            self.assertEqual(chain, [entry["manifest"] for entry in pilot.artifact_entries(series)])
            self.assertTrue(all(left["after"] == right["before"]
                                for left, right in zip(pairs, pairs[1:])))
