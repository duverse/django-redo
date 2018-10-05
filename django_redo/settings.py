from django.conf import settings


class Settings(object):
    """
    Module settings helper.
    """
    prefix = 'REDO_'

    @staticmethod
    def get(key, default=None):
        key = '{}{}'.format(Settings.prefix, key)
        if not hasattr(settings, key):
            return default

        return getattr(settings, key)
