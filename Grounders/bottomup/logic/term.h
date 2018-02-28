//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_TERM_H
#define BOTTOMUP_TERM_H

#include <string>
#include "parser.h"

namespace logic {

    enum class term_type {
        constant,
        variable
    };

    class term {
    protected:
        std::string _name;

    public:
        explicit term(const std::string &name): _name(name) {}

        virtual ~term() noexcept = default;

        virtual term_type get_type() const noexcept = 0;

        const std::string& get_name() const noexcept {
            return _name;
        }

    };
}


#endif //BOTTOMUP_TERM_H
