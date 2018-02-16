#!/usr/bin/env python3

from syntetic import datasets
from syntetic import rules
import time
import subprocess
import os
import sys
import numpy as np
import queue
import threading
import argparse
import sqlite3
import tempfile
import random
import datetime
import multiprocessing


class Parameter:
    def __init__(self, name, options):
        self.name = name
        self.options = options

    def cardinality(self):
        return len(self.options)


class ResultStore:
    DATABASE="results.db"
    TABLE_NAME="results"
    RESULT_COLUMN="time"

    def __init__(self, directory, parameters):
        self._connection = sqlite3.connect(os.path.join(directory, self.DATABASE), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
        self._lock = threading.Lock()

        self._create_store(parameters)

    @staticmethod
    def _resolve_type(value):
        if isinstance(value, float):
            return 'real'
        elif isinstance(value, int):
            return 'integer'
        else:
            return 'text'

    @staticmethod
    def _transform(param):
        if param == "unique" or param == "all":
            return "param_" + param

        return param

    @staticmethod
    def _transform_config(configuration):
        c = {}
        for key in configuration:
            c[ResultStore._transform(key)] = configuration[key]

        return c

    def _create_store(self, parameters):
        sql = """
        CREATE TABLE IF NOT EXISTS {table} (
        {columns},
        PRIMARY KEY ({col_list})
        ) WITHOUT ROWID;
        """

        columns = []
        col_list = []
        for param in parameters:
            columns.append("{} {} NOT NULL".format(ResultStore._transform(param.name), ResultStore._resolve_type(param.options[0])))
            col_list.append(ResultStore._transform(param.name))

        columns.append("time real")

        sql_query = sql.format(
            table=self.TABLE_NAME,
            columns=", ".join(columns),
            col_list=",".join(col_list)
        )
        self._cursor.execute(sql_query)
        self._connection.commit()

    def find_uncompleted(self, parameters, max_count):
        sql = "SELECT {params}, count(*) as count_grounders FROM {table} GROUP BY {params} HAVING count_grounders > 1 AND count_grounders < {max_count};"
        params = [ResultStore._transform(p) for p in parameters]

        with self._lock:
            self._cursor.execute(sql.format(table=self.TABLE_NAME, params=', '.join(params), max_count=max_count))
            return self._cursor.fetchall()

    def find(self, configuration):
        sql = "SELECT * FROM {table} WHERE {constraints};"

        constraints = []

        config = ResultStore._transform_config(configuration)
        for key, value in config.items():
            constraints.append("{key} = :{key}".format(key=key))


        with self._lock:
            self._cursor.execute(sql.format(table=self.TABLE_NAME, constraints=" AND ".join(constraints)), config)
            return self._cursor.fetchall()

    def insert(self, configuration, value):
        sql = "INSERT INTO {table} ({keys}) VALUES ({values});"

        values = []
        keys = []
        config = ResultStore._transform_config(configuration)
        config[self.RESULT_COLUMN] = value
        for key, val in config.items():
            keys.append(key)
            values.append(":{}".format(key))

        config[self.RESULT_COLUMN] = value
        with self._lock:
            try:
                sql_query = sql.format(
                    table=self.TABLE_NAME,
                    keys=", ".join(keys),
                    values=", ".join(values)
                )
                self._cursor.execute(sql_query, config)
                self._connection.commit()
            except sqlite3.IntegrityError:
                print("Unique constraint failed: {}".format(config))
                pass

    def __del__(self):
        self._connection.close()


class Runner:
    TIME_OUT=600

    def run_experiment(self, configuration, name):
        dataset_config = configuration.copy()
        dataset_config['output'] = tempfile.NamedTemporaryFile(mode='w+')
        dataset_config['format'] = 'datalog'

        self._alter_dataset_config(dataset_config)
        datasets.run(dataset_config)

        rules_config = configuration.copy()
        rules_config['output'] = tempfile.NamedTemporaryFile(mode='w')
        rules_config['data'] = dataset_config['output']
        rules_config['data'].seek(0)

        rules_config['data_format'] = 'datalog'
        rules_config['type'] = 'datalog'
        rules_config['print'] = False

        self._alter_rules_config(rules_config)
        rules.run(rules_config)

        self.setup()

        command = self._generate_command(dataset_config['output'].name, rules_config['output'].name)
        print(self.print_info(configuration, name))
        result = self._run_process(command)
        self.destroy()

        return result

    def print_info(self, configuration, name):
        info_line = []
        for key in sorted(configuration):
            info_line.append("[{0}={1}]".format(str(key), str(configuration[key])))

        return "[{2}] {0:10s}: {1}".format(str(self), ''.join(info_line), name)

    def _alter_rules_config(self, config):
        pass

    def _alter_dataset_config(self, config):
        pass

    def __str__(self):
        return "Runner"

    def _generate_command(self, dataset, rules):
        return None

    def setup(self):
        pass

    def destroy(self):
        pass

    def _run_process(self, command):
        try:
            start = time.perf_counter()
            subprocess.run(command, stdout=subprocess.DEVNULL, timeout=self.TIME_OUT, stderr=subprocess.DEVNULL)
            end = time.perf_counter()
            run_time = "{0:.5f}".format(end - start)
            print(run_time, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("Timeout expired", file=sys.stderr)
            run_time = None

        return run_time


class GringoRunner(Runner):
    def _generate_command(self, dataset, rules):
        return [
            '../Grounders/clingo/build/bin/clingo', '--pre', '--mode=gringo', '--text',
            dataset, rules
        ]

    def __str__(self):
        return "Gringo"


class PrologRunner(Runner):
    def _generate_command(self, dataset, rules):
        return [
            '../Grounders/swi-prolog/build/bin/swipl', '--nosignals', '-O', '--quiet', '--nodebug', '-f', dataset, '-s', rules
        ]

    def _alter_rules_config(self, config):
        config['type'] = 'prolog'

    def __str__(self):
        return 'Prolog'


class DlvRunner(Runner):
    def _generate_command(self, dataset, rules):
        return [
            '../Grounders/dlv/dlv', '-nofacts', '-silent', '-instantiate', dataset, rules
        ]

    def __str__(self):
        return 'Dlv'


class LParseRunner(Runner):
    def _generate_command(self, dataset, rules):
        return [
            '../Grounders/lparse/build/lparse', '-t', '-W', 'none', dataset, rules
        ]

    def __str__(self):
        return 'LParse'

class PostgreSQLRunner(Runner):
    PORT='55556'
    BUILD_DIR='../Grounders/postgresql/build/bin'
    DB_NAME='experiment'

    def __init__(self):
        self._data_dir = tempfile.TemporaryDirectory()
        subprocess.run([os.path.join(self.BUILD_DIR, 'initdb'), '-D', self._data_dir.name])
        self._server = multiprocessing.Process(target=self._start_server)
        self._server.start()

    def _start_server(self):
        subprocess.run([os.path.join(self.BUILD_DIR, 'postgres'), '-p', self.PORT, '-D', self._data_dir.name, '-c', 'logging_collector=on', '-c', 'log_directory=/tmp/pg_log'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _alter_rules_config(self, config):
        config['data_format'] = 'sql'
        config['type'] = 'sql'

    def _alter_dataset_config(self, config):
        config['format'] = 'sql'

    def setup(self):
        subprocess.run([os.path.join(self.BUILD_DIR, 'createdb'), '-p', self.PORT, self.DB_NAME])

    def destroy(self):
        subprocess.run([os.path.join(self.BUILD_DIR, 'dropdb'), '-p', self.PORT, self.DB_NAME])

    def _generate_command(self, dataset, rules):
        return [
            os.path.join(self.BUILD_DIR, 'psql'), '-p', self.PORT, '-f', dataset, '-f', rules, self.DB_NAME
        ]

    def __str__(self):
        return 'PostgreSQL'

    def __del__(self):
        self._server.terminate()
        self._server.join()



class Consumer(threading.Thread):
    def __init__(self, grid_search, queue, name):
        super().__init__()
        self._grid_search = grid_search
        self._queue = queue
        self._name = name

    def run(self):
        while not self._grid_search.stopped:
            configuration, runners = self._queue.get()
            if configuration is None:
                break

            for runner in self._grid_search._runners:
                if self._grid_search.stopped:
                    break

                if str(runner) not in runners:
                    result = runner.run_experiment(configuration, self._name)
                    self._grid_search.store_result(configuration, runner, result)

            self._queue.task_done()


class GridSearch:
    GROUNDER_PARAM="grounder"

    def __init__(self, parameters, runners):
        self._parameters = parameters
        self._runners = runners
        self._create_experiment_dir()

        params_runners = parameters + [Parameter(self.GROUNDER_PARAM, [str(runners[0])])]
        self._result_store = ResultStore(self._exp_dir, params_runners)

        self.stopped = False
        self._uncompleted_configs = []

        self._num_of_experiments = 1
        for param in parameters:
            self._num_of_experiments *= param.cardinality()


    def _create_experiment_dir(self):
        self._exp_dir = os.path.join("experiments", "grid-search")
        try:
            os.mkdir(self._exp_dir)
        except FileExistsError:
            pass

    def store_result(self, configuration, runner, value):
        configuration[self.GROUNDER_PARAM] = str(runner)

        self._result_store.insert(configuration, value)

    def _get_random_configuration(self):
        if len(self._uncompleted_configs) > 0:
            return self._uncompleted_configs.pop()
        else:
            random.seed()
            rand = random.randrange(0, self._num_of_experiments)
            configuration = {}

            for param in reversed(self._parameters):
                configuration[param.name] = param.options[rand % param.cardinality()]
                rand = rand // param.cardinality()

            return configuration

    def run(self, num_threads, max_time):
        self._queue = queue.Queue(maxsize=num_threads)
        consumers = [Consumer(self, self._queue, i) for i in range(num_threads)]

        for consumer in consumers:
            consumer.start()

        start = time.time()
        print("Started on {}".format(time.strftime("%X")), file=sys.stderr)
        print("Running for {}s, ETA: {}".format(max_time, (datetime.datetime.fromtimestamp(start + max_time).strftime("%X"))))

        uncompleted = self._result_store.find_uncompleted([p.name for p in self._parameters], len(self._runners))
        for uncom in uncompleted:
            config = {}
            for k in uncom.keys():
                ck = k
                if k == 'count_grounders':
                    continue
                elif k.startswith('param_'):
                    ck = k[6:]

                config[ck] = uncom[k]
            self._uncompleted_configs.append(config)


        print("Have #{} uncompleted jobs".format(len(uncompleted)))
        configuration = None
        try:
            while not self.stopped:
                elapsed = time.time() - start
                if elapsed + Runner.TIME_OUT >= max_time:
                    print("Time expired, clearing queue", file=sys.stderr)
                    print("Ended on {}".format(time.strftime("%X")), file=sys.stderr)
                    self.stopped = True
                    while not self._queue.empty():
                        try:
                            self._queue.get(False)
                        except queue.Empty:
                            continue
                        self._queue.task_done()

                    for i in range(num_threads):
                        self._queue.put((None, None))

                    break

                if configuration is None:
                    configuration = self._get_random_configuration()

                stored = self._result_store.find(configuration)
                if len(stored) < len(self._runners):
                    runners = [r[self.GROUNDER_PARAM] for r in stored]
                    try:
                        self._queue.put((configuration, runners), timeout=Runner.TIME_OUT)
                        configuration = None
                    except queue.Full:
                        pass
                else:
                    configuration = None

        except KeyboardInterrupt:
            self.stopped = True

        self.stopped = True
        for consumer in consumers:
            consumer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Runs grid search in defined parameter space")
    parser.add_argument(
        "-p", "--threads", type=int, default=1,
        help="Spawn N threads"
    )
    parser.add_argument(
        "-t", "--time", type=int, default=3600,
        help="Number of seconds to run the algorithm"
    )

    args = parser.parse_args()

    grid_search = GridSearch([
        Parameter('tables', [10, 50, 100]),
        Parameter('facts', [10, 500, 1000]),
        Parameter('base_rules', [10, 50, 100]),
        Parameter('count', [1, 3, 10, 20]),
        Parameter('rule_proportion', np.linspace(0, 1, 4)),
        Parameter('relations', [10, 50, 100]),
        Parameter('min_columns', [1, 5, 10]),
        Parameter('max_columns', [5, 10, 30]),
        Parameter('width', [1, 20, 50]),
        Parameter('weight', np.linspace(0, 1, 4)),
        Parameter('duplicity', [0, 1]),
        Parameter('unique', [False, True]),
        Parameter('all', [False, True]),
    ],
        [
            GringoRunner(),
            PostgreSQLRunner(),
            PrologRunner(),
            DlvRunner(),
            LParseRunner()
        ]
    )

    grid_search.run(args.threads, args.time)
    print("All done", file=sys.stderr)
