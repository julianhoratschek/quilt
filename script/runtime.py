from .template import Template
import script.builtins
from re import Pattern, compile


class Runtime:
    """Evaluates scripts and stores all relevant data"""

    # RegEx capturing groups
    IdentifierToken: int = 1
    NumberToken: int = 2
    DQString: int = 3

    BuiltinMethodNames: list[str] = [
        "btwn", "counter", "empty", "eq", "get", "gt", "join", "mask", "not", "run", "sum", "upper", "var"]

    # Script syntax as RegEx
    ScriptRe: Pattern = compile(r"([a-zA-Z_][\w_:]+)|(\d+)|\"([^\"]+)\"|\[|\(|]|\)|!")

    class EndParam:
        """Singleton-Class representing end of parameter list, used for array- and parameter creation.
        Should only be called using its class-method get()."""

        Singleton = None

        def __init__(self):
            self.Singleton = self

        @classmethod
        def get(cls):
            return cls.Singleton if cls.Singleton else cls()

    def __init__(self):

        # Value stack for script evaluation
        self.stack: list = []

        # Setup namespaces containing all builtin method names
        self.namespaces: dict = {builtin_name: builtin_name for builtin_name in Runtime.BuiltinMethodNames}
        self.templates: list[Template] = []

    def __str__(self) -> str:
        return (f"Namespaces:\n" +
                "\n".join([f"\t{name}: {value}" for name, value in self.namespaces.items()]) +
                f"\nTemplates: {len(self.templates)}" +
                f"\nStack: {self.stack}")

    def _execute_template(self) -> str:
        """Run a template using all its registered aliases for namespaces. All namespaces used in the template
        must have the same length"""

        # Get template id from stack
        template_id: int = int(self.stack.pop()[0])
        if 0 > template_id or template_id > len(self.templates):
            print(f"!! Trying to execute template nr {template_id} with only {len(self.templates)} registered")
            return ""

        template: Template = self.templates[template_id]
        template_aliases = iter(template.alias.values())

        # Test length of each used namespace
        template_len: int = len(self.namespaces[next(template_aliases)])
        while n := next(template_aliases, None):
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
        """Run a line of script in this runtime"""

        self.stack.clear()

        # Walk backwards as the script mimics stack execution order
        for token in self.ScriptRe.finditer(line[::-1]):

            # Push Namespace value
            if identifier := token.group(self.IdentifierToken):
                identifier = identifier[::-1]
                if identifier in self.namespaces:
                    self.stack.append(self.namespaces[identifier])
                else:
                    print(f"!! Identifier <{identifier}> is not a registered namespace")

            # Push number
            elif number := token.group(self.NumberToken):
                self.stack.append(int(number[::-1]))

            # Push string content
            elif text := token.group(self.DQString):
                self.stack.append(text[::-1])

            else:
                match token.group(0)[0]:
                    # Collect array or parameter list as list and push
                    case '(' | '[':
                        # Look for EndParam
                        i: int = 0
                        for i, value in enumerate(reversed(self.stack)):
                            if isinstance(value, self.EndParam):
                                break
                        else:
                            print("!! Missing ) or ]")
                            return ""

                        result: list = self.stack[len(self.stack) - i:]
                        self.stack = self.stack[:len(self.stack) - i - 1]
                        self.stack.append(result[::-1])

                    case ')' | ']':
                        self.stack.append(self.EndParam.get())

                    # Call method
                    case '!':
                        callback_name: str = self.stack.pop()

                        match callback_name:
                            case "run":
                                self.stack.append(self._execute_template())
                            case "var":
                                self.namespaces[self.stack.pop()[0]] = 0
                            case _:
                                if callback := getattr(script.builtins, f"builtin_{callback_name}"):
                                    self.stack.append(callback(self.stack.pop()))

        return self.stack.pop()




