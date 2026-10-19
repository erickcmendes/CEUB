"""
# NFR-06, D-006: Verification of repository skeleton and importability of portfolio_opt
"""

import portfolio_opt


def test_package_import():
    """# NFR-06: Ensure portfolio_opt package imports cleanly and has version."""
    assert portfolio_opt.__version__ == "0.1.0"
