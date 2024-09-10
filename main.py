from script import Runtime
from xml import Parser
from word import find_file, attach_runtime, write_file

from pathlib import Path

if __name__ == "__main__":

    rt: Runtime = Runtime()
    xml: Parser = Parser(rt)

    # Read options from file
    xml.process(Path("options.xml"))

    # Get Patient file by user input
    file_path: Path = find_file(xml.options, input("Name: "))

    # Read file and prepare runtime
    attach_runtime(rt, file_path)

    # Read all inserts/forms
    xml.process(Path("templates.xml"))

    # Process runtime data and write to output
    write_file(rt, xml.options)

