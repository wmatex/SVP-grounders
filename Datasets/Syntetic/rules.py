#!/usr/bin/env python3

"""
Create rules from defined datasets based on provided features.
"""

import random
import argparse
import sys
import numpy as np
import weights
import convert
from utils import generate_identifier

random.seed(0)
np.random.seed(0)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate rules for defined dataset')

    parser.add_argument(
        'data', type=argparse.FileType('r'),
        nargs='?', default=sys.stdin,
        help='Data source file'
    )

    parser.add_argument(
        '-n', '--count', type=int, default=0,
        help='Number of generated rules'
    )

    parser.add_argument(
        '-w', '--width', type=int, default=3,
        help='Number of predicates in the body'
    )

    parser.add_argument(
        '-d', '--duplicity', type=int, default=0,
        help='Number of duplicate predicates in body'
    )

    parser.add_argument(
        '-u', '--unique', action='store_true',
        help='Use unique variable names in duplicit body predicates'
    )

    parser.add_argument(
        '-a', '--all', action='store_true',
        help='Use all body variables in the head'
    )

    parser.add_argument(
        '-wg', '--weight', type=float, default=0.5,
        help='Weight of the predicate with <min> terms'
    )

    parser.add_argument(
        '-b', '--base-rules', type=int, default=1,
        help='Number of generated base rules with only tables in body'
    )

    parser.add_argument(
        '-r', '--rule-proportion', type=float, default=0,
        help='Proportion of rules in body'
    )

    parser.add_argument(
        '-p', '--print', action='store_true',
        help='Print the data source file to stdout'
    )

    parser.add_argument(
        '--type', default='datalog', choices=['datalog', 'prolog'],
        help='Type of exported file format'
    )

    return parser.parse_args()


class Rule:
    """
    Class with single rule definition
    """
    def __init__(self, id, tables, rules, size_of_body, first_item_weight=0.5, rules_proportion=0.0):
        """
        :param id: Numeric id used for identifier generation
        :param parser: Instance of the 'Parser' class
        :param num_of_tables: Number of tables to be used in the rule
        :param first_item_weight: Weight of the first item as required by :py:func:`weights.generate`
        """
        self._id = generate_identifier(id)
        self.body = []
        self.head = []

        self._create(tables, rules, size_of_body, first_item_weight, rules_proportion)

    def _create(self, tables, rules, size_of_body, first_item_weight, rules_proportion):
        num_of_tables = min(size_of_body, len(tables))

        tables_list = list(tables)

        tables_list.sort(key=lambda k: tables[k]['arity'])
        rules_list = sorted(rules, key=lambda k: len(k.head))

        wgs_tables = weights.generate(tables_list, first_item_weight)
        wgs_rules = weights.generate(rules_list, first_item_weight)

        non_zero_tables = sum(i > 0 for i in wgs_tables)
        num_of_tables = min(num_of_tables, non_zero_tables)
        tables_list = np.random.choice(tables_list, size=num_of_tables, p=wgs_tables, replace=False)

        self._tables = [tables[t] for t in tables_list]

        non_zero_rules = sum(i > 0 for i in wgs_rules)
        num_of_rules = min(non_zero_rules, num_of_tables*rules_proportion)
        if num_of_rules > 0 and len(rules_list) > 0:
            rules_list = np.random.choice(rules_list, size=num_of_rules, p=wgs_rules, replace=False)
        else:
            rules_list = []

        self._rules = rules_list

    def _create_head(self, duplicity, unique_names=False, all_body=False):
        self._head_symbols = {}

        for t in self._tables:
            n = 1
            if all_body:
                n = t['arity'] - len(t['relations'])
            self._head_symbols[t['name']] = self._head_symbols.get(t['name'], 0) + n

        for r in self._rules:
            self._head_symbols.update(r._head_symbols)

        heads = []
        for name, count in self._head_symbols.items():
            if unique_names:
                for i in range(duplicity):
                    if i > 0:
                        heads.extend([name.upper() + str(index) + "_" + str(i) for index in range(count)])
                    else:
                        heads.extend([name.upper() + str(index) for index in range(count)])

            else:
                heads.extend([name.upper() + str(index) for index in range(count)])

        return sorted(heads)

    def _create_body(self, prefix, arity, relations, dup, unique_names):
        variables = []
        suffix = ''
        if dup > 0 and unique_names:
            suffix = "_" + str(dup)

        for index in range(arity):
            if index in relations:
                variables.append(relations[index].upper() + "0" + suffix)
            else:
                variables.append(prefix + str(index) + suffix)

        return variables

    def generate(self, duplicity, unique_names, all_body):
        """
        Generate the rule definition and print it to the standard output

        :param int duplicity: How many times to duplicate each body predicate
        :param boolean unique_names: Whether to use unique variable names for each duplicate body predicate
        :param boolean all_body: Whether to include all variables from the body predicates in the head of the rule
        """
        self.head = self._create_head(duplicity, unique_names, all_body)

        for t in self._tables:
            prefix = t['name'].upper()

            for dup in range(duplicity):
                variables = self._create_body(prefix, t['arity'], t['relations'], dup, unique_names)

                self.body.append({
                    'name': t['name'],
                    'variables': variables
                })

        for r in self._rules:
            self.body.append({
                'name': "rule_" + r._id,
                'variables': r.head
            })


if __name__ == "__main__":
    args = parse_arguments()

    importer = convert.DatalogImporter(args.data, args.print)

    rules = []
    rules_predicates = []

    for i in range(args.base_rules):
        r = Rule(i, importer.predicates, [], args.width, args.weight, 0)
        r.generate(args.duplicity + 1, args.unique, args.all)

        rules.append(r)

    for i in range(args.count):
        r = Rule(i+args.base_rules, importer.predicates, rules, args.width, args.weight, args.rule_proportion)
        r.generate(args.duplicity + 1, args.unique, args.all)

        rules.append(r)

    exporter = None
    if args.type == 'datalog':
        exporter = convert.DatalogExporter()
    elif args.type == 'prolog':
        exporter = convert.PrologExporter()

    exporter.export(rules)

