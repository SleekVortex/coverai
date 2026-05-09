from dishka import AsyncContainer, make_async_container

from coverai.configs import Settings
from coverai.di.providers.queue_provider import QueueProvider
from coverai.di.providers.repository_provider import RepositoryProvider
from coverai.di.providers.service_provider import ServiceProvider
from coverai.di.providers.session_provider import SessionProvider
from coverai.di.providers.settings_provider import SettingsProvider


def create_di_container(settings: Settings) -> AsyncContainer:
    """Создает DI-контейнер."""
    return make_async_container(
        SettingsProvider(),
        SessionProvider(),
        QueueProvider(),
        RepositoryProvider(),
        ServiceProvider(),
        context={Settings: settings},
    )
