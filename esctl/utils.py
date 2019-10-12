class Color:
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    END = "\033[0m"
    GREEN = "\033[92m"
    ITALIC = "\033[3m"
    PURPLE = "\033[95m"
    RED = "\033[91m"
    UNDERLINE = "\033[4m"
    YELLOW = "\033[93m"

    @classmethod
    def colorize(cls, text, color):
        return "{}{}{}".format(color, text, cls.END)


def flatten_dict(dictionary):
    def expand(key, value):
        if isinstance(value, dict):
            return [(key + "." + k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in dictionary.items() for item in expand(k, v)]

    return dict(items)
