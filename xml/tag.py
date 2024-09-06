from re import Pattern, compile


class Tag:
    OptionNameGroup: int = 1
    OptionValueGroup: int = 2

    OptionsPattern: Pattern = compile(r"([a-zA-Z_]+)\s*=\s*\"([^\"]+)\"")

    def __init__(self, name: str, options: str = "", is_closing: bool = False, auto_close: bool = False):
        self.name: str = name
        self._options: dict[str, str] = {
            m.group(self.OptionNameGroup): m.group(self.OptionValueGroup)
            for m in self.OptionsPattern.finditer(options)
        }
        self.is_closing: bool = is_closing
        self.auto_close: bool = auto_close

    def __str__(self) -> str:
        return f"<{self.name} {self._options} closing: {self.is_closing} auto_close: {self.auto_close}>"

    def __getitem__(self, item: str) -> str | None:
        result = self._options.get(item, None)

        if result is None:
            print(f"!! {self.name}-tag[{self._options.get('name', '<unnamed>')}] requires attribute '{item}'")

        return result

    def attr(self, item: str, default: str = "") -> str:
        return self._options.get(item, default)
