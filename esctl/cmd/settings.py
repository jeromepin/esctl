from esctl.commands import EsctlCommandSetting
from esctl.utils import Color


class ClusterSettingsGet(EsctlCommandSetting):
    """Get a setting value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        setting = self.settings.get(
            parsed_args.setting, persistency=persistency
        )

        if setting.value is not None:
            if setting.persistency is "defaults":
                output = "{} ({})".format(
                    setting.value, Color.colorize("default", Color.ITALIC)
                )
            else:
                output = setting.value

            print(output)

        else:
            self.log.error(
                "{} does not exists in {} cluster settings.".format(
                    Color.colorize(setting.name, Color.ITALIC),
                    Color.colorize(persistency, Color.ITALIC),
                )
            )


class ClusterSettingsReset(EsctlCommandSetting):
    """Reset a setting value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)
        print(
            "Resetting {} to its default value".format(
                Color.colorize(parsed_args.setting, Color.ITALIC)
            )
        )
        print(
            self.settings.set(
                parsed_args.setting, None, persistency=persistency
            )
        )


class ClusterSettingsSet(EsctlCommandSetting):
    """Set a setting value."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        print(
            "Changing {} to {}".format(
                Color.colorize(parsed_args.setting, Color.ITALIC),
                Color.colorize(parsed_args.value, Color.ITALIC),
            )
        )

        print(
            self.settings.set(
                parsed_args.setting, parsed_args.value, persistency=persistency
            )
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("value", metavar="<value>", help=("Setting value"))
        return parser
