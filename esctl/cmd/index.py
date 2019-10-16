from esctl.commands import EsctlCommandIndex, EsctlLister
from esctl.main import Esctl
from esctl.formatter import JSONToCliffFormatter


class IndexCreate(EsctlCommandIndex):
    """Create an index."""

    def take_action(self, parsed_args):
        self.log.info("Creating index {}".format(parsed_args.index))
        print(Esctl._es.indices.create(index=parsed_args.index))


class IndexList(EsctlLister):
    """List all indices."""

    def take_action(self, parsed_args):
        indices = Esctl._es.cat.indices(format="json")
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


class IndexClose(EsctlCommandIndex):
    """Close an index."""

    def take_action(self, parsed_args):
        self.log.info("Closing index " + parsed_args.index)
        print(Esctl._es.indices.close(index=parsed_args.index))


class IndexDelete(EsctlCommandIndex):
    """Delete an index."""

    def take_action(self, parsed_args):
        self.log.info("Deleting index " + parsed_args.index)
        print(Esctl._es.indices.delete(index=parsed_args.index))


class IndexOpen(EsctlCommandIndex):
    """Open an index."""

    def take_action(self, parsed_args):
        self.log.info("Opening index " + parsed_args.index)
        print(Esctl._es.indices.open(index=parsed_args.index))