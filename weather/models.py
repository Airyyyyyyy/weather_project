from django.db import models  # noqa: F401

# This app intentionally has no persisted models: tracked cities live in the
# Django session (see weather/views.py), which is sufficient for a no-login
# demo app. See README's "known limitations" section for the tradeoff.