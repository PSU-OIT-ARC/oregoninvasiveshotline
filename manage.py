#!/usr/bin/env python
import os
import sys


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oregoninvasiveshotline.settings')
    os.environ.setdefault('EMCEE_CMD_ENV', 'dev')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
