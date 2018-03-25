//
// Created by wmatex on 10.3.18.
//

#ifndef BOTTOMUP_SUBSTITUTION_SET_H
#define BOTTOMUP_SUBSTITUTION_SET_H

#include <unordered_map>
#include <list>
#include <iostream>

#include "variable.h"
#include "constant.h"
#include "predicate.h"

namespace logic {

    template<typename Var = variable, typename Const = constant, typename Predicate = predicate<Var>>
    class substitution_set {
    public:
        using substitution = std::unordered_map<Var, std::shared_ptr<Const>>;
        using list = std::vector<substitution>;

        substitution_set() = default;

        void add_pred_substitution(const Predicate& p, substitution s) noexcept;

        list get_valid_substitutions() const noexcept;

        static void print(const substitution &s) {
            std::cout << "[ ";
            for (const auto& p: s) {
                std::cout << p.first.get_name() << "=>" << p.second->get_name() << ",";
            }
            std::cout << "]" << std::endl;
        }

    private:
        using predicate_map = std::unordered_map<
                Predicate,
                list
        >;

        void update_substitutions(
                typename predicate_map::const_iterator iterator,
                substitution& sub,
                list &subs_list
        ) const;

        void remove_all_assignments(const substitution& source, substitution& dest) const noexcept;

        predicate_map _map;
    };
}

#include "substitution_set.inl"

#endif //BOTTOMUP_SUBSTITUTION_SET_H
