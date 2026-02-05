"""Smoke-test that core packages are importable."""


def test_import_taskx():
    import taskx

    assert hasattr(taskx, "__version__")


def test_import_taskx_schemas():
    import taskx_schemas

    assert hasattr(taskx_schemas, "__version__")


def test_import_taskx_adapters():
    import taskx_adapters  # noqa: F401
