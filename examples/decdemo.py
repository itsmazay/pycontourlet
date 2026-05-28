"""Run the bundled decdemo from outside the package.

This is a thin wrapper -- the actual demo lives at ``pycontourlet.demo``
so it ships with the installed package. Run with::

    python examples/decdemo.py
    python -m pycontourlet
    pycontourlet-demo

The latter two require ``pip install -e .`` (or ``pip install``).
"""

from pycontourlet.demo import main

if __name__ == "__main__":
    raise SystemExit(main())
