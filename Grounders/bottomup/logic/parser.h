//
// Created by wmatex on 25.2.18.
//

#ifndef BOTTOMUP_PARSER_H
#define BOTTOMUP_PARSER_H

#include <regex>
#include <memory>

#include "fact.h"
#include "term.h"
#include "rule.h"

namespace logic {

    class parser {
    private:
        std::regex _line_regex;
        std::regex _head_regex;
        std::regex _body_regex;

        std::vector<fact> _facts;
        std::vector<rule> _rules;

    public:
        parser();

        void parse(const char *filename);


        const std::vector<fact> &get_facts() const noexcept {
            return _facts;
        }

        const std::vector<rule> &get_rules() const noexcept {
            return _rules;
        }

    private:
        void add_rule(const std::string &name, const std::string &head, const std::string &body) noexcept;

        void add_fact(const std::string &name, const std::string &head) noexcept;


        template<typename T>
        std::vector<T> parse_head(const std::string &head) noexcept {
            std::vector<T> term_list;

            auto terms_begin =
                    std::sregex_iterator(head.begin(), head.end(), _head_regex);
            auto terms_end = std::sregex_iterator();

            for (auto i = terms_begin; i != terms_end; ++i) {
                const auto &match = *i;

                term_list.push_back(T(match[1].str()));
            }

            return term_list;
        }
    };

}


#endif //BOTTOMUP_PARSER_H
