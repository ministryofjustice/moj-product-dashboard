from django.apps import AppConfig


class DashboardConfig(AppConfig):
    # this dotted name is necessary because
    # the app name dashboard is the same as
    # the top directory, which causes import
    # issues if not used.
    name = 'dashboard.apps.dashboard'

    def ready(self):
        from . import signals
