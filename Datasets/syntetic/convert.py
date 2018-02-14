import sys
import re
from syntetic import datasets

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
        try:
            self._file.flush()
        except ValueError:
            pass


class DatalogExporter(Exporter):
    def _export_table(self, table):
        print("% " + table._id + ":" + str(len(table._data[0])) + ":[", end="", file=self._file)
        rels = []
        for r in table._relations:
            rels.append(table._relations[r]._id + ":" + str(r))
        print(",".join(rels) + "]", file=self._file)

        for row in table._data:
            print(table._id + "(" + ", ".join(row) + ").", file=self._file)

    def _export_rule(self, rule):
        print("rule_" + rule._id + "(" + ", ".join(rule.head) + ") :- ", end="", file=self._file)
        body = [tr['name'] + "(" + ", ".join(tr['variables']) + ")" for tr in rule.body]
        print(", ".join(body) + ".", file=self._file)


class PrologExporter(DatalogExporter):
    def _export_rule(self, rule):
        super()._export_rule(rule)

        rule_string = "rule_" + rule._id + "(" + ",".join(rule.head) + ")"

        print(":- findall(" + rule_string + ", " + rule_string + ", G), writeln(G).", file=self._file)

    def _finalize(self, values):
        print(":- halt.", file=self._file)
        super()._finalize(values)


class SQLExporter(Exporter):
    def _export_table(self, table):
        self._export_table_definition(table)
        self._export_table_data(table)

    def _export_rule(self, rule):
        definition = "CREATE OR REPLACE TEMPORARY VIEW {name} AS {query};"
        select = "SELECT {head} FROM {tables}"

        select_cols = []
        fmt = {}
        for i, variable in enumerate(rule.head):
            self._parse_var(variable, fmt)
            select_cols.append(
                "{0}.{0}_col_{1} as {2}_col_{3}".format(
                    fmt[variable]['name'].lower(),
                    fmt[variable]['index'].lower(),
                    "rule_" + rule._id, i
                )
            )

        froms = set()
        constraints = []
        parsed_vars = {}

        for i, r in enumerate(rule.body):
            if r['name'] not in froms:
                froms.add(r['name'])

            for iv, v in enumerate(r['variables']):
                self._parse_var(v, parsed_vars)
                for j in range(iv+1, len(r['variables'])):
                    # Same variable in the same body => add constraint
                    if v == r['variables'][j]:
                        constraints.append("{table}.{table}_col_{index1} = {table}.{table}_col_{index2}".format(
                            table=r['name'],
                            index1=parsed_vars[v]['index'],
                            index2=j
                        ))

                for j in range(i+1, len(rule.body)):
                    for i2, vv in enumerate(rule.body[j]['variables']):
                        self._parse_var(vv, parsed_vars)

                        if v == vv:
                            if rule.body[j]['name'] not in froms:
                                froms.add(rule.body[j]['name'])

                            if parsed_vars[v]['name'].lower() == r['name']:
                                source_index = parsed_vars[v]['index']
                                target_index = i2
                            else:
                                source_index = iv
                                target_index = parsed_vars[v]['index']

                                if rule.body[j]['name'].startswith('rule_'):
                                    target_index = i2

                            constraints.append(
                                "{source}.{source}_col_{source_index} = {target}.{target}_col_{target_index}".format(
                                    source=r['name'],
                                    target=rule.body[j]['name'],
                                    source_index=source_index,
                                    target_index=target_index
                                )
                            )

        from_string = ', '.join(froms)

        where_query = ""
        if len(constraints) > 0:
            where_query = "WHERE {}".format(" AND ".join(constraints))

        print(definition.format(query=select.format(
            head=', '.join(select_cols),
            tables="{} {}".format(
                from_string,
                where_query
            )
        ), name="rule_" + rule._id), file=self._file)
        print("SELECT * FROM rule_{};".format(rule._id), file=self._file)


    def _parse_var(self, var, parsed):
        variable_reg = re.compile('(?P<name>[A-Z]+)(?P<index>[0-9]+)_?(?P<dup>[0-9]+)?')
        if var not in parsed:
            m = variable_reg.match(var)
            parsed[var] = {
                'name': m.group('name'),
                'index': m.group('index'),
                'dup': m.group('dup')
            }

    def _export_table_definition(self, table):
        definition = """
DROP TABLE IF EXISTS {name};
CREATE TABLE {name} (
  {columns},
  PRIMARY KEY ({primary})
);
        """

        column = "{name} character varying(255) NOT NULL {relation}"
        relation = "REFERENCES {reftable} ({refcolumn})"

        columns = []
        for index in range(len(table._data[0])):
            name = table._id + "_col_" + str(index)
            rel_string = ""
            if index in table._relations:
                rel = table._relations[index]
                rel_string = relation.format(reftable=rel._id, refcolumn=rel._id+"_col_0")

            columns.append(
                column.format(name=name, relation=rel_string)
            )

        print(definition.format(
            name=table._id,
            primary=table._id + "_col_0",
            columns=",\n  ".join(columns),
        ), file=self._file)

    def _export_table_data(self, table):
        insert_query = "INSERT INTO {table} VALUES {values};"

        data = []
        for row in table._data:
            row_data = []
            for column in row:
                row_data.append("'{}'".format(column))

            data.append("({})".format(",".join(row_data)))

        print(
            insert_query.format(table=table._id, values=",".join(data)),
            file=self._file
        )


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
        atom_info_reg = re.compile('(?P<name>[\w]+):\s*(?P<arity>[0-9]+):\s*\[(?P<relations>[\w:0-9,]*)\]')
        rel_info_reg = re.compile('(?P<name>[\w]+):(?P<pos>[0-9]+)')
        match = atom_info_reg.search(line)

        if match:
            predicate = {
                'arity': int(match.group('arity')),
                'name': match.group('name'),
                'relations': {}
            }

            for atom in match.group('relations').split(','):
                if atom:
                    match_rel = rel_info_reg.match(atom)
                    if match_rel:
                        predicate['relations'][int(match_rel.group('pos'))] = match_rel.group('name')

            self.predicates[match.group('name')] = predicate

    def _parse(self, print_to_stdout):
        for line in self._file:
            if print_to_stdout:
                print(line, end="")
            # Comment with relations
            if line[0] == '%':
                self._parse_atoms(line)


class SQLImporter(Importer):
    def _parse(self, print_to_stdout):
        table_def_reg = re.compile('CREATE TABLE (?P<name>[^ ]+)\s* \(')
        insert_reg = re.compile('INSERT INTO (?P<name>[^ ]+) VALUES (?P<data>.*);')

        data = {}

        for line in self._file:
            match = table_def_reg.search(line)
            if match:
                name = match.group('name').lower()
                self.predicates[name] = self._table_def(name)
                data[name] = []
                continue

            match = insert_reg.match(line)
            if match:
                name = match.group('name').lower()
                data[name] += self._parse_data(name, match.group('data'))
                continue

        tables = {}
        for table in data:
            tables[table] = datasets.Table.from_data(table, data[table], {})

        for table in data:
            relations = {}
            for r in self.predicates[table]['relations']:
                relations[r] = tables[self.predicates[table]['relations'][r]]
            tables[table]._relations = relations

        self.tables = [tables[t] for t in tables]


    def _parse_data(self, table, data):
        row_data = []
        rows = data.strip('()').split('),(')
        for row in rows:
            columns = row.split(',')
            row_data.append([c.strip('\'"') for c in columns])

        return row_data

    def _table_def(self, name):
        end_table_def = re.compile('\s*\).*;')
        column_reg = re.compile('\s*(?P<column>[a-z_0-9]+)')
        ref_reg = re.compile('REFERENCES (?P<table>[^ ]+)\s*\((?P<col>[a-z_0-9]+)\)')

        table_def = {
            'name': name,
            'arity': 0,
            'relations': {}
        }
        columns = {}
        col_index = 0

        for line in self._file:
            match = end_table_def.match(line)
            if match:
                return table_def

            match = column_reg.match(line)
            if match:
                columns[match.group('column')] = col_index
                table_def['arity'] += 1

                match = ref_reg.search(line)
                if match:
                    table_def['relations'][col_index] = match.group('table')
                    table_def['arity'] += 1

                col_index += 1


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        importer = SQLImporter(f, False)

        exporter = DatalogExporter()
        exporter.export(importer.tables)
