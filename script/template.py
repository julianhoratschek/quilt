class Template:
    def __init__(self):
        self.text: str = ""
        self.alias: dict[str, str] = {}

    def __str__(self) -> str:
        return f"Aliases:\n" + "\n".join([f"\t{alias}: {value}" for alias, value in self.alias.items()])

