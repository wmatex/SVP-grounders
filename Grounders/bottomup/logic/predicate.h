//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_PREDICATE_H
#define BOTTOMUP_PREDICATE_H

#include <functional>

#include <vector>
#include <iostream>
#include <type_traits>
#include <memory>
#include <sstream>

#include "term.h"

namespace logic {

    template <typename T>
    class predicate {
    protected:
        std::string _name;
        std::vector<std::shared_ptr<T>> _terms;
        std::string _string_rep;

    public:
        explicit predicate(std::string name, std::vector<std::shared_ptr<T>> terms) noexcept :
                _name(std::move(name)), _terms(std::move(terms)), _string_rep("") {
            std::stringstream ss;
            ss << *this;
            _string_rep = ss.str();
        }

        predicate() noexcept = default;

        predicate(const predicate<T>&) = default;
        predicate(predicate<T>&&) noexcept = default;

        virtual ~predicate() = default;

        const std::string& get_name() const noexcept {
            return _name;
        }


//        void add_term(const T &term) noexcept {
//            _terms.push_back(term);
//        }

        const std::shared_ptr<T>& operator[](size_t index) const {
            return _terms[index];
        }

        bool operator==(const predicate<T> &other) const noexcept {
            return _string_rep == other._string_rep;
        }

        const std::vector<std::shared_ptr<T>>& get_terms() const {
            return _terms;
        }

        size_t arity() const noexcept {
            return _terms.size();
        }

        const std::string get_string() const noexcept {
            return _string_rep;
        }

        friend std::ostream& operator<<(std::ostream& o, const predicate<T>& f) {
            if (f._string_rep.size() > 0) {
                o << f._string_rep;
            } else {
                o << f._name << "(";

                std::string sep;
                for (const auto &term: f._terms) {
                    o << sep << term->get_name();
                    sep = ", ";
                }
                o << ")";
            }

            return o;
        }

    };

    struct ptr_hash {
        template <typename T>
        std::size_t operator() (std::shared_ptr<T> const &p) const {
            return std::hash<T>()(*p);
        }
    };
    struct ptr_compare {
        template <typename T>
        size_t operator() (std::shared_ptr<T> const &a,
                           std::shared_ptr<T> const &b) const {
            return *a == *b;
        }
    };
}

namespace std {
    template <typename T>
    struct hash<logic::predicate<T>> {
        size_t operator()(const logic::predicate<T> &p) const noexcept {
            return std::hash<std::string>()(p.get_string());
        }
    };
}


#endif //BOTTOMUP_PREDICATE_H
