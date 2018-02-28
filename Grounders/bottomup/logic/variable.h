//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_VARIABLE_H
#define BOTTOMUP_VARIABLE_H

#include "term.h"

namespace logic {
    class variable: public term {
    public:
        variable(const std::string &name) : term(name) {}

        term_type get_type() const noexcept override {
            return term_type::variable;
        }
    };
}


#endif //BOTTOMUP_VARIABLE_H
