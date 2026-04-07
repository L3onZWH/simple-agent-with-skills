from add import add


def test_add_two_positive_numbers():
    assert add(1, 2) == 3


def test_add_negative_numbers():
    assert add(-1, -2) == -3


def test_add_positive_and_negative():
    assert add(5, -3) == 2


def test_add_with_zero():
    assert add(0, 0) == 0
    assert add(7, 0) == 7


def test_add_floats():
    assert add(1.5, 2.5) == 4.0
