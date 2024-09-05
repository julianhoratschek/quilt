from script import Runtime
from xml import Parser
from word import find_file, attach_runtime, write_file

from pathlib import Path

if __name__ == "__main__":

    rt: Runtime = Runtime()
    xml: Parser = Parser(rt)

    xml.process(Path("options.xml"))

    file_path: Path = find_file(xml.options, input("Name: "))
    attach_runtime(rt, file_path)

    xml.process(Path("templates.xml"))

    write_file(rt, xml.options)

