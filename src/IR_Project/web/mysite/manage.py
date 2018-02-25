#!/usr/bin/env python
import os
import sys
sys.path.append('/Users/Leo/Documents/github/NIR/leo/IR_Project/web/mysite/')
import myLib.utils as utils
from  myLib.preload import *

def preload():
    preloadInstance1 = Preload()
    print('hello')
    if Preload.db == None:
        preloadInstance1.init()
        print('--------preload--------')
        print(Preload.db)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings") 
    preload()
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
