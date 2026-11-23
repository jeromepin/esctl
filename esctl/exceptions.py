class SettingNotFoundError(Exception):
    pass


class ConfigurationError(Exception):
    """The configuration file cannot be used."""


class ExternalCommandError(Exception):
    """A command defined in the configuration file failed."""
