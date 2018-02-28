//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_FACT_H
#define BOTTOMUP_FACT_H


#include "constant.h"
#include "predicate.h"


namespace logic {
    using constant_ptr = std::shared_ptr<constant>;
    using fact_t = predicate<constant>;


    class fact: public fact_t {
    public:
        fact(const std::string &name, const std::vector<constant_ptr> &constants):
                fact_t(name, constants) {}

        friend std::ostream& operator<<(std::ostream& o, fact& f) {
            o << f.get_name() << "(";

            std::string separator = "";
            const auto &terms = f.get_terms();
            for (const auto &term: terms) {
                o << separator << term->get_name();
                separator = ", ";
            }
            o << ")";

            return o;
        }
    };
}


#endif //BOTTOMUP_FACT_H
