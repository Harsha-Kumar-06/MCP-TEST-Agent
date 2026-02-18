"""Test packages_distributions specifically"""
import sys
print(f"Python version: {sys.version}")

# First try the built-in version
print("\nTrying built-in importlib.metadata.packages_distributions()...")
try:
    import importlib.metadata as builtin_metadata
    result = builtin_metadata.packages_distributions()
    print(f"SUCCESS - found {len(result)} packages")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")

# Now try the third-party version
print("\nTrying importlib_metadata.packages_distributions()...")
try:
    import importlib_metadata
    print(f"importlib_metadata version: {importlib_metadata.version('importlib_metadata')}")
    result = importlib_metadata.packages_distributions()
    print(f"SUCCESS - found {len(result)} packages")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
