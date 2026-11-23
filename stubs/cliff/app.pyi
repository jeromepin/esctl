import argparse
import logging
from collections.abc import Callable
from typing import Any, ClassVar, TextIO

from cliff.command import Command
from cliff.commandmanager import CommandManager

class App:
    NAME: ClassVar[str]
    LOG: ClassVar[logging.Logger]
    CONSOLE_MESSAGE_FORMAT: ClassVar[str]
    LOG_FILE_MESSAGE_FORMAT: ClassVar[str]
    DEFAULT_VERBOSE_LEVEL: ClassVar[int]
    DEFAULT_OUTPUT_ENCODING: ClassVar[str]

    command_manager: CommandManager
    deferred_help: bool
    interactive_mode: bool
    parser: argparse.ArgumentParser
    options: argparse.Namespace
    stdin: TextIO
    stdout: TextIO
    stderr: TextIO

    def __init__(
        self,
        description: str,
        version: str,
        command_manager: CommandManager,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        interactive_app_factory: Callable[..., object] | None = None,
        deferred_help: bool = False,
    ) -> None: ...
    def build_option_parser(
        self,
        description: str,
        version: str,
        argparse_kwargs: dict[str, Any] | None = None,
    ) -> argparse.ArgumentParser: ...
    def configure_logging(self) -> None: ...
    def run(self, argv: list[str]) -> int: ...
    def run_subcommand(self, argv: list[str]) -> int: ...
    def initialize_app(self, argv: list[str]) -> None: ...
    def prepare_to_run_command(self, cmd: Command) -> None: ...
    def clean_up(self, cmd: Command, result: int, err: BaseException | None) -> None: ...
