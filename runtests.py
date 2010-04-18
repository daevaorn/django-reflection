#!/usr/bin/env python
from django.conf import settings
from django.core.management import call_command

settings.configure(
    INSTALLED_APPS=('django.contrib.contenttypes', 'django.contrib.auth', 'reflection',),
    DATABASE_ENGINE = 'sqlite3',
)

if __name__ == "__main__":
    call_command('test', 'reflection')
