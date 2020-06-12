import os

from ward import fixture, each

from esctl.config import Context
import esctl.main

TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
FIXTURES_PATH = "{}/fixtures".format(TESTS_PATH)


class Cases:
    def __init__(self, cases):
        self.cases = cases

    def input(self):
        return each(*[c.get("input") for c in self.cases])

    def expected_output(self):
        return each(*[c.get("expected_output") for c in self.cases])


class Options:
    pass


@fixture
def dummy_esctl():
    app = esctl.main.Esctl()
    app.options = Options()
    app.options.config_file = "{}/valid_esctlrc.yml".format(FIXTURES_PATH)
    app.options.verbose_level = 3
    app.options.context = "localhost"
    app.initialize_app([])

    return app


@fixture
def dummy_context():
    return Context("foo", "bar", "baz", {})


@fixture
def dummy_esctl_with_dummy_context(esctl=dummy_esctl, context=dummy_context):
    esctl.context = context
    return esctl
