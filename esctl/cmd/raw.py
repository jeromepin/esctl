import json

from esctl.commands import EsctlCommand


class RawCommand(EsctlCommand):
    """Performs a raw HTTP call. Useful when esctl doesn't provide a nice interface for a specific route."""

    def take_action(self, parsed_args):
        body: str = parsed_args.body

        if parsed_args.body is not None and parsed_args.body.startswith("@"):
            body = self.read_from_file_or_stdin(parsed_args.body[1:])

        print(
            json.dumps(
                self.request(verb=parsed_args.verb, route=parsed_args.route, body=body),
            ),
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "-d",
            "--data",
            help=(
                "Specify the body to send. If you start the data with the letter @, "
                "the rest should be a file name to read the data from, or - if you want curl "
                "to read the data from stdin."
            ),
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
