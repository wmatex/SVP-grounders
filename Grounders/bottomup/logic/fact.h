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
        fact(std::string name, std::vector<constant_ptr> constants):
                fact_t(std::move(name), std::move(constants)) {}

    };
}


#endif //BOTTOMUP_FACT_H
