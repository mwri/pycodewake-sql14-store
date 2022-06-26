# Python code wake SQL Academy 1.4 store adapter (pycodewake-sql14-store)

[![test](https://github.com/mwri/pycodewake-sql14-store/actions/workflows/test.yml/badge.svg)](https://github.com/mwri/pycodewake-sql14-store/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/mwri/pycodewake-sql14-store/branch/main/graph/badge.svg)](https://codecov.io/gh/mwri/pycodewake-sql14-store)

This store adapter provides backing via SQL Academy 1.4 for Code Wake.

For example:

```python
import code_wake
from code_wake_sql14_store import Sql14Store

cwproc = code_wake.Process(
    app_name="my_app",
    app_vsn="1.2.3",
    env_name="production",
    store=Sql14Store("sqlite:////tmp/some_file.sqlite"),
)
```
