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
        '-d', '--duplicity', type=int, default=0,
        help='Number of duplicate predicates in body'
    )

    parser.add_argument(
        '-u', '--unique', action='store_true',
        help='Use unique variable names in duplicit tables'
    )

    parser.add_argument(
        '-p', '--print', action='store_true',
        help='Print the data source file to stdout'
    )

    return parser.parse_args()

class Parser:
    def __init__(self, data_file, print_to_stdout):
        self.predicates = {}
        self._parse(data_file, print_to_stdout)

    def _parse_atoms(self, line):
        atom_info_reg = re.compile('(?P<name>[\w]+):\s*(?P<arity>[0-9]+):\s*\[(?P<relations>[\w,]*)\]')
        match = atom_info_reg.search(line)

        if match:
            predicate = {
                'arity': int(match.group('arity')),
                'name': match.group('name'),
                'relations': []
            }

            for atom in match.group('relations').split(','):
                if atom:
                    predicate['relations'].append(atom)

            self.predicates[match.group('name')] = predicate

    def _parse(self, data_file, print_to_stdout):
        for line in data_file:
            if print_to_stdout:
                print(line, end="")
            # Comment with relations
            if line[0] == '%':
                self._parse_atoms(line)



class Rule:
    def __init__(self, id, parser, num_of_tables):
        self._id = generate_identifier(id)

        self._create(parser, num_of_tables)

    def _create(self, parser, num_of_tables):
        num_of_tables = min(num_of_tables, len(parser.predicates))

        tables = random.sample(list(parser.predicates), num_of_tables)
        self._tables = [parser.predicates[t] for t in tables]

    def _create_head(self, tables, duplicity, unique_names=False):
        head_symbols = {}

        for t in tables:
            head_symbols[t['name']] = head_symbols.get(t['name'], 0) + 1

        heads = []
        for name, count in head_symbols.items():
            if unique_names:
                for i in range(duplicity):
                    if i > 0:
                        heads.extend([name.upper() + str(index) + "_" + str(i) for index in range(count)])
                    else:
                        heads.extend([name.upper() + str(index) for index in range(count)])

            else:
                heads.append(name.upper() + "0")

        return heads

    def _create_body(self, prefix, arity, relations, dup, unique_names):
        variables = []
        suffix = ''
        if dup > 0 and unique_names:
            suffix = "_" + str(dup)

        for index in range(arity - len(relations)):
            variables.append(prefix + str(index) + suffix)

        for r in relations:
            variables.append(r.upper() + "0" + suffix)

        return variables


    def generate(self, width, duplicity, unique_names):
        head_symbols = self._create_head(self._tables, duplicity, unique_names)
        print("rule_" + self._id + "(" + ", ".join(head_symbols) + ") :- ", end="")

        table_rules = []
        for t in self._tables:
            prefix = t['name'].upper()

            for dup in range(duplicity):
                variables = self._create_body(prefix, t['arity'], t['relations'], dup, unique_names)

                table_rules.append(t['name'] + "(" + ", ".join(variables) + ")")

        print(", ".join(table_rules) + ".")

if __name__ == "__main__":
    args = parse_arguments()

    parser = Parser(args.data, args.print)

    for i in range(args.count):
        r = Rule(i, parser, args.width)
        r.generate(args.width, args.duplicity, args.unique)
