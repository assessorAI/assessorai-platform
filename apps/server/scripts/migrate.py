#!/usr/bin/env python3
"""Compatibility shim forwarding to the new manage_db utility."""

from scripts.manage_db import main

if __name__ == "__main__":
    main()
