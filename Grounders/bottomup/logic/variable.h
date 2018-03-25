//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_VARIABLE_H
#define BOTTOMUP_VARIABLE_H

#include <unordered_map>

#include "term.h"

namespace logic {

    class variable: public term {
    public:
        explicit variable(const std::string &name) : term(name) {}

        term_type get_type() const noexcept override {
            return term_type::variable;
        }

        bool operator==(const variable &other) const noexcept {
            return _name == other._name;
        }
    };

}

namespace std {
    template <>
    struct hash<logic::variable> {
        size_t operator()(const logic::variable &t) const noexcept {
            return std::hash<std::string>()(t.get_name());
        }
    };
}


#endif //BOTTOMUP_VARIABLE_H
