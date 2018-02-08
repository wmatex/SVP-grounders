import argparse
import random
import sys
import itertools
from syntetic.utils import generate_identifier
from syntetic import convert

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

    parser.add_argument(
        '-fmt', '--format', default='datalog', choices=['datalog', 'sql'],
        help="Output file format"
    )

    parser.add_argument(
        '--output', type=argparse.FileType('w'), default=sys.stdout,
        help="Output file"
    )

    return parser.parse_args()


class Table:
    def __init__(self, id, columns, rows, generate=True):
        self._id = generate_identifier(id)
        self._columns = columns
        if generate:
            self._data = [[generate_identifier(id, i*columns + j) for j in range(columns)] for i in range(rows)]
        else:
            self._data = None

        self._relations = {}

    @staticmethod
    def from_data(name, data, relations):
        t = Table(0, len(data[0]), len(data), False)
        t._id = name
        t._data = data
        t._relations = relations
        return t

    def add_relation(self, table):
        self._relations[len(self._data[0])] = table
        for row in self._data:
            row.append(table.get_random_id())

    def get_random_id(self):
        rows = len(self._data)
        return self._data[random.randint(0, rows-1)][0]

def run(parameters):
    tables = []
    max_columns = parameters['max_columns']
    min_columns = parameters['min_columns']

    k = (max_columns - min_columns)/(parameters['tables'] - 1)
    for t in range(parameters['tables']):
        table = Table(t, round(k*t + min_columns), parameters['facts'])
        tables.append(table)

    random.seed(0)
    num_relations = min(parameters['relations'], parameters['tables']**2)
    pairs = itertools.product(tables, tables)
    pairs = random.sample(list(pairs), num_relations)

    for t1, t2 in pairs:
        t1.add_relation(t2)

    if parameters['format'] == 'sql':
        exporter = convert.SQLExporter(file=parameters['output'])
    else:
        exporter = convert.DatalogExporter(file=parameters['output'])

    exporter.export(tables)


if __name__ == "__main__":
    args = parse_arguments()
    run(vars(args))

