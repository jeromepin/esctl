from collections.abc import Iterator

class CommandManager:
    namespace: str

    def __init__(self, namespace: str, convert_underscores: bool = True) -> None: ...
    def __iter__(self) -> Iterator[tuple[str, object]]: ...
