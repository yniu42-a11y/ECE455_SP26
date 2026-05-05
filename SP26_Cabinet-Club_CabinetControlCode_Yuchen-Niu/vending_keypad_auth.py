#!/usr/bin/env python3
"""
Backward-compatible wrapper.
Use main.py as the primary entrypoint.

This file preserves legacy launch commands while delegating all logic to main().
"""

from main import main


if __name__ == "__main__":
    main()
