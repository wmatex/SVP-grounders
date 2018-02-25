#!/usr/bin/env python3

import sqlite3
import os
import re


def list_dirs_recurse(path, dirs):
    for item in os.listdir(path):
        new_dir = os.path.join(path, item)
        if os.path.isdir(new_dir):
            yield from list_dirs_recurse(new_dir, dirs + [item])
        else:
            yield dirs + [item]

def transform(name):
    if name == "all" or name == "unique":
        return "param_" + name
    elif name == "runner":
        return "grounder"

    return name

def parse_dirs(items, params):
    for i in range(0, len(items), 2):
        params[transform(items[i])] = items[i+1]

def parse_file(filename, params):
    match_reg = re.compile('result\.txt(\.gz)?$')
    if match_reg.search(filename):
        param_reg = re.compile('[a-zA-Z0-9_.=]+')
        matches = param_reg.findall(filename)
        for match in matches[:-1]:
            key_val = match.split('=')
            params[transform(key_val[0])] = key_val[1]

def read_file(dir, items):
    path = os.path.join(dir, *items)
    with open(path, 'r') as f:
        for line in f:
            vals = line.split(':')
            if len(vals) > 0:
                return vals[1].strip()
            else:
                return vals[0].strip()


def insert(dir, items):
    params = {}
    if len(items) > 1:
        parse_dirs(items[:-1], params)
        parse_file(items[-1], params)
        value = read_file(dir, items)

        sql = "INSERT INTO {table} ({keys}) VALUES ({values});"

        values = []
        keys = []
        for key, val in params.items():
            keys.append(transform(key))
            values.append(":{}".format(transform(key)))

        keys.append('time')
        values.append(':time')

        params['time'] = value
        return sql.format(
            table='results',
            keys=", ".join(keys),
            values=", ".join(values)
        ), params

    return None, None


if __name__ == "__main__":
    dirname = 'experiments/grid-search'
    connection = sqlite3.connect(os.path.join(dirname, 'results.db'))
    cursor = connection.cursor()

    for file in list_dirs_recurse(dirname, []):
        query, params = insert(dirname, file)
        if query:
            try:
                cursor.execute(query, params)
            except sqlite3.IntegrityError:
                pass

    connection.commit()
