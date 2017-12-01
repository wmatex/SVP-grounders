#!/usr/bin/env python3

import argparse
import random
import math
import itertools

random.seed(0)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate syntetic dataset for grounder')

    parser.add_argument('-f', '--facts', type=int, default=10,
                        help='Number of facts')

    parser.add_argument('-t', '--tables', type=int, default=3,
                        help='Number of tables')

    parser.add_argument('-r', '--relations', type=int, default=2,
                        help='Number of connections')

    parser.add_argument('-c', '--columns', type=int, default=3,
                        help='Average number of table columns')

    parser.add_argument('-u', '--rules', type=int, default=5,
                        help='Number of table rules')

    return parser.parse_args()

def generate_identifier(x, y = None):
    a = 97
    z = 123
    chars = [str(chr(i)) for i in range(a, z)]

    xx = 1
    idt = ""
    while xx > 0:
        idt = chars[x % (z - a)] + idt
        xx = int(x / (z - a))
        x = xx

    if y is not None:
        return idt + str(y)
    else:
        return idt


class Table:
    def __init__(self, id, columns, rows):
        self._id = generate_identifier(id)
        self._columns = columns
        self._data = [[generate_identifier(id, i*columns + j) for j in range(columns)] for i in range(rows)]
        self._relations = []

    def addRelation(self, table):
        self._relations.append(table)
        for row in self._data:
            row.append(table.getRandomId())

    def getRandomId(self):
        rows = len(self._data)
        return self._data[random.randint(0, rows-1)][0]

class Rule:
    def __init__(self, id, tables, rules, num_of_tables, num_of_rules):
        self._id = generate_identifier(id)
        self._tables = tables
        self._rules = rules

        self._generate(num_of_tables, num_of_rules)


    def _generate(self, num_of_tables, num_of_rules):
        num_of_tables = min(num_of_tables, len(self._tables))
        num_of_rules = min(num_of_rules, len(self._rules))

        tables = random.sample(self._tables, num_of_tables)
        rules = random.sample(self._rules, num_of_rules)

        self._rule = tables


class Convertor:
    def convertTo(self, tables):
        pass

    def convertRulesTo(self, rules):
        pass


class DatalogConvertor(Convertor):
    def convertTo(self, tables):
        for t in tables:
            for row in t._data:
                print(t._id + "(" + ", ".join(row) + ").")

    def convertRulesTo(self, rules):
        for r in rules:
            head_symbols = set()
            for t in r._rule:
                prefix = t._id.upper()
                for index in range(t._columns):
                    head_symbols.add(prefix + str(index))

            print("rule_" + r._id + "(" + ", ".join(head_symbols) + ") :- ", end="")
            table_rules = []
            for t in r._rule:
                prefix = t._id.upper()
                variables = []
                for index in range(t._columns):
                    variables.append(prefix + str(index))

                for relation in t._relations:
                    variables.append(relation._id.upper() + "0")

                table_rules.append(t._id + "(" + ", ".join(variables) + ")")

            print(", ".join(table_rules) + ".")


if __name__ == "__main__":
    args = parse_arguments()

    tables = []
    rules = []
    columns = args.columns

    for t in range(args.tables):
        table = Table(t, columns, args.facts)
        tables.append(table)

    num_relations = min(args.relations, args.tables**2)
    pairs = itertools.product(tables, tables)
    pairs = random.sample(list(pairs), num_relations)

    for t1, t2 in pairs:
        t1.addRelation(t2)

    for u in range(args.rules):
        rules.append(Rule(u, tables, [], random.randint(1, args.tables), 0))

    convertor = DatalogConvertor()
    convertor.convertTo(tables)
    convertor.convertRulesTo(rules)
