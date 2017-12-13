#!/usr/bin/env python3

"""
Create rules from defined datasets based on provided features.
"""

import random
import argparse
import sys
import re
import numpy as np
import weights
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
        '-a', '--all', action='store_true',
        help='Use all body variables in the head'
    )

    parser.add_argument(
        '-wg', '--weight', type=float, default=0.5,
        help='Weight of the table with <min> columns'
    )

    parser.add_argument(
        '-p', '--print', action='store_true',
        help='Print the data source file to stdout'
    )

    return parser.parse_args()


class Parser:
    """
    Parse the structure of the given dataset from the file header
    """
    def __init__(self, data_file, print_to_stdout):
        """
        :param data_file: Handler of the file, which should be parsed
        :param print_to_stdout:  Whether to copy the *data_file* to the stdout
            (useful when creating complete dataset with rules)
        """
        self.predicates = {}
        """
        Dictionary with the parsed predicates.
        
        The keys are the predicate names and the attributes are following:
            arity: predicate arity
            
            name: the same as the key
            
            relations: array of the names of the relations in the given order
        """
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
    """
    Class with single rule definition
    """
    def __init__(self, id, parser, num_of_tables, first_item_weight=0.5):
        """
        :param id: Numeric id used for identifier generation
        :param parser: Instance of the 'Parser' class
        :param num_of_tables: Number of tables to be used in the rule
        :param first_item_weight: Weight of the first item as required by :py:func:`weights.generate`
        """
        self._id = generate_identifier(id)

        self._create(parser, num_of_tables, first_item_weight)

    def _create(self, parser, num_of_tables, first_item_weight):
        num_of_tables = min(num_of_tables, len(parser.predicates))

        tables = list(parser.predicates)
        tables.sort(key=lambda k: parser.predicates[k]['arity'])
        wgs = weights.generate(tables, first_item_weight)

        non_zero = sum(i > 0 for i in wgs)
        num_of_tables = min(num_of_tables, non_zero)
        tables = np.random.choice(tables, size=num_of_tables, p=wgs, replace=False)
        self._tables = [parser.predicates[t] for t in tables]

    def _create_head(self, tables, duplicity, unique_names=False, all_body=False):
        head_symbols = {}

        for t in tables:
            n = 1
            if all_body:
                n = t['arity'] - len(t['relations'])
            head_symbols[t['name']] = head_symbols.get(t['name'], 0) + n


        heads = []
        for name, count in head_symbols.items():
            if unique_names:
                for i in range(duplicity):
                    if i > 0:
                        heads.extend([name.upper() + str(index) + "_" + str(i) for index in range(count)])
                    else:
                        heads.extend([name.upper() + str(index) for index in range(count)])

            else:
                heads.extend([name.upper() + str(index) for index in range(count)])

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

    def generate(self, duplicity, unique_names, all_body):
        """
        Generate the rule definition and print it to the standard output

        :param int duplicity: How many times to duplicate each body predicate
        :param boolean unique_names: Whether to use unique variable names for each duplicate body predicate
        :param boolean all_body: Whether to include all variables from the body predicates in the head of the rule
        """
        head_symbols = self._create_head(self._tables, duplicity, unique_names, all_body)
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
        r = Rule(i, parser, args.width, args.weight)
        r.generate(args.duplicity + 1, args.unique, args.all)
