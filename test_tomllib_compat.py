#!/usr/bin/env python3
"""
Test script to verify tomllib compatibility across Python versions.
This simulates the import behavior for the test fixes.
"""

import sys
from pathlib import Path

def test_tomllib_import():
    """Test that our tomllib import logic works correctly."""
    print(f"Testing with Python {sys.version}")

    # Simulate the import logic from our test
    tomllib = None
    import_method = None

    try:
        import tomllib  # Python 3.11+
        import_method = "tomllib (Python 3.11+)"
        print(f"✅ Successfully imported: {import_method}")
        assert tomllib is not None, "tomllib should be available"
        return
    except ImportError:
        print("tomllib not available, trying tomli...")
        try:
            import tomli as tomllib  # Python 3.9-3.10 fallback
            import_method = "tomli (fallback for Python 3.9-3.10)"
            print(f"✅ Successfully imported: {import_method}")
            assert tomllib is not None, "tomli should be available as fallback"
            return
        except ImportError:
            print("❌ No TOML library available (neither tomllib nor tomli)")
            assert False, "No TOML library available"

if __name__ == "__main__":
    tomllib = test_tomllib_import()
    if tomllib:
        print("🎉 tomllib compatibility test passed!")
    else:
        print("💥 tomllib compatibility test failed!")
        sys.exit(1)
