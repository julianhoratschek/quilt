from script.runtime import Runtime
from script.template import Template
from .tag import Tag
from .entry import Entry
from util import glob

from pathlib import Path
from re import Match, finditer, search, sub


class Parser:
    CloseTagGroup: int = 1
    TagNameGroup: int = 2
    OptionsGroup: int = 3
    AutoCloseTagGroup: int = 4

    class EmptyInsert:
        Singleton = None

        def __init__(self):
            self.Singleton = self

        @classmethod
        def get(cls):
            return cls.Singleton if cls.Singleton else cls()

    def __init__(self, rt: Runtime, options: dict[str, str | list[str]] = None):
        self.runtime: Runtime = rt
        self.text: str = ""
        self.pos: int = 0

        self.tag_stack: list[Tag] = []
        self.current_tag: Tag = Tag("templates")
        self.current_match: Match | None = None

        self.namespaces: list[str] = []
        self.last_input: str = ""

        self.text_blocks: list[str] = []
        self.field_value_names: list[str] = []
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

    def _assert_has_name(self) -> bool:
        if "name" not in self.current_tag.options:
            print(f"!! {self.current_tag.name}-tag must have name attribute")
            return False
        return True

    def _close_tag(self):
        match self.current_tag.name:
            case "field":
                self.namespaces.pop()

            case "form":
                self.namespaces.pop()

            case "insert":
                self.namespaces.pop()

            case "mapping":
                self._map_field_values()

            case "template":
                self.runtime.templates[-1].text = self.runtime.namespaces[self.current_namespace]
                self.runtime.namespaces[self.current_namespace] = len(self.runtime.templates) - 1
                self.namespaces.pop()

            case "textblock":
                join_str: str = self.parent_tag.options.get("join", " ")
                self.runtime.namespaces[self.current_namespace] = join_str.join(self.text_blocks)

            case "value":
                self.namespaces.pop()

            case tag_name:
                if tag_name not in ["entry", "gender", "import", "insert", "option",
                                    "prompt", "pronoun", "select", "set", "templates", "text", "variable"]:
                    print(f"!! Unknown tag <{tag_name}>")

        self.tag_stack.pop()

    def _content(self):
        def repl(m: Match) -> str:
            return str(self.runtime.run(m.group(1)))

        if not (content_match := search(f"(.*?)</{self.current_tag.name}>", self.text[self.pos:])):
            print(f"!! Tag {self.current_tag.name} dos not have any content")
            return ""

        self.pos += content_match.end(1)

        return sub(r"#\{([^}]+)}", repl, content_match.group(1))

    def _map_field_values(self):
        start_idx: int = int(self.opening_tag.options.get("start", "0"))
        number_type: bool = self.tag_stack[-2].options.get("type", "") == "numbers"
        mapped_type: bool = self.opening_tag.options.get("type", "") == "mapped"

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
                    "ignore" in self.current_tag.options
                ))

            case "field":
                self.field_value_names.clear()
                self.namespaces.append(self.current_tag.options.get("name", "global"))

            case "form":
                form_name: str = self.current_tag.options.get("name", "global")
                if form_name in self.options["ignore_forms"]:
                    return self._skip_tag()
                self.namespaces.append(form_name)

            case "gender":
                if not self._assert_has_name() or self.last_input != self.current_tag.options["name"]:
                    return self._skip_tag()

            case "import":
                if self._assert_has_name():
                    p: Parser = Parser(self.runtime, self.options)
                    p.process(Path(self.current_tag.options["name"]))
                    # self.options |= p.options

            case "insert":
                if "for" not in self.current_tag.options or not glob(
                        self.current_tag.options["for"],
                        self.runtime.namespaces["diagnoses:icd10"]):
                    self.runtime.namespaces[self.current_tag.options.get("name", "local")] = ""
                    return self._skip_tag()

                self.namespaces.append(self.current_tag.options.get("name", "local"))

            case "mapping":
                self.entries.clear()
                if self.parent_tag.name != "field":
                    print("!! mapping tag must be child of field tag")

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
                if self._assert_has_name():
                    self.runtime.namespaces[self.current_tag.options["name"]] = self._content()

            case "select":
                self.entries.append(Entry([], "ignore" in self.current_tag.options))

            case "set":
                if "name" not in self.current_tag.options or "value" not in self.current_tag.options:
                    print("!! set-tag must contain name and value attributes")
                elif self.current_tag.options["name"] == "ignore_forms":
                    self.options["ignore_forms"] = [
                        s.strip() for s in self.current_tag.options["value"].split(",")
                    ]
                else:
                    self.options[self.current_tag.options["name"]] = self.current_tag.options["value"]

            case "template":
                self.runtime.templates.append(Template())
                self.namespaces.append(f"template:{self.current_tag.options.get('name', 'local')}")

            case "text":
                if "when" not in self.current_tag.options \
                        or int(self.runtime.run(self.current_tag.options["when"])) != 0:
                    self.text_blocks.append(self._content())

            case "textblock":
                self.text_blocks.clear()

            case "value":
                self.namespaces.append(self.current_tag.options.get("name", "local"))
                self.field_value_names.append(self.current_namespace)
                self.runtime.namespaces[self.current_namespace] = self.runtime.run(
                    self.current_tag.options.get("content", "0"))

            case "variable":
                if self.parent_tag.name != "template":
                    print("!! variable-tag must have template-tag as parent")
                elif "name" not in self.current_tag.options or "from" not in self.current_tag.options:
                    print("!! variable-tag must have name and from attributes")
                else:
                    self.runtime.templates[-1].alias[self.current_tag.options["name"]] = \
                        self.current_tag.options["from"]

        self.tag_stack.append(self.current_tag)

    def _prompt_user(self):
        prompt: str = self._content()

        while True:
            self.last_input = input(prompt)

            if self.last_input == "%":
                self.last_input = self.current_tag.options.get("default", "")

            if self.parent_tag.name != "field":
                return

            # Form type numbers
            if "type" not in self.parent_tag.options:
                print("!! field tags require type attribute")
                return

            match self.parent_tag.options["type"]:
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

            if "count" in self.parent_tag.options and len(result) != int(self.parent_tag.options["count"]):
                print(f"!! Expected {self.parent_tag.options['count']} entries, found {len(result)}")
                continue

            else:
                if "min" in self.parent_tag.options and len(result) < int(self.parent_tag.options["min"]):
                    print(f"!! Expected at least {self.parent_tag.options['min']} entries, found {len(result)}")
                    continue

                if "max" in self.parent_tag.options and len(result) > int(self.parent_tag.options["max"]):
                    print(f"!! Expected at most {self.parent_tag.options['max']} entries, found {len(result)}")
                    continue
            break

        self.runtime.namespaces[self.current_namespace] = result

    def _skip_tag(self):
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

        self.text = file_name.read_text("utf-8")
        self.pos = 0

        while tag_match := search(r"<(/)?([a-zA-Z_]+)\s*(.*?)?(/)?>", self.text[self.pos:]):
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


