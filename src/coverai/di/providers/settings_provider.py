from dishka import Provider, Scope, from_context

from coverai.configs import Settings


class SettingsProvider(Provider):
    settings = from_context(Settings, scope=Scope.APP)
