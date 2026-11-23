import random
import ssl

from elasticsearch import Elasticsearch

from esctl.config import Context


class ClientNotConfiguredError(RuntimeError):
    pass


class Client:
    """Process-wide holder of the Elasticsearch client.

    The application configures it once the configuration file and the context
    are loaded. Commands and settings helpers must fetch it lazily through
    `Client.get()` instead of at import time, because modules can be imported
    before the application is initialized.
    """

    _es: Elasticsearch | None = None

    @classmethod
    def configure(
        cls,
        context: Context,
        http_auth: tuple[str, str] | None = None,
    ) -> Elasticsearch:
        cls._es = cls.initialize_elasticsearch_connection(context, http_auth)
        return cls._es

    @classmethod
    def get(cls) -> Elasticsearch:
        if cls._es is None:
            raise ClientNotConfiguredError(
                "The Elasticsearch client was used before the application configured it",
            )
        return cls._es

    @classmethod
    def reset(cls) -> None:
        cls._es = None

    @staticmethod
    def initialize_elasticsearch_connection(
        context: Context,
        http_auth: tuple[str, str] | None = None,
    ) -> Elasticsearch:
        elasticsearch_client_kwargs = {
            "http_auth": http_auth,
        }

        if context.settings.get("no_check_certificate"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            elasticsearch_client_kwargs["ssl_context"] = ssl_context
            elasticsearch_client_kwargs["verify_certs"] = False

        if "max_retries" in context.settings:
            elasticsearch_client_kwargs["max_retries"] = context.settings.get(
                "max_retries",
            )

        if "timeout" in context.settings:
            elasticsearch_client_kwargs["timeout"] = context.settings.get("timeout")

        return Elasticsearch(
            random.choice(context.cluster["servers"]),
            **elasticsearch_client_kwargs,
        )
