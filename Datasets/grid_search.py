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


class Parameter:
    def __init__(self, name, type, options):
        self._name = name
        self.type = type
        self._options = options

    def get_options(self):
        for r in self._options:
            yield {
                'param': self._name,
                'value': r
            }

    def cardinality(self):
        return len(self._options)


class ResultStore:
    DATABASE="results.db"
    TABLE_NAME="results"
    RESULT_COLUMN="time"

    def __init__(self, directory, parameters):
        self._connection = sqlite3.connect(os.path.join(directory, self.DATABASE))
        self._cursor = self._connection.cursor()

        self._create_store(parameters)

    def _create_store(self, parameters):
        sql = """
        CREATE TABLE IF NOT EXISTS {table} (
        {columns},
        PRIMARY KEY (col_list)
        ) WITHOUT ROWID;
        """

        columns = []
        col_list = []
        for param in parameters:
            columns.append("{} {}".format(param._name, param.type))
            col_list.append(param._name)

        columns.append("time text")

        self._cursor.execute(sql.format(
            table=self.TABLE_NAME,
            columns=", ".join(columns),
            col_list=",".join(col_list)
        ))
        self._connection.commit()

    def find(self, configuration):
        sql = "SELECT * FROM {table} WHERE {constraints};"

        constraints = []
        for key, value in configuration.enumerate:
            constraints.append("{key} = :{key}".format(key=key))

        self._cursor.execute(sql.format(table=self.TABLE_NAME, constraints=" AND ".join(constraints)), configuration)
        return self._cursor.fetchone()

    def insert(self, configuration, value):
        sql = "INSERT INTO {table} ({keys}) VALUES ({values});"

        values = []
        keys = []
        for key, val in configuration.enumerate():
            keys.append(key)
            values.append(":{}".format(val))

        keys.append(self.RESULT_COLUMN)
        values.append(value)

        configuration[self.RESULT_COLUMN] = value
        self._cursor.execute(sql.format(
            table=self.TABLE_NAME,
            keys=", ".join(keys),
            values=", ".join(values)
        ), configuration)
        self._connection.commit()

    def __del__(self):
        self._connection.close()


class Runner:
    TIME_OUT=600

    @staticmethod
    def _setup(experiment_dir, file_prefix, make_dir, parameters, configuration):
        if len(parameters) < 1:
            if os.path.isfile(os.path.join(experiment_dir, file_prefix + '-result.txt')) or \
               os.path.isfile(os.path.join(experiment_dir, file_prefix + '-result.txt.gz')):
                return None, None, None
            else:
                return experiment_dir, file_prefix, configuration

        else:
            if make_dir > 0:
                experiment_dir = os.path.join(experiment_dir, parameters[0]['param'], str(parameters[0]['value']))
                if not os.path.isdir(experiment_dir):
                    os.makedirs(experiment_dir, exist_ok=True)
            else:
                file_prefix += "[{0}={1}]".format(parameters[0]['param'], parameters[0]['value'])

            configuration.update({parameters[0]['param']: parameters[0]['value']})
            return Runner._setup(experiment_dir, file_prefix, make_dir - 1, parameters[1:], configuration)


    def run_experiment(self, experiment_dir, max_dirs, parameters, prefix):
        experiment_dir, file_prefix, configuration = Runner._setup(experiment_dir, '', max_dirs, parameters, {})
        if experiment_dir:
            self._run(experiment_dir, file_prefix, configuration, prefix)


    def _alter_rules_config(self, config):
        config['type'] = 'datalog'

    def __str__(self):
        return "Runner"

    def _run(self, experiment_dir, file_prefix, configuration, prefix):
        dataset_config = configuration.copy()
        dataset_output = os.path.join(experiment_dir, file_prefix + '-dataset.txt')
        if not os.path.isfile(dataset_output):
            dataset_config['output'] = open(dataset_output, 'w')
            datasets.run(dataset_config)

        rules_config = configuration.copy()
        rules_output = os.path.join(experiment_dir, file_prefix + '-rules.txt')
        if not os.path.isfile(rules_output):
            rules_config['output'] = open(rules_output, 'w')
            rules_config['data'] = open(dataset_output, 'r')

            # FIXME: Use generic format
            rules_config['data_format'] = 'datalog'
            rules_config['print'] = False

            self._alter_rules_config(rules_config)
            rules.run(rules_config)

        command = self._generate_command(dataset_output, rules_output)
        if command:
            print("{0} {1}/{2}".format(prefix, experiment_dir, file_prefix))
            self._run_process(command, experiment_dir, file_prefix)

            os.remove(dataset_output)
            os.remove(rules_output)

    def _generate_command(self, dataset, rules):
        return None


    def _run_process(self, command, experiment_dir, file_prefix):
        run_time = ""
        try:
            start = time.perf_counter()
            subprocess.run(command, stdout=subprocess.DEVNULL, timeout=self.TIME_OUT, stderr=subprocess.DEVNULL)
            end = time.perf_counter()
            run_time = "{0:.5f}".format(end - start)
        except subprocess.TimeoutExpired:
            print("Timeout expired", file=sys.stderr)
            run_time = "Timeout expired"

        with open(os.path.join(experiment_dir, file_prefix + '-result.txt'), 'a') as res_f:
            print("Time: {}".format(run_time), file=res_f)


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


