from loguru import logger

from vigil.vigil import Vigil


def test_input_scanner():
    result = app.input_scanner.perform_scan('Hello world!')

def test_output_scanner():
    app.output_scanner.perform_scan('Hello world!', 'Hello world!')

def test_canary_tokens():
    add_result = app.canary_tokens.add('Hello world!')
    app.canary_tokens.check(add_result)


if __name__ == '__main__':
    app = Vigil.from_config('conf/openai.conf')

    test_input_scanner()
    test_output_scanner()
    test_canary_tokens()

