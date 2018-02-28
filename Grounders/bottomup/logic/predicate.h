//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_PREDICATE_H
#define BOTTOMUP_PREDICATE_H


#include <vector>
#include <type_traits>

#include "term.h"

namespace logic {
    template <typename T, typename = std::enable_if_t<std::is_base_of<term, T>::value> >
    class predicate {
    protected:
        std::string _name;
        std::vector<std::shared_ptr<T>> _terms;

    public:
        explicit predicate(const std::string &name, const std::vector<std::shared_ptr<T>> &terms) noexcept :
                _name(name), _terms(terms) {}

        predicate() noexcept = default;

        virtual ~predicate() = default;

        const std::string& get_name() const noexcept {
            return _name;
        }

//        void add_term(const T &term) noexcept {
//            _terms.push_back(term);
//        }

        T& operator[](size_t index) {
            return _terms[index];
        }

        const std::vector<std::shared_ptr<T>>& get_terms() const {
            return _terms;
        }

        size_t arity() const noexcept {
            return _terms.size();
        }

    };
}


#endif //BOTTOMUP_PREDICATE_H
