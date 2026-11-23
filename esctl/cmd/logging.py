from esctl.commands import EsctlCommandLogging, selected_persistency


class LoggingGet(EsctlCommandLogging):
    """Get a logger value."""

    def take_action(self, parsed_args):
        persistency = selected_persistency(parsed_args)
        self.log.debug("Persistency is %s", persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        setting = self.cluster_settings.get(parsed_args.logger, persistency=persistency)

        print(f"{parsed_args.logger} : {setting.value or ''}")


class LoggingReset(EsctlCommandLogging):
    """Reset a logger value."""

    def take_action(self, parsed_args):
        persistency = selected_persistency(parsed_args)
        self.log.debug("Persistency is %s", persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        print(f"Resetting logger {parsed_args.logger}")
        print(
            self.cluster_settings.set(parsed_args.logger, None, persistency=persistency),
        )


class LoggingSet(EsctlCommandLogging):
    """Set a logger value."""

    def take_action(self, parsed_args):
        persistency = selected_persistency(parsed_args)
        self.log.debug("Persistency is %s", persistency)

        if not parsed_args.logger.startswith("logger"):
            parsed_args.logger = "logger." + parsed_args.logger

        print(f"Changing logger {parsed_args.logger} to {parsed_args.level}")

        print(
            self.cluster_settings.set(
                parsed_args.logger,
                parsed_args.level,
                persistency=persistency,
            ),
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
