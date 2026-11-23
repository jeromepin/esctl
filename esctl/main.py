import argparse
import importlib.metadata
import logging
import re
import shlex
import subprocess
import sys
import threading
from collections import deque
from typing import Any, ClassVar

from cliff.app import App
from cliff.commandmanager import CommandManager

from esctl import utils
from esctl.config import ConfigFileParser
from esctl.elasticsearch import Client
from esctl.exceptions import ExternalCommandError
from esctl.interactive import InteractiveApp

# `configure_logging` and `build_option_parser` methods comes from cliff
# and are modified


DISTRIBUTION_NAME = "esctl"


class ColoredLevelFormatter(logging.Formatter):
    """Colorize the level name, without touching the global level names
    (which would also color log files and accumulate across app instances)."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: utils.Color.END,
        logging.INFO: utils.Color.BLUE,
        logging.WARNING: utils.Color.YELLOW,
        logging.ERROR: utils.Color.PURPLE,
        logging.CRITICAL: utils.Color.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Work on a copy: the same record goes through the other handlers
        record = logging.makeLogRecord(record.__dict__)
        record.levelname = utils.Color.colorize(record.levelname, self.COLORS.get(record.levelno, utils.Color.END))
        return super().format(record)


# Seconds a pre-command gets to exit after SIGTERM before being killed
PRE_COMMAND_STOP_TIMEOUT = 5
# Lines of a background pre-command's stderr kept to explain its failure
PRE_COMMAND_OUTPUT_TAIL = 50


class Esctl(App):
    log = App.LOG

    def __init__(self):
        super().__init__(
            description=importlib.metadata.metadata(DISTRIBUTION_NAME)["Summary"],
            version=importlib.metadata.version(DISTRIBUTION_NAME),
            command_manager=CommandManager("esctl"),
            deferred_help=True,
            interactive_app_factory=InteractiveApp,
        )
        self.interactive_mode = False
        self.config_file_parser = ConfigFileParser()
        # Loaded by initialize_app(), before any command runs
        self.config: dict[str, Any] = {}
        self._connected = False
        self._pre_command_processes: list[subprocess.Popen] = []
        self._pre_command_drains: list[threading.Thread] = []

    def configure_logging(self):
        """Create logging handlers for any log output."""
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        logging.getLogger("stevedore.extension").setLevel(logging.WARNING)

        # Set up logging to a file
        if self.options.log_file:
            file_handler = logging.FileHandler(filename=self.options.log_file)
            formatter = logging.Formatter(self.LOG_FILE_MESSAGE_FORMAT)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Always send higher-level messages to the console via stderr
        console = logging.StreamHandler(self.stderr)
        console_level = {
            0: logging.ERROR,  # quiet, with -q flag
            1: logging.WARNING,  # default, without -v or -q flags
            2: logging.INFO,
            3: logging.DEBUG,
        }.get(self.options.verbose_level, logging.DEBUG)
        console.setLevel(console_level)

        formatter = ColoredLevelFormatter(
            "[%(levelname)-8s] " + self.CONSOLE_MESSAGE_FORMAT,
        )
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def resolve_external_credentials(self, user: dict[str, Any]) -> None:
        """Replace `external_username`/`external_password` by the output of their command."""
        for field in ("username", "password"):
            definition = user.pop(f"external_{field}", None)
            if definition is not None:
                user[field] = self._run_os_system_command(
                    definition["command"]["run"],
                    purpose=field,
                )

    def initialize_app(self, argv):
        self.config = self.config_file_parser.load_configuration(
            self.options.config_file,
        )
        self.context = self.config_file_parser.create_context(self.options.context)

    @staticmethod
    def _requires_cluster(cmd) -> bool:
        # cliff's own commands (help, complete) don't define it and are local too
        return getattr(cmd, "requires_cluster", False)

    def connect(self):
        """Resolve the credentials and configure the Elasticsearch client, once."""
        if self._connected:
            return

        http_auth: tuple[str, str] | None = None

        if self.context.user is not None:
            self.resolve_external_credentials(self.context.user)

            username, password = self.context.user.get("username"), self.context.user.get("password")
            if username and password:
                http_auth = (username, password)

        Client.configure(self.context, http_auth)
        self._connected = True

    def _run_os_system_command(self, raw_command: str, purpose: str) -> str:
        """Run a shell command from the configuration file and return its output."""
        self.log.debug("Running command : %s", raw_command)
        # Running through a shell is intended: users write pipelines in their config file
        completed = subprocess.run(
            raw_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            msg = (
                f"The command retrieving the {purpose} failed with exit code {completed.returncode}: "
                f"`{raw_command}`\n{completed.stderr.strip()}"
            )
            raise ExternalCommandError(msg)

        value = completed.stdout.strip()
        if not value:
            msg = f"The command retrieving the {purpose} printed nothing: `{raw_command}`"
            raise ExternalCommandError(msg)

        return value

    def _run_shell_subcommand(self, command):
        command = shlex.split(command)
        self.log.debug("Running pre-command : %s", command)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return process

    def prepare_to_run_command(self, cmd):
        if not self._requires_cluster(cmd):
            return

        self.connect()

        for command_block in self.context.pre_commands:
            command: str = command_block["command"]
            process = self._run_shell_subcommand(command)
            self._pre_command_processes.append(process)

            if command_block.get("wait_for_exit"):
                _, stderr = process.communicate()

                if process.returncode != 0:
                    msg = (
                        f"Pre-command `{command}` failed with exit code {process.returncode}\n"
                        f"{stderr.decode(errors='replace').strip()}"
                    )
                    raise ExternalCommandError(msg)

            else:
                # Nobody else reads the pipes of a background command: if they
                # fill up, the command blocks on its next write.
                stderr_drain, stderr_tail = self._drain(process.stderr, command)

                if command_block.get("wait_for_output"):
                    self._wait_for_output(
                        process,
                        command,
                        command_block["wait_for_output"],
                        stderr_drain,
                        stderr_tail,
                    )

                self._drain(process.stdout, command)

    def _drain(self, stream, command: str) -> tuple[threading.Thread, deque]:
        """Read a pipe in the background, logging it and keeping its last lines."""
        tail: deque[str] = deque(maxlen=PRE_COMMAND_OUTPUT_TAIL)

        def drain():
            try:
                for raw_line in stream:
                    line = raw_line.decode("utf-8", errors="replace").rstrip()
                    tail.append(line)
                    self.log.debug("[%s] %s", command, line)
            except (OSError, ValueError):
                # The pipe was closed while stopping the command
                pass

        thread = threading.Thread(target=drain, daemon=True)
        thread.start()
        self._pre_command_drains.append(thread)
        return thread, tail

    def _wait_for_output(
        self,
        process: subprocess.Popen,
        command: str,
        string_to_look_for: str,
        stderr_drain: threading.Thread,
        stderr_tail: deque,
    ):
        pattern = re.compile(string_to_look_for)
        stdout = process.stdout
        if stdout is None:
            msg = "Pre-commands must be started with a piped stdout"
            raise RuntimeError(msg)

        for raw_line in stdout:
            line = raw_line.decode("utf-8", errors="replace").strip()

            if pattern.search(line):
                self.log.debug("Got `%s` from `%s`", string_to_look_for, command)
                return

            self.log.debug("Expecting command output to match `%s` but got `%s`...", string_to_look_for, line)

        # stdout was closed without the expected line: the command is gone or useless
        process.wait()
        stderr_drain.join(timeout=PRE_COMMAND_STOP_TIMEOUT)
        stderr = "\n".join(stderr_tail)
        msg_0 = (
            f"Pre-command `{command}` exited with code {process.returncode} "
            f"before printing a line matching `{string_to_look_for}`\n{stderr}"
        )
        raise ExternalCommandError(
            msg_0,
        )

    def clean_up(self, cmd, result, err):
        self._stop_pre_commands()

        if err:
            self.log.debug("got an error: %s", err)

    def _stop_pre_commands(self):
        """Stop every pre-command started for the current command, even if starting them failed midway."""
        processes, self._pre_command_processes = self._pre_command_processes, []
        drains, self._pre_command_drains = self._pre_command_drains, []

        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=PRE_COMMAND_STOP_TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        for drain in drains:
            drain.join(timeout=PRE_COMMAND_STOP_TIMEOUT)

        for process in processes:
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """Return an argparse option parser for this application."""
        argparse_kwargs = argparse_kwargs or {}
        parser = argparse.ArgumentParser(
            description=description,
            add_help=False,
            **argparse_kwargs,
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version}",
        )
        verbose_group = parser.add_mutually_exclusive_group()
        verbose_group.add_argument(
            "-v",
            "--verbose",
            action="count",
            dest="verbose_level",
            default=self.DEFAULT_VERBOSE_LEVEL,
            help="Increase verbosity of output. Can be repeated.",
        )
        verbose_group.add_argument(
            "-q",
            "--quiet",
            action="store_const",
            dest="verbose_level",
            const=0,
            help="Suppress output except errors.",
        )
        parser.add_argument(
            "--log-file",
            action="store",
            default=None,
            help="Specify a file to log output. Disabled by default.",
        )
        parser.add_argument(
            "--config",
            action="store",
            default="~/.esctlrc",
            help="Path to the config file",
            dest="config_file",
        )
        if self.deferred_help:
            parser.add_argument(
                "-h",
                "--help",
                dest="deferred_help",
                action="store_true",
                help="Show help message and exit.",
            )

        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
            help="Show tracebacks on errors.",
        )

        parser.add_argument(
            "--context",
            action="store",
            help="Context to use",
            type=str,
        )

        return parser


def main(argv=sys.argv[1:]):
    esctl = Esctl()
    return esctl.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
