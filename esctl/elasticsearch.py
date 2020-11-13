import ssl
from typing import Optional, Tuple, Union

from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context

from esctl.config import Context
from esctl.override import EsctlTransport


class Client:
    def __new__(
        self,
        context: Optional[Union[Context, None]] = None,
        http_auth: Optional[Union[Tuple[str], None]] = None,
        scheme: Optional[str] = "https",
    ):
        if not hasattr(self, "instance"):
            self.instance = super().__new__(self)
            self.es = Client.initialize_elasticsearch_connection(
                self, context, http_auth, scheme
            )

        return self.instance

    @staticmethod
    def initialize_elasticsearch_connection(
        client,
        context: Optional[Union[Context, None]] = None,
        http_auth: Optional[Union[Tuple[str], None]] = None,
        scheme: Optional[str] = "https",
    ):
        elasticsearch_client_kwargs = {
            "http_auth": http_auth,
            "scheme": scheme,
            "transport_class": EsctlTransport,
        }

        if context is not None:
            if scheme == "https":
                if context.settings.get("no_check_certificate"):
                    ssl_context = create_ssl_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    elasticsearch_client_kwargs["ssl_context"] = ssl_context

            if "max_retries" in context.settings:
                elasticsearch_client_kwargs["max_retries"] = context.settings.get(
                    "max_retries"
                )

            if "timeout" in context.settings:
                elasticsearch_client_kwargs["timeout"] = context.settings.get("timeout")

            return Elasticsearch(
                context.cluster.get("servers"), **elasticsearch_client_kwargs
            )
