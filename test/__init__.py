from . import tests

def main():
    reload(tests)
    return tests.test_main()

