#include <iostream>

#include "logic/parser.h"
#include "grounder.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Missing input file" << std::endl;
        return 1;
    }


    logic::parser parser;
    for (int i = 1; i < argc; ++i) {
        parser.parse(argv[i]);
    }

//    for (const auto &f: parser.get_facts()) {
//        std::cout << f << std::endl;
//    }
//
//    for (const auto &r: parser.get_rules()) {
//        std::cout << r << std::endl;
//    }

    grounder g(parser);

    const auto &grounded = g.ground();

    for (const auto &pair: grounded) {
        for (const auto &fact: pair.second) {
            std::cout << *fact << "." << std::endl;
        }
    }

    return 0;
}