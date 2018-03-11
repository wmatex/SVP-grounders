cmake_minimum_required(VERSION 3.9)
project(bottomup)

set(CMAKE_CXX_STANDARD 14)

set(CMAKE_CXX_FLAGS "-Wall -Wextra -pedantic -std=c++14")

add_executable(bottomup main.cpp logic/parser.cpp logic/parser.h logic/term.h logic/constant.h logic/predicate.h logic/fact.h logic/rule.h logic/variable.h logic/rule.cpp grounder.cpp grounder.h logic/substitution_set.h)