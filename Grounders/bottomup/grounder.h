//
// Created by wmatex on 28.2.18.
//

#ifndef BOTTOMUP_GROUNDER_H
#define BOTTOMUP_GROUNDER_H

#include <vector>

#include "logic/rule.h"
#include "logic/fact.h"

class grounder {
    std::vector<logic::fact> _facts;
    std::vector<logic::rule> _rules;


public:
    grounder();
};


#endif //BOTTOMUP_GROUNDER_H
