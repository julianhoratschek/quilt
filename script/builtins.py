

def builtin_empty(args: list) -> bool:
    return bool(len(args[0]))


def builtin_get(args: list):
    return args[0][args[1]]


def builtin_gt(args: list) -> int:
    return int(args[0] > args[1])


def builtin_join(args: list) -> str:
    last_join: str = str(args[2]) if len(args) == 3 else str(args[1])
    return str(args[0][0]) if len(args) == 1 else last_join.join([str(args[1]).join(list(args[0])[:-1]), args[0][-1]])


def builtin_mask(args: list) -> list[bool]:
    return [bool(value) if i in args[1] else 0 for i, value in enumerate(args[0])]


def builtin_not(args: list) -> bool:
    return not bool(args[0])


def builtin_sum(args: list) -> int:
    return sum(args[0])

