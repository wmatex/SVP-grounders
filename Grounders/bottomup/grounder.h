//
// Created by wmatex on 28.2.18.
//

#ifndef BOTTOMUP_GROUNDER_H
#define BOTTOMUP_GROUNDER_H

#include <vector>
#include <string>
#include <unordered_set>
#include <unordered_map>
#include <utility>

#include "logic/parser.h"
#include "logic/rule.h"
#include "logic/fact.h"
#include "logic/predicate.h"
#include "logic/substitution_set.h"

class grounder {
private:

public:
    using fact_set = std::unordered_set<std::shared_ptr<logic::fact>, logic::ptr_hash, logic::ptr_compare>;
    using pred_fact_map =
    std::unordered_map<
            std::string,
            fact_set
    >;

    std::vector<logic::fact> _facts;
    std::vector<logic::rule> _rules;

    pred_fact_map _grounded;


public:
    explicit grounder(const logic::parser &parser) noexcept;

    const pred_fact_map& ground();

    using substitution = logic::substitution_set<>::substitution;

    std::shared_ptr<logic::fact> apply(const substitution&, const logic::rule&) const noexcept;

private:
    void preprocess() noexcept;


    std::vector<substitution> find_substitutions(const logic::rule::rule_t& rule);

    std::vector<substitution> create_substitutions(const logic::rule::rule_t& rule, const fact_set& ground);
};


#endif //BOTTOMUP_GROUNDER_H
