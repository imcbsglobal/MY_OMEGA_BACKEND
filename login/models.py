# login/models.py
from django.db import models

# No models needed for the superuser ID+password JWT login flow.
# We rely entirely on Django's built-in User model.
# Add your own models here later if needed (e.g., profiles, logs, etc.).