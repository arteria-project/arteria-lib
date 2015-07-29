import time

class TestFunctionDelta:
    """
    Checks the results of the same function call made consecutively
    
    Replaces:
        x1 = f()
        do_something()
        x2 = f()
        assert_equal(x2 - x1, expected_delta)

    with:
        function_delta = TestFunctionDelta(lambda: f(), self)
        do_something()
        function_delta.assert_changed_by(expected_delta)

    which can be somewhat more readable
    """
    def __init__(self, func, asserts, sleep=0):
        """
        Initializes the class with one initial call to func

        :param func: The function being called consecutively
        :param asserts: An object that provides an assertEqual method
        :param sleep: Time to sleep in seconds before asserting
        :return: None
        """
        self._current = None
        self._func = func
        self._asserts = asserts
        self._last = self._func()
        self._start = self._last
        self._sleep = sleep

    def _assert_changed_by(self, expected, compare_to):
        def evaluate():
            self._current = self._func()
            return self._current - compare_to

        actual = evaluate()
        if expected != actual and self._sleep > 0:
            # Evaluate again if sleep is provided. Provided for cases where there may be some latency
            time.sleep(self._sleep)
            actual = evaluate()
        self._asserts.assertEqual(expected, actual)
        self._last = self._current

    def assert_changed_by_total(self, expected):
        """
        Asserts that the result of calling the wrapped function
        has increased by the expected number since first called 

        :param expected: The expected increase since the object was created
        """
        self._assert_changed_by(expected, self._start)

    def assert_changed_by(self, expected):
        """
        Asserts that the result of calling the wrapped function
        has increased by the expected number since last asserted 

        :param expected: The expected increase since last asserted 
        """
        self._assert_changed_by(expected, self._last)

