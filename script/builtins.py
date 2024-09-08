
def builtin_btwn(args: list) -> bool:
    """Returns True is args[0] is between args[1] and args[2] (inclusive).
    Signature: btwn(val: int, lower: int, higher: int)"""

    if len(args) != 3:
        print("!! #btwn expects 3 parameters: value, lower (inclusive), higher (inclusive)")
        return False
    return int(args[1]) <= int(args[0]) <= int(args[2])


def builtin_counter(args: list) -> int:
    """Creates or increments and returns an integer counter calls args[0], optionally starting at args[1] and
    incrementing by args[2].
    Signature: counter(c_name: str[, c_start: int[, c_step: int]])"""

    cntr_name: str = str(args[0])

    # Increment and return old counter
    if cntr_name in builtin_counter.counters:
        cntr, inc = builtin_counter.counters[cntr_name]
        builtin_counter.counters[cntr_name] = (cntr + inc, inc)
        return cntr

    # Create new counter
    start: int = args[1] if len(args) > 1 else 1
    add: int = args[2] if len(args) > 2 else 1
    builtin_counter.counters[cntr_name] = (start, add)
    return start


builtin_counter.counters = {}


def builtin_empty(args: list) -> bool:
    return bool(len(args[0]))


def builtin_eq(args: list) -> bool:
    return bool(int(args[0]) == int(args[1]))


def builtin_get(args: list):
    """Returns element at index args[1] of list args[0].
    Signature: get(lst: array, idx: int)"""

    if len(args) != 2:
        print("!! #get expects 2 parameters")
        return 0

    idx: int = int(args[1])
    if idx < 0 or idx >= len(args[0]):
        print(f"!! #get cannot access element {idx} in list with {len(args[0])} elements")
        return 0

    return args[0][idx]


def builtin_gt(args: list) -> int:
    return int(int(args[0]) > int(args[1]))


def builtin_join(args: list) -> str:
    """Joins strings in list args[0] using string args[1], if args[2] is given, it is used to join the last
    element of args[0].
    Signature: join(lst: array, join_str: str[, join_last: str])"""

    if len(args) < 2:
        print("!! #join expected at least 2 Parameters")
        return ""

    if not len(args[0]):
        return ""

    jstr: str = str(args[1])
    last_join: str = str(args[2]) if len(args) == 3 else jstr
    return str(args[0][0]) if len(args[0]) == 1 else last_join.join([jstr.join(list(args[0])[:-1]), args[0][-1]])


def builtin_mask(args: list) -> list[bool]:
    """Returns a list with length of args[0] where all indexes in list args[1] are set to True if
    args[0][args[1][i]] is evaluated to True. Every other value is set to False.
    Signature: mask(lst: array, indices: array)"""

    if len(args) != 2:
        print("!! #mask expects 2 parameters")
        return []

    return [bool(value) if i in args[1] else 0 for i, value in enumerate(args[0])]


def builtin_not(args: list) -> bool:
    return not bool(args[0])


def builtin_sum(args: list) -> int:
    return sum(args[0])


def builtin_upper(args: list) -> str:
    return str(args[0]).capitalize()
