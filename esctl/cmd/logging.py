from esctl.commands import EsctlCommandLogging


class LoggingGet(EsctlCommandLogging):
    """Get a logger value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        level = (
            self.cluster_settings.get(parsed_args.logger, persistency=persistency) or ""
        )

        print("{} : {}".format(str(parsed_args.logger), str(level)))


class LoggingReset(EsctlCommandLogging):
    """Reset a logger value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        print("Resetting logger {}".format(parsed_args.logger))
        print(
            self.cluster_settings.set(parsed_args.logger, None, persistency=persistency)
        )


class LoggingSet(EsctlCommandLogging):
    """Set a logger value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        print("Changing logger {} to {}".format(parsed_args.logger, parsed_args.level))

        print(
            self.cluster_settings.set(
                parsed_args.logger, parsed_args.level, persistency=persistency
            )
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "level",
            metavar="<level>",
            help=("Log level"),
            choices=["TRACE", "DEBUG", "INFO", "WARN"],
        )
        return parser
