from esctl.commands import EsctlCommand, EsctlLister, EsctlShowOne
from esctl.formatter import JSONToCliffFormatter


class RepositoryList(EsctlLister):
    """Returns information about snapshot repositories registered in the cluster."""

    def take_action(self, parsed_args):
        repositories = self.es.cat.repositories(format="json")

        return JSONToCliffFormatter(repositories).format_for_lister(
            columns=[("id"), ("type")]
        )


class RepositoryShow(EsctlShowOne):
    """Returns information about a repository."""

    def take_action(self, parsed_args):
        repository = self.es.snapshot.get_repository(
            repository=parsed_args.repository, format="json"
        ).get(parsed_args.repository)

        return JSONToCliffFormatter(repository).to_show_one(
            lines=list(repository.keys())
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "repository", help=("A comma-separated list of repository names")
        )
        return parser


class RepositoryVerify(EsctlCommand):
    """Verifies a repository."""

    def take_action(self, parsed_args):
        repository = self.es.snapshot.verify_repository(
            repository=parsed_args.repository, format="json"
        )

        print(repository)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("repository", help=("A repository name"))
        return parser
