from re import Match, Pattern, compile, search, sub


def glob(pattern: str, text_list: list[str]) -> bool:

    def repl(m: Match) -> str:
        return {".": r"\.", "?": ".", "*": ".*?"}[m.group(0)]

    s: str = sub(r"[.?*]", repl, pattern)

    pattern_re: Pattern = compile(s)
    for val in text_list:
        if pattern_re.search(val) is not None:
            print(f"\tmatched: {val}")
            return True
    return False
