//
// Created by wmatex on 25.2.18.
//

#ifndef BOTTOMUP_PARSER_H
#define BOTTOMUP_PARSER_H

#include <regex>
#include <memory>

#include "fact.h"
#include "term.h"

namespace logic {

    class parser {
    private:
        std::regex _line_regex;
        std::regex _head_regex;

        std::vector<fact> _facts;

    public:
        parser();

        void parse(const char *filename);

        // get facts
        // get rules

        const std::vector<fact> &get_facts() noexcept {
            return _facts;
        }

    private:
        void add_rule(const std::string &name, const std::string &head, const std::string &body) noexcept;

        void add_fact(const std::string &name, const std::string &head) noexcept;


        template<typename T>
        std::vector<std::shared_ptr<T>> parse_head(const std::string &head) noexcept {
            std::vector<std::shared_ptr<T>> term_list;

            auto terms_begin =
                    std::sregex_iterator(head.begin(), head.end(), _head_regex);
            auto terms_end = std::sregex_iterator();

            for (std::sregex_iterator i = terms_begin; i != terms_end; ++i) {
                std::smatch match = *i;

                term_list.push_back(std::move(std::make_shared<T>(match[1].str())));
            }

            return std::move(term_list);
        }
    };

}


#endif //BOTTOMUP_PARSER_H
