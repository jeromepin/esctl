from esctl.commands import EsctlCommand, EsctlCommandIndex, EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class IndexCreate(EsctlCommand):
    """Create an index.

    Read the index configuration as a JSON document from either stdin or a path.
    """

    def take_action(self, parsed_args):
        configuration = self.read_from_file_or_stdin(parsed_args.configuration)

        self.log.info("Creating index {}".format(parsed_args.index))
        print(self.es.indices.create(index=parsed_args.index, body=configuration))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("index", help="Name of the index to create")
        parser.add_argument(
            "--configuration",
            metavar="PATH",
            help="Path to the JSON document containing the index configuration (mapping, aliases, settings)",
        )
        return parser


class IndexList(EsctlLister):
    """Returns information about indices: number of primaries and replicas, document counts, disk size, ..."""

    def take_action(self, parsed_args):
        indices = self.transform(
            self.es.cat.indices(format="json", index=parsed_args.index)
        )
        return JSONToCliffFormatter(indices).format_for_lister(
            columns=[
                ("index"),
                ("health",),
                ("status"),
                ("uuid", "UUID"),
                ("pri", "Primary"),
                ("rep", "Replica"),
                ("docs.count"),
                ("docs.deleted"),
                ("store.size"),
                ("pri.store.size", "Primary Store Size"),
            ]
        )

    def transform(self, indices):
        if self.uses_table_formatter():
            for idx, indice in enumerate(indices):
                indices[idx]["health"] = Color.colorize(
                    indice.get("health"), getattr(Color, indice.get("health").upper())
                )

                if indice.get("status") == "close":
                    indices[idx]["status"] = Color.colorize(
                        indice.get("status"), Color.ITALIC
                    )

        return indices

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index",
            help="A comma-separated list of index names to limit the returned information",
            nargs="?",
        )
        return parser


class IndexClose(EsctlCommandIndex):
    """Close an index."""

    def take_action(self, parsed_args):
        self.log.info("Closing index " + parsed_args.index)
        print(self.es.indices.close(index=parsed_args.index))


class IndexDelete(EsctlCommandIndex):
    """Delete an index."""

    def take_action(self, parsed_args):
        self.log.info("Deleting index " + parsed_args.index)
        print(self.es.indices.delete(index=parsed_args.index))


class IndexOpen(EsctlCommandIndex):
    """Open an index."""

    def take_action(self, parsed_args):
        self.log.info("Opening index " + parsed_args.index)
        print(self.es.indices.open(index=parsed_args.index))
