#!/usr/bin/env python3

import sys
import re

class Exporter:
    def __init__(self, file=sys.stdout):
        if type(file) == "string":
            self._file = open(file, 'w')
        else:
            self._file = file

    def export(self, values):
        for v in values:
            if v.__class__.__name__ == 'Table':
                self._export_table(v)
            elif v.__class__.__name__ == 'Rule':
                self._export_rule(v)
            else:
                raise TypeError('This class is not supported: {}'.format(v.__class__.__name__))

        self._finalize(values)

    def _export_table(self, table):
        raise NotImplementedError

    def _export_rule(self, rule):
        raise NotImplementedError

    def _finalize(self, values):
        pass


class DatalogExporter(Exporter):
    def _export_table(self, table):
        print("% " + table._id + ":" + str(len(table._data[0])) + ":[", end="", file=self._file)
        rels = []
        for r in table._relations:
            rels.append(r._id)
        print(",".join(rels) + "]", file=self._file)

        for row in table._data:
            print(table._id + "(" + ", ".join(row) + ").", file=self._file)

    def _export_rule(self, rule):
        print("rule_" + rule._id + "(" + ", ".join(rule.head_symbols) + ") :- ", end="", file=self._file)
        tables = [tr['name'] + "(" + ", ".join(tr['variables']) + ")" for tr in rule.table_rules]
        print(", ".join(tables) + ".")

class PrologExporter(DatalogExporter):
    def _export_rule(self, rule):
        super()._export_rule(rule)

        rule_string = "rule_" + rule._id + "(" + ",".join(rule.head_symbols) + ")"

        print(":- findall(" + rule_string + ", " + rule_string + ", G), writeln(G).", file=self._file)

    def _finalize(self, values):
        print(":- halt.", file=self._file)


class Importer:
    """
    Parse the structure of the given dataset from the file header
    """
    def __init__(self, file=sys.stdin, print_to_stdout=False):

        """
        :param data_file: Handler of the file, which should be parsed
        :param print_to_stdout:  Whether to copy the *data_file* to the stdout
            (useful when creating complete dataset with rules)
        """

        if type(file) == "string":
            self._file = open(file, 'r')
        else:
            self._file = file

        self.predicates = {}
        """
        Dictionary with the parsed predicates.
        
        The keys are the predicate names and the attributes are following:
            arity: predicate arity
            
            name: the same as the key
            
            relations: array of the names of the relations in the given order
        """

        self._parse(print_to_stdout)

    def _parse(self, reprint):
        raise NotImplementedError

class DatalogImporter(Importer):
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

    def _parse(self, print_to_stdout):
        for line in self._file:
            if print_to_stdout:
                print(line, end="")
            # Comment with relations
            if line[0] == '%':
                self._parse_atoms(line)

