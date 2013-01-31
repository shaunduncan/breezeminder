# Activate the VENV
activate_this = '/opt/breezeminder/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))


# Since we aren't installing the app to site-packages
import os
import sys
sys.path.insert(0, '/opt/breezeminder/src/breezeminder')


# CORE
from breezeminder.app import (app as application,
                              auth,
                              context,
                              filters)

# OTHERS TO INCLUDE
from breezeminder import views, models
