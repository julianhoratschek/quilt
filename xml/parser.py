import re

from script import Runtime, Template
from .tag import Tag
from .entry import Entry
from util import glob

from pathlib import Path
from re import Pattern, Match, compile, finditer, search, sub


class Parser:

    # RegEx-Groups
    CloseTagGroup: int = 1
    TagNameGroup: int = 2
    OptionsGroup: int = 3
    AutoCloseTagGroup: int = 4

    def __init__(self, rt: Runtime, options: dict[str, str | list[str]] = None):
        self.runtime: Runtime = rt

        # Content of xml-file to process
        self.text: str = ""
        # Offset in xml-content
        self.pos: int = 0

        # Currently "open" tags
        self.tag_stack: list[Tag] = []
        # Last opened tag (before being pushed onto tag_stack)
        self.current_tag: Tag = Tag("templates")
        # Last match in text
        self.current_match: Match | None = None

        # List of names to build runtime namespace name (e.g. "patient", "height", "values" -> "patient:height:values")
        self.namespaces: list[str] = []

        # Last user input from <prompt> tag
        self.last_input: str = ""

        # All currently read <text> tag contents
        self.text_blocks: list[str] = []
        # All currently registered <value> tags in the last encountered <field> tag
        self.field_value_names: list[str] = []
        # All currently registered <entry> or <select> tags in the last encountered <mapping> tag
        self.entries: list[Entry] = []

        self.options: dict[str, str | list[str]] = options if options else {
            "ignore_forms": []
        }

    def __str__(self) -> str:
        return f"Tag Stack: {self.tag_stack}\nOptions: {self.options}"

    @property
    def current_namespace(self) -> str:
        return ":".join(self.namespaces)

    @property
    def parent_tag(self) -> Tag:
        return self.tag_stack[-1]

    @property
    def opening_tag(self) -> Tag:
        return self.tag_stack[-1]

    def _close_tag(self):
        match self.current_tag.name:
            case "field" | "form" | "insert" | "value":
                self.namespaces.pop()

            case "mapping":
                self._map_field_values()

            case "template":
                # Assign last read text to template
                self.runtime.templates[-1].text = self.runtime.namespaces[self.current_namespace]
                # Let namespace point to current template
                self.runtime.namespaces[self.current_namespace] = len(self.runtime.templates) - 1
                # Leave scope
                self.namespaces.pop()

            case "textblock":
                print(f"{self.current_namespace} {self.text_blocks}")
                self.runtime.namespaces[self.current_namespace] = \
                    self.parent_tag.attr("join", " ").join(self.text_blocks)

            case tag_name:
                if tag_name not in ["entry", "gender", "import", "option",
                                    "prompt", "pronoun", "select", "set", "templates", "text", "variable"]:
                    print(f"!! Unknown tag <{tag_name}>")

        self.tag_stack.pop()

    def _content(self) -> str:
        """Read text node of current tag and execute scripts in it"""

        def repl(m: Match) -> str:
            return str(self.runtime.run(m.group(1)))

        if not (content_match := search(f"(.*?)</{self.current_tag.name}>", self.text[self.pos:], re.DOTALL)):
            print(f"!! Tag {self.current_tag.name} dos not have any content")
            return ""

        # Ensure we don't omit closing tag
        self.pos += content_match.end(1)

        return sub(r"#\{([^}]+)}", repl, content_match.group(1))

    def _map_field_values(self):
        start_idx: int = int(self.opening_tag.attr("start", "0"))
        number_type: bool = self.tag_stack[-2].attr("type", "") == "numbers"
        mapped_type: bool = self.opening_tag.attr("type", "") == "mapped"

        # For all values in this field
        for ns_name in [self.current_namespace, *self.field_value_names]:
            # Map numbers
            if number_type:
                if mapped_type:
                    result: list[str] = [
                        entry.content[i] for entry, idx in zip(self.entries, self.runtime.namespaces[ns_name])
                        if not entry.skip
                           and isinstance(entry.content, list)
                           and 0 <= (i := (int(idx) - start_idx)) < len(entry.content)
                    ]

                else:
                    result: list[str] = [
                        self.entries[i].content for idx in self.runtime.namespaces[ns_name]
                        if 0 <= (i := (int(idx) - start_idx)) < len(self.entries)
                           and not self.entries[i].skip
                    ]

            # Map checks
            else:
                result: list[str] = [
                    entry.content for val, entry in zip(self.runtime.namespaces[ns_name], self.entries)
                    if bool(val)
                       and not entry.skip
                       and isinstance(entry.content, str)
                ]

            self.runtime.namespaces[ns_name] = result

    def _open_tag(self):
        match self.current_tag.name:
            case "entry":
                self.entries.append(Entry(
                    self._content(),
                    self.current_tag.attr("ignore") != ""
                ))

            case "field":
                if (field_name := self.current_tag["name"]) and self.current_tag["type"]:
                    self.field_value_names.clear()
                    self.namespaces.append(field_name)

            case "form":
                if not (form_name := self.current_tag["name"]) or form_name in self.options.get("ignore_forms", []):
                    return self._skip_tag()
                self.namespaces.append(form_name)

            case "gender":
                if not (gender_name := self.current_tag["name"]) or self.last_input != gender_name:
                    return self._skip_tag()

            case "import":
                if import_file := self.current_tag["name"]:
                    p: Parser = Parser(self.runtime, self.options)
                    p.process(Path(import_file))

            case "insert":
                if not (ns_name := self.current_tag["name"]):
                    return self._skip_tag()

                self.namespaces.append(ns_name)

                if (not (glob_pattern := self.current_tag["for"])
                        or not glob(glob_pattern, self.runtime.namespaces["diagnoses:icd10"])):
                    self.runtime.namespaces[self.current_namespace] = ""
                    self.namespaces.pop()
                    return self._skip_tag()

            case "mapping":
                self.entries.clear()
                if self.parent_tag.name != "field":
                    print("!! mapping tag must be child of field tag")
                    return self._skip_tag()

            case "option":
                if len(self.entries) == 0:
                    print("!! Option-tag must be used within mapping and select tags")

                elif not isinstance(self.entries[-1].content, list):
                    print("!! Option-tag can only be used within select tags")

                else:
                    self.entries[-1].content.append(self._content())

            case "prompt":
                self._prompt_user()

            case "pronoun":
                if ns_name := self.current_tag["name"]:
                    self.runtime.namespaces[ns_name] = self._content()

            case "select":
                self.entries.append(Entry([], self.current_tag.attr("ignore") != ""))

            case "set":
                if ((set_name := self.current_tag["name"])
                        and (set_value := self.current_tag["value"])):
                    self.options[set_name] = [
                        s.strip() for s in set_value.split(",")
                    ] if set_name == "ignore_forms" else set_value

            case "template":
                if template_name := self.current_tag["name"]:
                    self.runtime.templates.append(Template())
                    self.namespaces.append(f"template:{template_name}")

            case "text":
                if not (when_clause := self.current_tag.attr("when")) \
                        or int(self.runtime.run(when_clause)) != 0:
                    self.text_blocks.append(self._content())

            case "textblock":
                self.text_blocks.clear()

            case "value":
                if self.parent_tag.name != "field":
                    print("!! value-tag must have field-tag as parent")
                elif (value_name := self.current_tag["name"]) and (value_content := self.current_tag["content"]):
                    self.namespaces.append(value_name)
                    self.field_value_names.append(self.current_namespace)
                    self.runtime.namespaces[self.current_namespace] = self.runtime.run(value_content)

            case "variable":
                if self.parent_tag.name != "template":
                    print("!! variable-tag must have template-tag as parent")
                elif (var_name := self.current_tag["name"]) and (from_var := self.current_tag["from"]):
                    self.runtime.templates[-1].alias[var_name] = from_var

        self.tag_stack.append(self.current_tag)

    def _prompt_user(self):
        prompt: str = self._content()

        while True:
            self.last_input = input(prompt)

            # Fill in default values, if set
            if self.last_input == "%":
                self.last_input = self.current_tag.attr("default", "")

            # Don't process or save to namespace, if parent tag isn't a field
            if self.parent_tag.name != "field":
                return

            # field-tags are asserted to have type attribute
            match self.parent_tag["type"]:
                case "numbers":
                    if "," not in self.last_input and " " not in self.last_input:
                        result: list[int] = [int(i) for i in self.last_input if i.isdigit()]
                    else:
                        result: list[int] = [int(m.group(0)) for m in finditer(r"\d+", self.last_input)]

            # Form type checks (default)
                case "checks":
                    result: list[bool] = [c == "x" for c in self.last_input.lower() if c.isalpha()]

                case "text":
                    result: str = self.last_input
                    break

                case parent_type:
                    print(f"!! Unknown field type {parent_type}")
                    return

            if (cnt := self.parent_tag.attr("count")) and len(result) != int(cnt):
                print(f"!! Expected {cnt} entries, found {len(result)}")
                continue

            else:
                if (min_val := self.parent_tag.attr("min")) and len(result) < int(min_val):
                    print(f"!! Expected at least {min_val} entries, found {len(result)}")
                    continue

                if (max_val := self.parent_tag.attr("max")) and len(result) > int(max_val):
                    print(f"!! Expected at most {max_val} entries, found {len(result)}")
                    continue
            break

        self.runtime.namespaces[self.current_namespace] = result

    def _skip_tag(self):
        """Read all including closing tag. Read position is set after closing tag"""

        if self.current_tag.auto_close:
            return

        if not (m := search(f"</{self.current_tag.name}>", self.text[self.pos:])):
            print(f"!! {self.current_tag.name} tag does not have a closing tag")
            return

        self.pos += m.end()

    def process(self, file_name: Path):
        if not file_name.exists():
            print(f"!! File {file_name} does not exist")
            return

        tag_pattern: Pattern = compile(r"<(/)?([a-zA-Z_]+)\s*(.*?)?(/)?>")

        self.text = file_name.read_text("utf-8")
        self.pos = 0

        # Look for all tags
        while tag_match := tag_pattern.search(self.text[self.pos:]):
            self.current_match = tag_match
            self.current_tag = Tag(
                tag_match.group(self.TagNameGroup),
                tag_match.group(self.OptionsGroup),
                tag_match.group(self.CloseTagGroup) is not None,
                tag_match.group(self.AutoCloseTagGroup) is not None)
            self.pos += tag_match.end()

            if self.current_tag.is_closing:
                self._close_tag()
            else:
                self._open_tag()
                if self.current_tag.auto_close:
                    self._close_tag()


