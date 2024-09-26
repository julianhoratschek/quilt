from script import Runtime
from util import remove_zip_file

from pathlib import Path
from re import Pattern, Match, sub, compile
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import copy


def add_content(runtime: Runtime, options: dict[str, str | list[str]]) -> bool:
    def repl(m: Match) -> str:
        return str(runtime.run(m.group(1)))

    def cleanup(_m: Match) -> str:
        return ""

    path_name: Path = Path(options["output_dir"]) / Path(
        f"A-{runtime.namespaces['patient:last_name']}, "
        f"{runtime.namespaces['patient:first_name']} "
        f"{runtime.namespaces['patient:admission']}.docx")
    insert_pattern: Pattern = compile(
        r'<w:bookmarkStart w:id="[\d_]+" w:name="skip\[([^]]+)]"/>')
    cleanup_pattern: Pattern = compile(r'<w:bookmarkEnd w:id="[\d_]+"/>')

    if not path_name.exists():
        print(f"!! File {path_name} does not seem to exist, nothing was added")
        return False

    with ZipFile(path_name, "r", compression=ZIP_DEFLATED) as zip_archive:
        text: str = insert_pattern.sub(
            repl, cleanup_pattern.sub(cleanup, zip_archive.read("word/document.xml").decode("utf-8")))

    with ZipFile(path_name, "a", compression=ZIP_DEFLATED) as zip_archive:
        remove_zip_file(zip_archive, "word/document.xml")
        zip_archive.writestr(
            "word/document.xml",
            text.encode("utf-8"),
            compress_type=ZIP_DEFLATED)

    return True


def write_file(runtime: Runtime, options: dict[str, str | list[str]]):
    def repl(m: Match) -> str:
        return str(runtime.run(m.group(1)))

    document_content: str = sub(r"#\{([^}]+)}", repl, Path(options["docx_document"]).read_text("utf-8"))
    header_content: str = sub(r"#\{([^}]+)}", repl, Path(options["docx_header"]).read_text("utf-8"))
    output_dir: Path = Path(options["output_dir"])

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    file_name: Path = copy(
        options["docx_template"],
        output_dir / Path(f"A-{runtime.namespaces['patient:last_name']}, "
                          f"{runtime.namespaces['patient:first_name']} "
                          f"{runtime.namespaces['patient:admission']}.docx"))

    with ZipFile(file_name, "a", compression=ZIP_DEFLATED) as output_file:
        output_file.writestr(
            "word/document.xml",
            document_content.encode("utf-8"),
            compress_type=ZIP_DEFLATED)
        output_file.writestr("word/header1.xml",
                             header_content.encode("utf-8"),
                             compress_type=ZIP_DEFLATED)


