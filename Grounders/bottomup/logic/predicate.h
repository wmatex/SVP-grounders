//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_PREDICATE_H
#define BOTTOMUP_PREDICATE_H

#include <functional>

#include <vector>
#include <iostream>
#include <type_traits>
#include <sstream>

#include "term.h"

namespace logic {

    template <typename T>
    class predicate {
    protected:
        std::string _name;
        std::vector<T> _terms;
        std::string _string_rep;

    public:
        explicit predicate(std::string name, std::vector<T> terms) noexcept :
                _name(std::move(name)), _terms(std::move(terms)), _string_rep("") {
            std::stringstream ss;
            ss << *this;
            _string_rep = ss.str();
        }

        predicate() noexcept = default;

        virtual ~predicate() = default;

        const std::string& get_name() const noexcept {
            return _name;
        }


//        void add_term(const T &term) noexcept {
//            _terms.push_back(term);
//        }

        const T& operator[](size_t index) const {
            return _terms[index];
        }

        bool operator==(const predicate<T> &other) const noexcept {
            return _string_rep == other._string_rep;
        }

        const std::vector<T>& get_terms() const {
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
                    o << sep << term.get_name();
                    sep = ", ";
                }
                o << ")";
            }

            return o;
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
