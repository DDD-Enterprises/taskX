# dopeTask Migration Guide for dopemux

## Overview

This guide provides step-by-step instructions for migrating dopemux from `dopetask-kernel` to `dopetask`.

## Changes Required in dopemux

### 1. Update Package Dependencies

**File**: `pyproject.toml` or `requirements.txt`

**Before**:
```toml
[tool.poetry.dependencies]
dopetask-kernel = "^0.1.3"
```

**After**:
```toml
[tool.poetry.dependencies]
dopetask = "^0.1.4"
```

### 2. Update Import Statements

**Find and replace all occurrences**:

```python
# Before
import dopetask
from dopetask import some_module
from dopetask.some_module import some_function

# After  
import dopetask
from dopetask import some_module
from dopetask.some_module import some_function
```

### 3. Update CLI Commands

**Both commands will work** (backward compatibility maintained):
- `dopetask` (new, preferred)
- `dopetask` (old, still works)

No changes needed in scripts that call the CLI.

### 4. Update Installation Scripts

**File**: Any installation or setup scripts

**Before**:
```bash
pip install dopetask-kernel
```

**After**:
```bash
pip install dopetask
```

### 5. Update Documentation

**Find and replace in all documentation**:
- `dopetask-kernel` → `dopetask`
- `dopeTask` → `dopetask` (where referring to the package)
- Keep `dopetask` CLI references (backward compatibility)

### 6. Update Configuration Files

**File**: `.dopetask-pin` (if exists)

**Before**:
```
install=pypi
ref=0.1.3
```

**After**:
```
install=pypi
ref=0.1.4
```

## Migration Steps

### Step 1: Update Dependencies

```bash
# Using pip
pip install --upgrade dopetask

# Using poetry
poetry add dopetask@^0.1.4
poetry remove dopetask-kernel

# Using uv
uv add dopetask
uv remove dopetask-kernel
```

### Step 2: Update Imports

Run a global search and replace:

```bash
# Find all dopetask imports
grep -r "import dopetask" . --include="*.py"
grep -r "from dopetask" . --include="*.py"

# Replace them (use sed or your IDE's find/replace)
sed -i 's/import dopetask/import dopetask/g' $(find . -name "*.py")
sed -i 's/from dopetask/from dopetask/g' $(find . -name "*.py")
```

### Step 3: Test the Migration

```bash
# Test imports
python -c "import dopetask; print('✅ dopetask import works')"

# Test CLI
dopetask --version
dopetask --version  # Should still work

# Run your test suite
pytest
```

### Step 4: Update Documentation

```bash
# Find documentation references
grep -r "dopetask-kernel" . --include="*.md"
grep -r "dopeTask" . --include="*.md" | grep -i package

# Update them manually or with sed
sed -i 's/dopetask-kernel/dopetask/g' $(find . -name "*.md")
```

## Backward Compatibility

### What Still Works

- ✅ `dopetask` CLI command (points to same binary as `dopetask`)
- ✅ All existing functionality
- ✅ All CLI commands and flags
- ✅ Configuration file formats

### What Changed

- ❌ `import dopetask` in Python code (must use `import dopetask`)
- ❌ `pip install dopetask-kernel` (must use `pip install dopetask`)

## Troubleshooting

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'dopetask'`

**Solution**: Update imports to use `dopetask`:
```python
# Change this
import dopetask

# To this
import dopetask
```

### Installation Errors

**Error**: `Could not find a version that satisfies the requirement dopetask-kernel`

**Solution**: Install the new package:
```bash
pip install dopetask
```

### CLI Command Not Found

**Error**: `command not found: dopetask`

**Solution**: Reinstall the package:
```bash
pip install --upgrade dopetask
```

## Verification Checklist

- [ ] `import dopetask` works in Python
- [ ] `dopetask --version` shows 0.1.4
- [ ] `dopetask --version` still works (backward compatibility)
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CI/CD pipelines updated
- [ ] Dependencies updated in all environment files

## Support

For issues with the migration:

1. Check the [dopetask documentation](https://github.com/hu3mann/dopeTask)
2. Review this migration guide
3. Test in a staging environment first
4. Open an issue if you encounter problems

---

*Generated: 2024-02-24*  
*dopeTask Version: 0.1.4*