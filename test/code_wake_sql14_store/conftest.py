"""Pytest configuration / fixtures."""


import pytest
from code_wake.test.conftest import *

from code_wake_sql14_store import Sql14Store


@pytest.fixture
def store_params():
    return (["sqlite:///:memory:"], {})


@pytest.fixture
def store_cls():
    return Sql14Store
