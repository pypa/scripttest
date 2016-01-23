from __future__ import absolute_import

import pytest

PY2 = pytest.mark.skipif("sys.version_info >= (3, 0)",
                         reason="Python 3.x only")
PY3 = pytest.mark.skipif("sys.version_info < (3, 0)",
                         reason="Python 2.x only")
