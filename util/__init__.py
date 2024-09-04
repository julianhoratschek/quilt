from re import Match, Pattern, compile, search, sub


def glob(pattern: str, text_list: list[str]) -> bool:
    def repl(m: Match) -> str:
        return {".": r"\.", "?": ".{1}", "*": ".*?"}[m.group(0)]

    pattern_re: Pattern = compile(sub(r"[.?*]", repl, pattern))
    for val in text_list:
        if pattern_re.search(val) is not None:
            return True
    return False
