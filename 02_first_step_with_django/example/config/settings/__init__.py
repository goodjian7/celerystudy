import os
django_development = os.environ.get("DJANGO_DEVELOPMENT", "TRUE")
django_development =  django_development == "TRUE"

if django_development:
    from .settings_dev import *
else:
    from .settings_prod import *