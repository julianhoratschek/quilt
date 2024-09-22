from script import Runtime
from xml import Parser
from word import find_file, attach_runtime, write_file, add_content, parse_medication

from pathlib import Path
from argparse import ArgumentParser, Namespace
from enum import Enum


class ProgramMode(Enum):
    Create = 0
    Add = 1
    Remove = 2


if __name__ == "__main__":

    parser: ArgumentParser = ArgumentParser(
        prog="brief",
        description="A short program to write medical letters",
    )

    parser.add_argument("-a", "--add",
                        action="extend",
                        nargs="+",
                        type=str,
                        dest="add_list",
                        help="add diagnoses with corresponding textblocks to an existing letter")
    # TODO implement
    parser.add_argument("-d", "--delete",
                        action="extend",
                        nargs="+",
                        type=str,
                        dest="remove_list",
                        help="remove diagnoses and textblocks from an existing letter")

    args: Namespace = parser.parse_args()
    program_mode: ProgramMode = ProgramMode.Add if args.add_list else ProgramMode.Create

    rt: Runtime = Runtime()
    xml: Parser = Parser(rt)

    # Read options from file
    xml.process(Path("options.xml"))

    # Get Patient file by user input
    file_path: Path = find_file(xml.options, input("Name: "))

    # Read file and prepare runtime
    attach_runtime(rt, file_path)

    # TODO put into write_file?
    generated_path: Path = (Path(xml.options["output_dir"]) /
                            Path(f"A-{rt.namespaces['patient:last_name']}, "
                                 f"{rt.namespaces['patient:first_name']} "
                                 f"{rt.namespaces['patient:admission']}.docx"))

    # Setup mode
    match program_mode:

        # Don't overwrite existing files silently
        case ProgramMode.Create:
            if generated_path.exists() \
            and input(f"A generated File {file_path} already exists. Overwrite it? y(es), n(o): ").lower()[0] != 'y':
                print("!! File generation aborted")
                exit(0)

        # Add new icd-codes into runtime
        case ProgramMode.Add:
            xml.options["ignore_forms"].extend([
                "gdb", "midas_score", "treatments", "afflictions",
                "whodas_categories", "whodas_score", "bdi", "chronic_pain"])
            rt.namespaces["diagnoses:icd10"].extend(args.add_list)
            rt.namespaces["diagnoses:names"].extend(["[Diagnose einfügen]" for _ in args.add_list])

        # TODO implement
        case ProgramMode.Remove:
            print("!! Not implemented yet")

        case _:
            print("!! Unknown program mode")
            exit(0)

    # Read all inserts/forms
    xml.process(Path("templates.xml"))

    # Run mode
    match program_mode:
        case ProgramMode.Create:
            # Process runtime data and write to output
            write_file(rt, xml.options)

        case ProgramMode.Add:
            add_content(rt, xml.options)
            print("Text blocks were added.")
            print("!! IMPORTANT: Please add the new diagnoses or medications manually !!")

        case ProgramMode.Remove:
            print("!! Remove is not implemented yet")

        case _:
            print("!! Unknown program mode")


