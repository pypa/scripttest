import doctest
import os

def test_index():
    failure, success = doctest.testfile(
        "../docs/index.txt",
        optionflags=doctest.ELLIPSIS,
        report=True)
    assert success
    assert not failure

