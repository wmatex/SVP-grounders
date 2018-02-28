//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_RULE_H
#define BOTTOMUP_RULE_H

#include "variable.h"
#include "predicate.h"

namespace logic {

    using variable_ptr = std::shared_ptr<variable>;
    using rule_t = predicate<variable>;
    using rule_t_ptr = std::shared_ptr<rule_t>;

    class rule: public rule_t {
    protected:
        std::vector<rule_t_ptr> _body;

    public:
        rule(std::string name, const std::vector<variable_ptr> &variables):
                rule_t(std::move(name), variables), _body() {}


        void add_body(std::string name, std::vector<variable_ptr> variables);

        friend std::ostream& operator<<(std::ostream& o, const rule& r);
    };

}


#endif //BOTTOMUP_RULE_H
