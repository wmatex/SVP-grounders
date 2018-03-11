//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_FACT_H
#define BOTTOMUP_FACT_H


#include "constant.h"
#include "predicate.h"


namespace logic {

    class fact: public predicate<constant> {
    public:
        using fact_t = predicate<constant>;

        fact(std::string name, std::vector<constant> constants):
                fact_t(std::move(name), std::move(constants)) {}

    };
}

namespace std {
    template <>
    struct hash<logic::fact> {
        size_t operator()(const logic::fact &p) const noexcept {
            return std::hash<std::string>()(p.get_string());
        }
    };
}


#endif //BOTTOMUP_FACT_H
