//
// Created by wmatex on 25.2.18.
//

#include <fstream>
#include <iostream>
#include <regex>

#include "parser.h"

namespace logic {

    parser::parser() :
            _line_regex("([a-zA-Z_]+)\\(([^)]+?)\\)(\\s*:-\\s*(.*))?\\."),
            _head_regex("([a-zA-Z0-9_]+),?")
    {
    }

    void parser::parse(const char *filename) {
        const int NAME = 1;
        const int HEAD = 2;
        const int BODY = 4;
        std::ifstream source(filename);

        while (!source.eof()) {
            std::string line;
            std::getline(source, line);

            // Skip comments
            if (line[0] == '%') continue;

            std::smatch matches;
            if (std::regex_search(line, matches, _line_regex)) {
                if (matches[BODY].matched) {
                    this->add_rule(matches[NAME], matches[HEAD], matches[BODY]);
                } else {
                    this->add_fact(matches[NAME], matches[HEAD]);
                }
            }

        }
    }

    void parser::add_rule(const std::string &name, const std::string &head, const std::string &body) noexcept {
        std::cout << "Add rule: " << name << ", " << head << " = " << body << std::endl;
    }

    void parser::add_fact(const std::string &name, const std::string &head) noexcept {
        _facts.push_back(fact(name, parse_head<constant>(head)));
    }

}
