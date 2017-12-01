#!/usr/bin/env python3

import random
import argparse
import sys
import re
from utils import generate_identifier

random.seed(0)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate rules for defined dataset')

    parser.add_argument(
        'data', type=argparse.FileType('r'),
        nargs='?', default=sys.stdin,
        help='Data source file'
    )

    parser.add_argument(
        '-n', '--count', type=int, default=1,
        help='Number of generated rules'
    )

    parser.add_argument(
        '-w', '--width', type=int, default=3,
        help='Number of tables in the body'
    )

    parser.add_argument(
        '-d', '--duplicity', type=float, default=0.0,
        help='Probability of having duplicate predicates in the body'
    )

    return parser.parse_args()

class Parser:
    def __init__(self, data_file):
        self._predicates = {}
        self._parse(data_file)

    def _parse_atoms(self, line):
        
        pass

    def _parse(self, data_file):
        last_identifier = None
        id_reg = re.compile('^([a-z]+)\(')
        arity_reg = re.compile(',')

        for line in data_file:
            # Comment with relations
            if line[0] == '%':
                self._parse_atoms(line)
            else:
                match = id_reg.match(line)
                if match:
                    if last_identifier is not match.group(1):
                        last_identifier = match.group(1)
                        m = arity_reg.findall(line)
                        self._predicates[last_identifier]['arity'] = len(m) + 1

        print(self._predicates)


class Rule:
    def __init__(self, id, tables, num_of_tables):
        self._id = generate_identifier(id)
        self._tables = tables

        self._create(num_of_tables)

    def _create(self, num_of_tables):
        num_of_tables = min(num_of_tables, len(self._tables))

        tables = random.sample(self._tables, num_of_tables)

        self._rule = tables

    def generate(self, duplicity):
        head_symbols = set()
        for t in self._rule:
            prefix = t._id.upper()
            for index in range(t._columns):
                head_symbols.add(prefix + str(index))

        print("rule_" + self._rule._id + "(" + ", ".join(head_symbols) + ") :- ", end="")
        table_rules = []
        for t in self._rule:
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

    parser = Parser(args.data)

    # for i in range(args.count):
    #     r = Rule(i, )
