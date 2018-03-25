//
// Created by wmatex on 25.2.18.
//

#include <fstream>
#include <iostream>
#include <regex>

#include "parser.h"
#include "variable.h"
#include "rule.h"

namespace logic {

    parser::parser() :
            _line_regex("([a-zA-Z_]+)\\(([^)]+?)\\)(\\s*:-\\s*(.*))?\\."),
            _head_regex("([a-zA-Z0-9_]+),?"),
            _body_regex("([a-zA-Z_]+)\\(([^)]+?)\\),?\\s*")
    {
    }

    void parser::parse(const char *filename) {
        const int NAME = 1;
        const int HEAD = 2;
        const int BODY = 4;
        std::ifstream source(filename);

        while (!source.eof() && source.is_open()) {
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
        auto head_terms = parse_head<variable>(head);

        auto body_begin = std::sregex_iterator(body.begin(), body.end(), _body_regex);
        auto body_end   = std::sregex_iterator();

        rule r(name, head_terms);

        for (auto i = body_begin; i != body_end; ++i) {
            const auto &match = *i;

            r.add_body(match[1].str(), parse_head<variable>(match[2].str()));
        }

        _rules.push_back(r);
    }

    void parser::add_fact(const std::string &name, const std::string &head) noexcept {
        _facts.emplace_back(name, parse_head<constant>(head));
    }

}
