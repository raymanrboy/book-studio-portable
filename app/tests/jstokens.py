"""A small JavaScript tokenizer for tests/test_scripts.py: the identifiers a piece of code refers to (not inside
strings, comments or template text; `${…}` inside templates is code; `a.b` — b is a property, not a reference;
`...a` — a is). Not a parser: enough to tell which names a script uses."""
import re

ID_START = re.compile(r"[A-Za-z_$]")
ID_CHAR = re.compile(r"[\w$]")
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {""}
KEYWORDS_BEFORE_REGEX = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "yield",
                         "await"}


def tokens(src):
    """(kind, text, prev_significant_char) for identifiers; strings and comments skipped."""
    out = []
    i, n = 0, len(src)
    prev = ""        # the last significant character outside strings/comments
    prev_word = ""
    stack = []       # template nesting: brace depth at which a ${ } closes
    depth = 0
    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "'\"":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            i = j + 1
            prev, prev_word = "s", ""
            continue
        if c == "`" or (c == "}" and stack and stack[-1] == depth):
            if c == "}":
                stack.pop()
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "`":
                    j += 1
                    break
                if src.startswith("${", j):
                    stack.append(depth)
                    j += 2
                    break
                j += 1
            else:
                j = n
            i = j
            prev, prev_word = "s", ""
            continue
        if c == "/" and (prev in REGEX_BEFORE or prev_word in KEYWORDS_BEFORE_REGEX):
            j = i + 1
            in_class = False
            while j < n and (src[j] != "/" or in_class):
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "\n":
                    break
                j += 1
            j += 1
            while j < n and ID_CHAR.match(src[j]):
                j += 1
            i = j
            prev, prev_word = "r", ""
            continue
        if ID_START.match(c):
            j = i + 1
            while j < n and ID_CHAR.match(src[j]):
                j += 1
            word = src[i:j]
            out.append((word, prev, i, j))
            prev, prev_word = "a", word
            i = j
            continue
        if c.isdigit():
            j = i + 1
            while j < n and (ID_CHAR.match(src[j]) or src[j] == "."):
                j += 1
            i = j
            prev, prev_word = "0", ""
            continue
        if src.startswith("...", i):  # a spread: what follows is a reference, not a property
            prev, prev_word = ",", ""
            i += 3
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        prev, prev_word = c, ""
        i += 1
    return out


def refs(src):
    """Identifiers used as references (not after a dot)."""
    return {w for w, p, *_ in tokens(src) if p != "."}
