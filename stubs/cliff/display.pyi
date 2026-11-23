from cliff.command import Command

class DisplayCommandBase(Command):
    # The formatter plugin selected with --format, set when the command runs
    formatter: object
