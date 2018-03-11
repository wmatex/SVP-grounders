//
// Created by wmatex on 27.2.18.
//

#ifndef BOTTOMUP_TERM_H
#define BOTTOMUP_TERM_H

#include <string>

namespace logic {

    enum class term_type {
        constant,
        variable
    };

    class term {
    protected:
        std::string _name;

    public:
        term() = default;

        explicit term(std::string name): _name(std::move(name)) {}

        virtual ~term() noexcept = default;

        virtual term_type get_type() const noexcept = 0;

        const std::string& get_name() const noexcept {
            return _name;
        }

        bool operator!= (const term &other) const noexcept {
            return _name != other._name;
        }

    };
}

namespace std {
    template <>
    struct hash<logic::term> {
        size_t operator()(const logic::term &t) const noexcept {
            return std::hash<std::string>()(t.get_name());
        }
    };
}


#endif //BOTTOMUP_TERM_H
