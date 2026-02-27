"""Smoke-test that core packages are importable."""


def test_import_dopetask():
    import dopetask

    assert hasattr(dopetask, "__version__")


def test_import_dopetask_schemas():
    import dopetask_schemas

    assert hasattr(dopetask_schemas, "__version__")


def test_import_dopetask_adapters():
    import dopetask_adapters  # noqa: F401
