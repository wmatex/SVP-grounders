//
// Created by wmatex on 28.2.18.
//

#include <unordered_map>
#include <list>

#include "grounder.h"
#include "logic/substitution_set.h"


grounder::grounder(const logic::parser &parser) noexcept :
    _facts(parser.get_facts()), _rules(parser.get_rules()), _grounded()
{
    preprocess();
}

void grounder::preprocess() noexcept {
    for (const auto &fact: _facts) {
        _grounded[fact.get_name()].insert(fact);
    }
}

const typename grounder::pred_fact_map& grounder::ground() {
    using namespace logic;

    bool done = false;

    while (!done) {
        size_t prev_size = _grounded.size();
        for (const auto &rule: _rules) {
            if (_grounded.count(rule.get_name()) < 1) {

                substitution_set<> subs_set;

                for (const auto &body_pred: rule.get_body()) {
                    auto substitutions = find_substitutions(body_pred);

                    if (!substitutions.empty()) {
                        for (auto &s: substitutions) {
                            subs_set.add_pred_substitution(body_pred, std::move(s));
                        }
                    } else {
                        break;
                    }
                }

                substitution_set<>::list valid_subs = subs_set.get_valid_substitutions();


                for (const auto &s: valid_subs) {
                    _grounded[rule.get_name()].insert(this->apply(s, rule));
                }
            }
        }

        done = _grounded.size() <= prev_size;
    }

    return _grounded;
}

std::vector<grounder::substitution> grounder::find_substitutions(const logic::rule::rule_t& rule) {
    try {
        const auto &grounds = _grounded.at(rule.get_name());

        return create_substitutions(rule, grounds);
    } catch (std::out_of_range &e) {
        return std::vector<grounder::substitution>();
    }
}

logic::fact grounder::apply(const substitution &substitution, const logic::rule &rule) const noexcept {
    const auto &vars = rule.get_terms();

    std::vector<logic::constant> head;
    for (const auto& var: vars) {
        head.emplace_back(substitution.at(var));
    }

    return logic::fact(rule.get_name(), head);
}

std::vector<grounder::substitution> grounder::create_substitutions(const logic::rule::rule_t &rule,
                                                                const std::unordered_set<logic::fact> &ground) {
    std::vector<grounder::substitution> substitutions;

    for (const auto &fact: ground) {
        grounder::substitution s;
        const auto &terms = rule.get_terms();
        for (int i = 0; i < terms.size(); ++i) {
            s.emplace(terms[i], fact[i]);
        }

        substitutions.push_back(std::move(s));
    }

    return substitutions;
}