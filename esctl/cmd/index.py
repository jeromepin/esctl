from esctl.commands import EsctlCommandIndex, EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class IndexCreate(EsctlCommandIndex):
    """Create an index."""

    def take_action(self, parsed_args):
        self.log.info("Creating index {}".format(parsed_args.index))
        print(self.es.indices.create(index=parsed_args.index))


class IndexList(EsctlLister):
    """List all indices."""

    def take_action(self, parsed_args):
        indices = self.transform(self.es.cat.indices(format="json"))
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
        if self.formatter.__class__.__name__ == "TableFormatter":
            for idx, indice in enumerate(indices):
                indices[idx]["health"] = Color.colorize(
                    indice.get("health"), getattr(Color, indice.get("health").upper())
                )

                if indice.get("status") == "close":
                    indices[idx]["status"] = Color.colorize(
                        indice.get("status"), Color.ITALIC
                    )

        return indices


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
