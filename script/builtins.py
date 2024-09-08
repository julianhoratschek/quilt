
def builtin_btwn(args: list) -> bool:
    """btwn(val: int, lower: int, higher: int)"""
    if len(args) != 3:
        print("!! #btwn expects 3 parameters: value, lower (inclusive), higher (inclusive)")
        return False
    return int(args[1]) <= int(args[0]) <= int(args[2])


counters: dict[str, tuple[int, int]] = {}


def builtin_counter(args: list) -> int:
    """counter(c_name: str[, c_start: int[, c_step: int]])"""
    cntr_name = str(args[0])
    if cntr_name in counters:
        cntr, inc = counters[cntr_name]
        counters[cntr_name] = (cntr + inc, inc)
        return cntr

    start: int = args[1] if len(args) > 1 else 0
    add: int = args[2] if len(args) > 2 else 1
    counters[cntr_name] = (start, add)
    return start


def builtin_empty(args: list) -> bool:
    return bool(len(args[0]))


def builtin_eq(args: list) -> bool:
    return bool(int(args[0]) == int(args[1]))


def builtin_get(args: list):
    return args[0][args[1]]


def builtin_gt(args: list) -> int:
    return int(args[0] > args[1])


def builtin_join(args: list) -> str:
    if not len(args[0]):
        return ""
    last_join: str = str(args[2]) if len(args) == 3 else str(args[1])
    return str(args[0][0]) if len(args[0]) == 1 else last_join.join([str(args[1]).join(list(args[0])[:-1]), args[0][-1]])


def builtin_mask(args: list) -> list[bool]:
    return [bool(value) if i in args[1] else 0 for i, value in enumerate(args[0])]


def builtin_not(args: list) -> bool:
    return not bool(args[0])


def builtin_sum(args: list) -> int:
    return sum(args[0])


def builtin_upper(args: list) -> str:
    return str(args[0]).capitalize()
