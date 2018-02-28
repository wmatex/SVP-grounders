#include <iostream>

#include "logic/parser.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Missing input file" << std::endl;
        return 1;
    }

    logic::parser parser;

    parser.parse(argv[1]);

    const auto &facts = parser.get_facts();
    for (auto f: facts) {
        std::cout << f << std::endl;
    }

    return 0;
}