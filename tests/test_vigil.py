import pytest
from vigil.vigil import Vigil


@pytest.fixture
def app() -> Vigil:
    return Vigil.from_config("conf/openai.conf")


def test_input_scanner(app: Vigil):
    result = app.input_scanner.perform_scan("Hello world!")
    assert result


def test_output_scanner(app: Vigil):
    assert app.output_scanner.perform_scan("Hello world!", "Hello world!")


def test_canary_tokens(app: Vigil):
    add_result = app.canary_tokens.add("Hello world!")
    assert app.canary_tokens.check(add_result)


if __name__ == "__main__":
    a = app()
    test_input_scanner(a)
    test_output_scanner(a)
    test_canary_tokens(a)
