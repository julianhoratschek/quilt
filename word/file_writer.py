from script import Runtime
from util import remove_zip_file

from pathlib import Path
from re import Pattern, Match, sub, compile, search
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import copy


def add_content(output_file_path: Path, runtime: Runtime, options: dict[str, str | list[str]]) -> bool:
    def cleanup(_m: Match) -> str:
        nonlocal cleanup_ids
        return "" if str(_m.group(1)) in cleanup_ids else _m.group(0)

    new_text: str = ""
    last_pos: int = 0
    cleanup_ids: list[str] = []

    #path_name: Path = Path(options["output_dir"]) / Path(
    #    f"A-{runtime.namespaces['patient:last_name']}, "
    #    f"{runtime.namespaces['patient:first_name']} "
    #    f"{runtime.namespaces['patient:admission']}.docx")

    insert_pattern: Pattern = compile(
        r'<w:bookmarkStart w:id="([\d_]+)" w:name="skip\[([^]]+)]"/>')
    cleanup_pattern: Pattern = compile(r'<w:bookmarkEnd w:id="([\d_]+)"/>')

    # Make sure we are working on an existing file
    if not output_file_path.exists():
        print(f"!! File {output_file_path} does not seem to exist, nothing was added")
        return False

    # Load old file content
    with ZipFile(output_file_path, "r", compression=ZIP_DEFLATED) as zip_archive:
        old_text: str = zip_archive.read("word/document.xml").decode("utf-8")

    # Find all bookmarks in the old content
    for m in insert_pattern.finditer(old_text):

        # Get new content, strip due to formatting
        insert_text: str = str(runtime.run(m.group(2))).strip()

        # Kind of inserted content defines backtracking, as word will put each bookmark into a following <w:p> element
        match insert_text[0:5]:
            # For paragraphs: Track back to before the current paragraph
            case "<w:p ":
                tag_name: str = "p "

            # For runs: insert as is at current position
            case "<w:r ":
                new_text += old_text[last_pos:m.start()]
                new_text += insert_text
                cleanup_ids.append(m.group(1))
                last_pos = m.end()
                continue

            # For Table rows: track back to last table row. FIXME: Will not work if first table row is to be inserted
            case "<w:tr":
                tag_name: str = "tr "

            # For tables: Track back to last table
            case "<w:tb":
                tag_name: str = "tbl>"

            case _:
                continue

        # Backtracking
        pos: int = old_text.rfind(f"<w:{tag_name}", last_pos, m.start())

        # If nothing was found, try to recover by finding the last paragraph
        if pos < 0 and (tag_name == "p" or (pos := old_text.rfind("<w:p ", last_pos, m.start()) == -1)):
            print("!!!! Insert not found")
            continue

        # Insert insert before current paragraph
        new_text += old_text[last_pos:pos]
        new_text += insert_text
        new_text += old_text[pos:m.start()]

        cleanup_ids.append(m.group(1))
        last_pos = m.end()

    new_text += old_text[last_pos:]

    # Remove old document.xml file and write changes
    with ZipFile(output_file_path, "a", compression=ZIP_DEFLATED) as zip_archive:
        remove_zip_file(zip_archive, "word/document.xml")
        zip_archive.writestr(
            "word/document.xml",
            cleanup_pattern.sub(cleanup, new_text).encode("utf-8"),
            compress_type=ZIP_DEFLATED)

    return True


def write_file(output_file_path: Path, runtime: Runtime, options: dict[str, str | list[str]]):
    def repl(m: Match) -> str:
        return str(runtime.run(m.group(1)))

    document_content: str = sub(r"#\{([^}]+)}", repl, Path(options["docx_document"]).read_text("utf-8"))
    header_content: str = sub(r"#\{([^}]+)}", repl, Path(options["docx_header"]).read_text("utf-8"))
    output_dir: Path = Path(options["output_dir"])

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    file_name: Path = copy(
        options["docx_template"],
        output_file_path)
        #output_dir / Path(f"A-{runtime.namespaces['patient:last_name']}, "
        #                  f"{runtime.namespaces['patient:first_name']} "
        #                  f"{runtime.namespaces['patient:admission']}.docx"))

    with ZipFile(file_name, "a", compression=ZIP_DEFLATED) as output_file:
        output_file.writestr(
            "word/document.xml",
            document_content.encode("utf-8"),
            compress_type=ZIP_DEFLATED)
        output_file.writestr("word/header1.xml",
                             header_content.encode("utf-8"),
                             compress_type=ZIP_DEFLATED)


