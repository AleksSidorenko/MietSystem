import pytest
from IPython.utils.syspathcontext import appended_to_syspath


def test_append_deprecated():
    with pytest.warns(DeprecationWarning):
        appended_to_syspath(".")
