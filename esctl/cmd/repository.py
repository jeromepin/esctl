import argparse

from typing_extensions import override

from esctl.commands import EsctlCommand, EsctlLister, EsctlShowOne, ListerResult, ShowOneResult
from esctl.formatter import JSONToCliffFormatter


class RepositoryList(EsctlLister):
    """Returns information about snapshot repositories registered in the cluster."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        repositories = self.rows(self.es.cat.repositories(format="json"))

        return JSONToCliffFormatter(repositories).format_for_lister(
            columns=[("id"), ("type")],
        )


class RepositoryShow(EsctlShowOne):
    """Returns information about a repository."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        repository = self.es.snapshot.get_repository(
            name=parsed_args.repository,
        ).get(parsed_args.repository)
        self.response = repository

        return JSONToCliffFormatter(repository, pretty_key=self.pretty_keys).to_show_one(
            lines=list(repository.keys()),
        )

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "repository",
            help=("A comma-separated list of repository names"),
        )
        return parser


class RepositoryVerify(EsctlCommand):
    """Verifies a repository."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        repository = self.es.snapshot.verify_repository(
            name=parsed_args.repository,
        )

        self.print_output(repository)

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument("repository", help=("A repository name"))
        return parser
