#!/usr/bin/env python
"""Django's command-line utility (migrate, makemigrations, check, ...). Day-to-day commands: `python -m app`, `python -m pytest`."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
