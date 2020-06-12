from ward import test
from fixtures import dummy_esctl_with_dummy_context, Cases


c = Cases(
    [
        {"input": ["https://foo.example.com:8200"], "expected_output": "https"},
        {"input": ["http://foo.example.com:8200"], "expected_output": "http"},
        {
            "input": [
                "https://foo.example.com:8200",
                "http://bar.example.com:8200",
                "http://baz.example.com:8200",
            ],
            "expected_output": "https",
        },
        {"input": ["foo://foo.example.com:8200"], "expected_output": "https"},
        {"input": ["foo.example.com:8200"], "expected_output": "https"},
    ]
)


@test("Scheme discovery and interpolation : {input} -> {expected_output}")
def test_scheme_discovery(
    esctl=dummy_esctl_with_dummy_context,
    input=c.input(),
    expected_output=c.expected_output(),
):

    esctl.context.cluster = {"servers": input}
    assert esctl.find_scheme() == expected_output
