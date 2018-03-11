//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_CONSTANT_H
#define BOTTOMUP_CONSTANT_H

#include "term.h"

namespace logic {

    class constant : public term {
    public:
        explicit constant(std::string name): term(std::move(name)) {}
        constant() = default;
        constant(const constant&) = default;


        term_type get_type() const noexcept override {
            return term_type::constant;
        }

    };
}

namespace std {
    template <>
    struct hash<logic::constant> {
        size_t operator()(const logic::constant &t) const noexcept {
            return std::hash<std::string>()(t.get_name());
        }
    };
}

#endif //BOTTOMUP_CONSTANT_H
