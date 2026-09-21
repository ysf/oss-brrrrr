#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t *, std::size_t);

static int run(std::istream &input) {
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(input), {}};
    return LLVMFuzzerTestOneInput(data.data(), data.size());
}

int main(int argc, char **argv) {
    if (argc == 1)
        return run(std::cin);
    for (int i = 1; i < argc; ++i) {
        std::ifstream input(argv[i], std::ios::binary);
        if (!input || run(input))
            return 1;
    }
    return 0;
}
