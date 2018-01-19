#!/usr/bin/env python3

from syntetic import datasets
from syntetic import rules
import time
import subprocess
import os
import numpy as np
import gzip
import shutil
import queue
import threading
import argparse

def gzip_file(filename):
    with open(filename, 'rb') as f_in:
        with gzip.open(filename + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            os.remove(filename)

class Parameter:
    def __init__(self, name, options):
        self._name = name
        self._options = options

    def get_options(self):
        for r in self._options:
            yield {
                'param': self._name,
                'value': r
            }


class Runner:
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


    def run_experiment(self, experiment_dir, max_dirs, parameters):
        experiment_dir, file_prefix, configuration = Runner._setup(experiment_dir, '', max_dirs, parameters, {})
        if experiment_dir:
            self._run(experiment_dir, file_prefix, configuration)


    def _alter_rules_config(self, config):
        config['type'] = 'datalog'

    def __str__(self):
        return "Runner"

    def _run(self, experiment_dir, file_prefix, configuration):
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
            print("Running {0} for: {1}/{2}".format(self.__str__(), experiment_dir, file_prefix))
            self._run_process(command, experiment_dir, file_prefix)
            gzip_file(dataset_output)
            gzip_file(rules_output)

    def _generate_command(self, dataset, rules):
        return None


    def _run_process(self, command, experiment_dir, file_prefix):
        output = os.path.join(experiment_dir, file_prefix + '-output.txt')
        with open(output, 'w') as out_f:
            run_time = ""
            try:
                start = time.perf_counter()
                subprocess.run(command, stdout=out_f, timeout=600)
                end = time.perf_counter()
                run_time = "{0:.3f}".format(end - start)
            except subprocess.TimeoutExpired:
                run_time = "Timeout expired"

            with open(os.path.join(experiment_dir, file_prefix + '-result.txt'), 'w') as res_f:
                print("Time: {}".format(run_time), file=res_f)

        gzip_file(output)


class GringoRunner(Runner):
    def _generate_command(self, dataset, rules):
        return [
            '../Grounders/clingo/build/bin/clingo', '--pre', '--mode=gringo', '--text',
            dataset, rules
        ]

    def __str__(self):
        return "Gringo"


class Consumer(threading.Thread):
    def __init__(self, grid_search, queue):
        super().__init__()
        self._grid_search = grid_search
        self._queue = queue

    def run(self):
        while not self._grid_search.stopped:
            configuration = self._queue.get()
            if configuration[-1]['param'] == 'runner' and isinstance(configuration[-1]['value'], Runner):
                configuration[-1]['value'].run_experiment(self._grid_search._exp_dir, self._grid_search._max_dirs, configuration)
            else:
                print("No runner for: ", configuration)


class GridSearch:
    def __init__(self, parameters, max_dirs):
        self._parameters = parameters
        self._create_experiment_dir()
        self._max_dirs = max_dirs
        self.stopped = False

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

    def run(self, num_threads):
        self._queue = queue.Queue(maxsize=num_threads)
        consumers = [Consumer(self, self._queue) for i in range(num_threads)]

        for consumer in consumers:
            consumer.start()

        try:
            for configuration in self._generate_configuration(0, []):
                self._queue.put(configuration)
        except KeyboardInterrupt:
            pass

        self.stopped = True
        for consumer in consumers:
            consumer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Runs grid search in defined parameter space")
    parser.add_argument(
        "-t", "--threads", type=int, default=1,
        help="Spawn N threads"
    )

    args = parser.parse_args()

    grid_search = GridSearch([
        Parameter('tables', [10, 50, 100]),
        Parameter('facts', [10, 500, 1000]),
        Parameter('base_rules', [10, 50, 100]),
        Parameter('count', [1, 3, 10, 20]),
        Parameter('rule_proportion', np.linspace(0, 1, 5)),
        Parameter('relations', [10, 50, 100]),
        Parameter('min_columns', [1, 5, 10]),
        Parameter('max_columns', [5, 10, 30]),
        Parameter('width', [1, 20, 50]),
        Parameter('weight', np.linspace(0, 1, 5)),
        Parameter('duplicity', [0, 1, 5]),
        Parameter('unique', [False, True]),
        Parameter('all', [False, True]),
        Parameter('runner', [
            GringoRunner(),
        ]),
    ],
    5)

    grid_search.run(args.threads)
    print("All done")
