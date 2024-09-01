from .template import Template
import script.builtins
from re import Pattern, compile


class Runtime:
    IdentifierToken: int = 1
    NumberToken: int = 2
    DQString: int = 3

    ScriptRe: Pattern = compile(r"([a-zA-Z_][\w_]+)|(\d+)|\"([^\"]+)\"|\[|\(|]|\)|!")

    class EndParam:
        Singleton = None

        def __init__(self):
            self.Singleton = self

        @classmethod
        def get(cls):
            return cls.Singleton if cls.Singleton else cls()

    def __init__(self):
        self.stack: list = []
        self.namespaces: dict = {
            "ytpme": "empty",
            "teg": "get",
            "tg": "gt",
            "nioj": "join",
            "ksam": "mask",
            "ton": "not",
            "mus": "sum"
        }
        self.templates: list[Template] = []

    def __str__(self) -> str:
        return (f"Namespaces:\n" +
                "\n".join([f"\t{name}: {value}" for name, value in self.namespaces.items()]) +
                f"\nTemplates: {len(self.templates)}" +
                f"\nStack: {self.stack}")

    def _execute_template(self) -> str:
        template_id: int = self.stack.pop()
        if 0 > template_id > len(self.templates):
            print(f"!! Trying to execute template nr {template_id} with only {len(self.templates)} registered")
            return ""

        template: Template = self.templates[template_id]
        template_aliases = iter(template.alias.values())
        template_len: int = len(self.namespaces[next(template_aliases)])

        while n := next(template_aliases):
            if len(self.namespaces[n]) != template_len:
                print(f"!! Template values ({','.join(iter(template.alias.values()))}) "
                      f"don't all have size {template_len}")
                return ""

        return "".join([
            template.text.format(**{
                alias: self.namespaces[ns_name][i] for alias, ns_name in template.alias.items()
            }) for i in range(template_len)
        ])

    def run(self, line: str):
        self.stack.clear()

        for token in self.ScriptRe.finditer(line[::-1]):
            print(token.group(0))

            if identifier := token.group(self.IdentifierToken):
                if identifier in self.namespaces:
                    self.stack.append(self.namespaces[identifier])
                else:
                    print(f"!! Identifier <{identifier[::-1]}> is not a registered namespace")

            elif number := token.group(self.NumberToken):
                self.stack.append(int(number[::-1]))

            elif text := token.group(self.DQString):
                self.stack.append(text[::-1])

            else:
                match token.group(0)[0]:
                    case '(' | '[':
                        for i, value in enumerate(reversed(self.stack)):
                            if isinstance(value, self.EndParam):
                                break
                        result: list = self.stack[len(self.stack) - i:]
                        self.stack = self.stack[:len(self.stack) - i - 1]
                        self.stack.append(result)

                    case ')' | ']':
                        self.stack.append(self.EndParam.get())

                    case '!':
                        if (callback_name := self.stack.pop()) == "run":
                            self.stack.append(self._execute_template())
                        elif callback := getattr(script.builtins, f"builtin_{callback_name}"):
                            self.stack.append(callback(self.stack.pop()))

        return self.stack.pop()




