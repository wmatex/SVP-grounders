//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_CONSTANT_H
#define BOTTOMUP_CONSTANT_H

#include "term.h"

namespace logic {

    class constant : public term {
    public:
        explicit constant(const std::string &name): term(name) {}


        term_type get_type() const noexcept override {
            return term_type::constant;
        }

    };
}


#endif //BOTTOMUP_CONSTANT_H
