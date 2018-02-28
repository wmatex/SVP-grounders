//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_RULE_H
#define BOTTOMUP_RULE_H

#include "variable.h"
#include "predicate.h"

namespace logic {

    using rule_t = predicate<variable>;

    class rule: rule_t {
    public:
        rule(const std::string &name, const std::vector<variable> &variables): rule_t(name, variables) {}
    };
}


#endif //BOTTOMUP_RULE_H
