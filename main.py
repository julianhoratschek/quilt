from script.runtime import Runtime
from xml.parser import Parser
from word.finder import find_file
from word.file_reader import attach_runtime
from word.file_writer import write_file

from pathlib import Path

if __name__ == "__main__":

    rt: Runtime = Runtime()
    xml: Parser = Parser(rt)
    xml.process(Path("options.xml"))
    file_path: Path = find_file(xml.options, input("Name: "))
    attach_runtime(rt, file_path)
    xml.process(Path("templates.xml"))

    write_file(rt, xml.options)


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx