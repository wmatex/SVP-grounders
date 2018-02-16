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
    def __init__(self, file=sys.stdout):
        super().__init__(file)
        self._constraints = []

    def _finalize(self, values):
        for constraint in self._constraints:
            print(constraint, file=self._file)

        super()._finalize(values)

    def _export_table(self, table):
        self._export_table_definition(table)
        self._export_table_data(table)

    def _preprocess(self, rule):
        metadata = {
            'tables': {},
            'vars': {}
        }

        for table in rule._tables:
            metadata['tables'][table['name']] = table

        for body in rule.body:
            for index, var in enumerate(body['variables']):
                self._parse_var(var, metadata['vars'])

                if body['name'] not in metadata['vars'][var]['predicates']:
                    metadata['vars'][var]['predicates'][body['name']] = {
                        'name': body['name'],
                        'pos': index
                    }


        return metadata

    def _create_constraint(self, left, leftindex, right, rightindex):
        return "\"{left}\".{left}_col_{leftindex} = \"{right}\".{right}_col_{rightindex}".format(
            left=left,
            leftindex=leftindex,
            right=right,
            rightindex=rightindex
        )

    def _export_rule(self, rule):
        definition = "CREATE OR REPLACE TEMPORARY VIEW {name} AS {query};"
        select = "SELECT DISTINCT {head} FROM {tables}"

        metadata = self._preprocess(rule)

        froms = set()
        constraints = []
        for table in rule._tables:
            for key, rel in table['relations'].items():
                if rel in metadata['tables']:
                    constraints.append(self._create_constraint(
                        table['name'], key,
                        rel, 0
                    ))

            froms.add(table['name'])

        for relation in rule.body:
            if relation['name'] not in froms:
                froms.add(relation['name'])


        for subrule in rule._rules:
            for subrule_var in subrule.head:
                for body_var in metadata['vars']:
                    if subrule_var == body_var:
                        for pred_name, predicate in metadata['vars'][subrule_var]['predicates'].items():
                            if predicate['name'] != 'rule_' + subrule._id:
                                constraints.append(self._create_constraint(
                                    'rule_' + subrule._id, metadata['vars'][subrule_var]['predicates']['rule_'+subrule._id]['pos'],
                                    predicate['name'], predicate['pos']
                                ))

        select_cols = []
        for head_index, head_var in enumerate(rule.head):
            from_table = metadata['vars'][head_var]['name'].lower()
            from_index = metadata['vars'][head_var]['index']

            if metadata['vars'][head_var]['name'].lower() not in froms:
                for pred_name, predicate in metadata['vars'][head_var]['predicates'].items():
                    if pred_name.startswith('rule_'):
                        from_table = pred_name
                        from_index = predicate['pos']
                        break

            select_cols.append(
                "\"{0}\".{0}_col_{1} as {2}_col_{3}".format(
                    from_table, from_index,
                    "rule_" + rule._id, head_index
                )
            )

        from_string = ', '.join(['"{}"'.format(f) for f in froms])

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
                'dup': m.group('dup'),
                'predicates': {}
            }

    def _export_table_definition(self, table):
        definition = """
DROP TABLE IF EXISTS "{name}";
CREATE TABLE "{name}" (
  {columns},
  PRIMARY KEY ({primary})
);
        """

        column = "{name} character varying(255) NOT NULL"
        relation = "ALTER TABLE \"{table}\" ADD CONSTRAINT cons_{table}_{refcolumn} FOREIGN KEY ({column}) REFERENCES \"{reftable}\" ({refcolumn});"

        columns = []
        for index in range(len(table._data[0])):
            name = table._id + "_col_" + str(index)
            if index in table._relations:
                rel = table._relations[index]
                self._constraints.append(relation.format(table=table._id, reftable=rel._id, column=name, refcolumn=rel._id+"_col_0"))

            columns.append(
                column.format(name=name)
            )

        print(definition.format(
            name=table._id,
            primary=table._id + "_col_0",
            columns=",\n  ".join(columns),
        ), file=self._file)

    def _export_table_data(self, table):
        insert_query = "INSERT INTO \"{table}\" VALUES {values};"

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
        self._metadata = {}

        table_def_reg = re.compile('CREATE TABLE "?(?P<name>[a-z0-9]+)"?\s* \(')
        insert_reg = re.compile('INSERT INTO "?(?P<name>[a-z0-9]+)"? VALUES (?P<data>.*);')
        ref_reg = re.compile('ALTER TABLE "?(?P<table>[a-z0-9]+)"? ADD CONSTRAINT [a-z_0-9]* FOREIGN KEY \((?P<column>[a-z_0-9]+)\) REFERENCES "?(?P<reftable>[a-z0-9]+)"? \((?P<refcolumn>[a-z_0-9]+)\)')

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

            match = ref_reg.match(line)
            if match:
                self.predicates[match.group('table')]['relations'][self._metadata[match.group('table')]['columns'][match.group('column')]] = match.group('reftable')
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

        table_def = {
            'name': name,
            'arity': 0,
            'relations': {}
        }
        self._metadata[name] = {
            'columns': {}
        }
        col_index = 0

        for line in self._file:
            match = end_table_def.match(line)
            if match:
                return table_def

            match = column_reg.match(line)
            if match:
                self._metadata[name]['columns'][match.group('column')] = col_index
                table_def['arity'] += 1


                col_index += 1


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        importer = SQLImporter(f, False)

        exporter = DatalogExporter()
        exporter.export(importer.tables)
