import re
from re import Match, Pattern, compile, sub


def glob(pattern: str, text_list: list[str], ignore_case: bool = False) -> bool:

    def repl(m: Match) -> str:
        return glob.lookup[m.group(0)]

    flags: int = re.IGNORECASE if ignore_case else 0
    pattern_re: Pattern = compile(sub(r"[.?*]", repl, pattern), flags)
    for val in text_list:
        if pattern_re.search(val) is not None:
            return True
    return False


glob.lookup = {".": r"\.", "?": ".", "*": ".*?"}

