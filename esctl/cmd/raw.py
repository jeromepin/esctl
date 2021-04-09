from esctl.commands import EsctlCommand


class RawCommand(EsctlCommand):
    """Performs a raw HTTP call. Useful when esctl doesn't provide a nice interface for a specific route."""

    def take_action(self, parsed_args):
        print(
            self.es.transport.perform_request(
                parsed_args.verb.upper(), parsed_args.route, body=parsed_args.body
            )
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "-d",
            "--data",
            help="Specify the body to send",
            metavar="BODY",
            dest="body",
        )
        parser.add_argument(
            "-X",
            "--request",
            help="Specify the HTTP verb to use.",
            default="GET",
            metavar="VERB",
            dest="verb",
        )
        parser.add_argument(
            "route",
            help="The route to call for.",
        )
        return parser