class Consumer(threading.Thread):
    def __init__(self, grid_search, queue):
        super().__init__()
        self._grid_search = grid_search
        self._queue = queue

    def run(self):
        while not self._grid_search.stopped:
            exp_num, configuration = self._queue.get()
            if configuration[-1]['param'] == 'runner' and isinstance(configuration[-1]['value'], Runner):
                prefix = "[{0:6d}/{1:6d}]".format(exp_num, self._grid_search._num_of_experiments)
                configuration[-1]['value'].run_experiment(self._grid_search._exp_dir, self._grid_search._max_dirs, configuration, prefix)
            else:
                print("No runner for: ", configuration)


class GridSearch:
    def __init__(self, parameters, max_dirs):
        self._parameters = parameters
        self._create_experiment_dir()
        self._max_dirs = max_dirs
        self.stopped = False

        self._num_of_experiments = 1
        for param in parameters:
            self._num_of_experiments *= param.cardinality()

    def _create_experiment_dir(self):
        self._exp_dir = os.path.join("experiments", "grid-search")
        try:
            os.mkdir(self._exp_dir)
        except FileExistsError:
            pass

    def _generate_configuration(self, index, configuration):
        if self.stopped:
            return

        if index >= len(self._parameters):
            yield configuration
        else:
            for param in self._parameters[index].get_options():
                yield from self._generate_configuration(index+1, configuration + [param])

    def run(self, num_threads, max_time):
        self._queue = queue.Queue(maxsize=num_threads)
        consumers = [Consumer(self, self._queue) for i in range(num_threads)]

        for consumer in consumers:
            consumer.start()

        start = time.time()
        print("Started on {}".format(time.strftime("%X")), file=sys.stderr)
        exp_num = 0
        try:
            for configuration in self._generate_configuration(0, []):
                elapsed = time.time() - start
                if elapsed + 2*Runner.TIME_OUT >= max_time:
                    print("Time expired, clearing queue", file=sys.stderr)
                    print("Ended on {}".format(time.strftime("%X")), file=sys.stderr)
                    while not self._queue.empty():
                        try:
                            self._queue.get(False)
                        except queue.Empty:
                            continue
                        self._queue.task_done()

                    break
                else:
                    exp_num += 1
                    self._queue.put((exp_num, configuration))

        except KeyboardInterrupt:
            pass

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
        Parameter('runner', [
            GringoRunner(),
            PrologRunner(),
            DlvRunner(),
            LParseRunner()
        ]),
    ],
    5)

    grid_search.run(args.threads, args.time)
    print("All done", file=sys.stderr)
