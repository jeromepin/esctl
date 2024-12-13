import random
import ssl
from typing import Optional, Tuple, Union

from elasticsearch import Elasticsearch

from esctl.config import Context


class Client:
    def __new__(
        self,
        context: Optional[Union[Context, None]] = None,
        http_auth: Optional[Union[Tuple[str], None]] = None,
    ):
        if not hasattr(self, "instance"):
            self.instance = super().__new__(self)
            self.es = Client.initialize_elasticsearch_connection(
                self, context, http_auth
            )

        return self.instance

    @staticmethod
    def initialize_elasticsearch_connection(
        client,
        context: Optional[Union[Context, None]] = None,
        http_auth: Optional[Union[Tuple[str], None]] = None,
    ):
        elasticsearch_client_kwargs = {
            "http_auth": http_auth,
        }

        if context is not None:
            if context.settings.get("no_check_certificate"):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                elasticsearch_client_kwargs["ssl_context"] = ssl_context
                elasticsearch_client_kwargs["verify_certs"] = False

            if "max_retries" in context.settings:
                elasticsearch_client_kwargs["max_retries"] = context.settings.get(
                    "max_retries"
                )

            if "timeout" in context.settings:
                elasticsearch_client_kwargs["timeout"] = context.settings.get("timeout")

            return Elasticsearch(
                random.choice(context.cluster["servers"]), **elasticsearch_client_kwargs
            )
