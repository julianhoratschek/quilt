from script import Runtime

from pathlib import Path
from re import Match, sub
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import copy


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
        output_dir /
        Path(f"A-{runtime.namespaces['patient:last_name']}, "
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


