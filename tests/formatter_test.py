from ward import test
from esctl.formatter import TableKey
from fixtures import Cases


c = Cases(
    [
        {"input": "foobar", "expected_output": "Foobar"},
        {"input": "foo_bar", "expected_output": "Foo Bar"},
        {"input": "foo.bar", "expected_output": "Foo Bar"},
        {"input": "foo-bar", "expected_output": "Foo-Bar"},
        {"input": "foo.percent", "expected_output": "Foo %"},
    ]
)


@test("Table's columns names interpolation : {input} -> {expected_output}")
def test_name_interpolation(input=c.input(), expected_output=c.expected_output()):
    assert TableKey(input)._create_name_from_id() == expected_output
