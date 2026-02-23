"""Smoke-test that core packages are importable."""


def test_import_taskx():
    import dopetask

    assert hasattr(taskx, "__version__")


def test_import_taskx_schemas():
    import dopetask_schemas

    assert hasattr(taskx_schemas, "__version__")


def test_import_taskx_adapters():
    import dopetask_adapters  # noqa: F401
