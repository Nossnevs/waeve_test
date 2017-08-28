import random
import signal
import argparse
import docker
import sys
from datetime import datetime
from time import sleep

from docker.types.services import Resources


class WeaveTest:

    def __init__(self, args):
        self.d = docker.from_env()
        self.services = args.services
        self.nodes = args.node_names
        self.quiet_time = args.quiet_time
        self.network = args.network

    def run(self):
        try:
            for i in range(0, self.services):
                node = random.choice(self.nodes)
                self.__create_test(i, node)
            server_list = self.d.services.list()
            test_services = [s for s in server_list if s.name.startswith('test_')]
            while True:
                sleep(self.quiet_time)
                print('Moving services around')
                self.__move_services(test_services)
        except Exception as e:
            clean_up()
            raise e

    def __move_services(self, services):
        for s in services:
            s.reload()
            node = random.choice(self.nodes)
            print('Banned ' + s.name + ' from ' + node)
            self.__update_test(s, node)

    def __create_test(self, i, node_name):
        test_kwargs = {
            'name': 'test_' + str(i),
            'image': 'nossnevs/weave_test:latest',
            'env': {'SERVICE_NAME': 'test_' + str(i)},
            'resources': Resources(mem_limit=512 * 1000 * 1000, mem_reservation=100 * 1000 * 1000),
            'labels':{
                'traefik.port': '80',
                'traefik.backend.loadbalancer.method': 'drr',
                'traefik.frontend.rule': 'Host:' + 'test_' + str(i) + '.ohmytest.se',
                'traefik.frontend.entryPoints': 'HTTP',

            },
            'networks': [self.network],
            'mode': {'Replicated': {'Replicas': 2}},
            'constraints': ['node.hostname!=' + node_name]
        }
        print('Creating service test_' + str(i))
        self.d.services.create(**test_kwargs)

    def __update_test(self, s, node_name=None, replicas=1):

        test_kwargs = {
            'name': s.name,
            'resources': Resources(mem_limit=512 * 1000 * 1000, mem_reservation=100 * 1000 * 1000),
            'env': {'SERVICE_NAME': s.name, 'date': datetime.now()},
            'networks': [self.network],
            'mode': {'Replicated': {'Replicas': replicas}},
        }

        if node_name:
            test_kwargs['constraints'] = ['node.hostname!=' + node_name]

        s.update(**test_kwargs)


def clean_up():
    d = docker.from_env()
    test_services = [s for s in d.services.list() if s.name.startswith('test_')]
    print('Start cleaning upp ' + str(len(test_services)) + ' services')
    for s in test_services:
        print('Removing ' + s.name)
        s.remove()


def handler(signum, frame):
    sleep(2)
    clean_up()
    sleep(5)
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    parser = argparse.ArgumentParser(
        description='This script trying to reproduce the bug in https://github.com/moby/moby/issues/32195'
    )
    parser.add_argument('services', metavar='services', type=int, help='Number of test services')
    parser.add_argument('quiet_time', metavar='quiet_time', type=int, help='The time between moving services')
    parser.add_argument('network', metavar='network', help='The network to be used.')
    parser.add_argument('node_names', metavar='node_name', nargs='+', help='The nodes to be used in the test')
    parsed_args = parser.parse_args()
    weave_test = WeaveTest(parsed_args)
    weave_test.run()
