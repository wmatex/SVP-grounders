#include "substitution_set.h"

using namespace logic;

template <typename V, typename C, typename P>
void substitution_set<V, C, P>::add_pred_substitution(const P &p, substitution s) noexcept {
    _map[p].push_back(std::move(s));
}

template <typename V, typename C, typename P>
typename substitution_set<V, C, P>::list substitution_set<V, C, P>::get_valid_substitutions() const noexcept {
    list subs_list;
    substitution substitution;

    auto iterator = _map.begin();
    update_substitutions(iterator, substitution, subs_list);

    return subs_list;
}

template <typename V, typename C, typename P>
void substitution_set<V, C, P>::update_substitutions(
        typename predicate_map::const_iterator iterator,
        typename substitution_set::substitution &substitution,
        typename substitution_set::list &subs_list) const {

    if (iterator == _map.end()) {
        subs_list.push_back(substitution);
        return;
    }

    const auto &possible_subs = iterator->second;

    for (const auto &sub: possible_subs) {
        bool valid = true;

        for (const auto &pair: sub) {
            if (substitution.count(pair.first) > 0) {
                // Valid substitution already exist
                if (substitution[pair.first] != pair.second) {
                    remove_all_assignments(sub, substitution);
                    valid = false;
                    break;
                }
            } else {
                substitution.insert(pair);
            }
        }

        if (valid) {
            update_substitutions(std::next(iterator), substitution, subs_list);
            remove_all_assignments(sub, substitution);
        }
    }
}


template <typename V, typename C, typename P>
void substitution_set<V, C, P>::remove_all_assignments(const substitution &source, substitution &dest) const noexcept {
    for (const auto& pair: source) {
        dest.erase(pair.first);
    }
}
