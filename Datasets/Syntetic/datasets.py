#!/usr/bin/env python3

import argparse
import random
import itertools
from utils import generate_identifier
import convert

random.seed(0)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate syntetic dataset for grounder')

    parser.add_argument(
        '-f', '--facts', type=int, default=10,
        help='Number of facts'
    )

    parser.add_argument(
        '-t', '--tables', type=int, default=3,
        help='Number of tables'
    )

    parser.add_argument(
        '-r', '--relations', type=int, default=2,
        help='Number of connections'
    )

    parser.add_argument(
        '-mx', '--max-columns', type=int, default=3,
        help='Maximum number of table columns'
    )

    parser.add_argument(
        '-mi', '--min-columns', type=int, default=1,
        help='Minimum number of table columns'
    )

    return parser.parse_args()


class Table:
    def __init__(self, id, columns, rows):
        self._id = generate_identifier(id)
        self._columns = columns
        self._data = [[generate_identifier(id, i*columns + j) for j in range(columns)] for i in range(rows)]
        self._relations = []

    def add_relation(self, table):
        self._relations.append(table)
        for row in self._data:
            row.append(table.get_random_id())

    def get_random_id(self):
        rows = len(self._data)
        return self._data[random.randint(0, rows-1)][0]


if __name__ == "__main__":
    args = parse_arguments()

    tables = []
    rules = []
    max_columns = args.max_columns
    min_columns = args.min_columns

    cols = 1
    k = (max_columns - min_columns)/(args.tables - 1)
    for t in range(args.tables):
        table = Table(t, round(k*t + min_columns), args.facts)
        tables.append(table)

    random.seed(0)
    num_relations = min(args.relations, args.tables**2)
    pairs = itertools.product(tables, tables)
    pairs = random.sample(list(pairs), num_relations)

    for t1, t2 in pairs:
        t1.add_relation(t2)

    exporter = convert.DatalogExporter()
    exporter.export(tables)