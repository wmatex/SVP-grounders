//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_RULE_H
#define BOTTOMUP_RULE_H

#include "variable.h"
#include "predicate.h"

namespace logic {


    class rule: public predicate<variable> {
    public:
        using rule_t = predicate<variable>;

    protected:
        std::vector<rule_t> _body;

    public:
        rule(std::string name, std::vector<variable> variables):
                rule_t(std::move(name), std::move(variables)), _body() {}


        void add_body(std::string name, std::vector<variable> variables);

        const std::vector<rule_t>& get_body() const {
            return _body;
        }

        friend std::ostream& operator<<(std::ostream& o, const rule& r);
    };

}

namespace std {
    template<>
    struct hash<logic::rule> {
        size_t operator() (const logic::rule &r) const noexcept {
            return std::hash<std::string>()(r.get_string());
        }
    };
}


#endif //BOTTOMUP_RULE_H
