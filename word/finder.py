from pathlib import Path
from re import Pattern, compile
from operator import itemgetter
from datetime import date, datetime


def pick_file(paths: list[Path]) -> Path:
    file_pattern: Pattern = compile(r"([.\w\- ]+),\s*([.\w\- ]+)\s*(\d{8})")
    option_list: list[tuple[str, str, date, Path]] = [
        (m.group(1), m.group(2), datetime.strptime(m.group(3), "%d%m%Y").date(), p)
        for p in paths if (m := file_pattern.search(p.name))
    ]

    # Sort by date, last name, first name
    option_list.sort(key=itemgetter(2, 0, 1))

    while True:
        for i, opt in enumerate(option_list, 1):
            print(f"\t[{i}] {opt[2].strftime('%d.%m.%Y')} {opt[0]}, {opt[1]}")

        if not (user_input := input(": ")).isdecimal():
            print(f"Auswahl muss zwischen 1 und {len(option_list)} liegen")
            continue

        return option_list[int(user_input) - 1][3]


def find_file(options: dict[str, str], patient_name: str) -> Path:
    search_dir: Path = Path(options["search_dir"])
    matches: list[Path] = [path for path in search_dir.glob("*.docx") if patient_name.lower() in path.name.lower()]
    print(matches)
    match len(matches):
        case 0:
            return Path()
        case 1:
            return matches[0]
        case _:
            return pick_file(matches)

