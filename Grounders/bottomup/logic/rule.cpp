//
// Created by wmatex on 28.2.18.
//

#include <memory>
#include <iostream>

#include "rule.h"

namespace logic {
    void rule::add_body(std::string name, std::vector<variable_ptr> variables) {
        _body.push_back(std::make_shared<rule_t>(std::move(name), std::move(variables)));
    }

    std::ostream &operator<<(std::ostream &o, const logic::rule &r) {
        o << r._name << "(";

        std::string sep;

        for (const auto &t: r._terms) {
            o << sep << t->get_name();
            sep = ", ";
        }
        o << ") :- ";

        sep = "";
        for (const auto &sub_r: r._body) {
            o << sep << *sub_r;
            sep = ", ";
        }

        return o;
    }
}
