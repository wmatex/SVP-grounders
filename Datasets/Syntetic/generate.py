#!/usr/bin/env python3

import argparse
import random
import math

random.seed(0)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate syntetic dataset for grounder')

    parser.add_argument('-f', '--facts', type=int, default=10,
                        help='Number of facts')

    parser.add_argument('-t', '--tables', type=int, default=3,
                        help='Number of tables')

    parser.add_argument('-r', '--relations', type=float, default=0.5,
                        help='Relative connectedness (number of connections is <relations> * <tables>^2)')

    parser.add_argument('-c', '--columns', type=int, default=3,
                        help='Average number of table columns')

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
        self._data = [[generate_identifier(id, i*columns + j) for j in range(columns)] for i in range(rows)]
        self._relations = []

    def addRelation(self, table):
        self._relations.append(table)
        for row in self._data:
            row.append(table.getRandomId())

    def getRandomId(self):
        rows = len(self._data)
        return self._data[random.randint(0, rows-1)][0]

class Convertor:
    def convertTo(self, tables):
        pass


class DatalogConvertor(Convertor):
    def convertTo(self, tables):
        for t in tables:
            for row in t._data:
                print(t._id + "(" + ", ".join(row) + ").")

if __name__ == "__main__":
    args = parse_arguments()

    tables = []
    columns = args.columns

    for t in range(args.tables):
        table = Table(t, columns, args.facts)
        tables.append(table)

    num_relations = math.floor(args.relations * args.tables**2)

    for r in range(int(num_relations)):
        t1 = random.choice(tables)
        t2 = random.choice(tables)

        t1.addRelation(t2)

    convertor = DatalogConvertor()
    convertor.convertTo(tables)
