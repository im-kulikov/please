"""Implements a simple Python script that rewrites a BUILD file to remove a set of targets."""

import sys
from _ast import Call, Str, PyCF_ONLY_AST

# These are templated in by Go. This is a little hacky but is an easy way of avoiding
# having to send arbitrary argument sets through Go / C function calls.
FILENAME = '__FILENAME__'
TARGETS = set(__TARGETS__)


def walk(node):
    """Replacement for ast.walk (we don't have collections in our limited environment)"""
    for child in iter_child_nodes(node):
        yield child
        for grandchild in walk(child):
            yield grandchild


with _open(FILENAME) as f:
    lines = f.readlines()
    tree = _compile(''.join(lines), FILENAME, 'exec', PyCF_ONLY_AST)

for node in walk(tree):
    if isinstance(node, Call) and any(k for k in node.keywords if k.arg == 'name'
                                      and isinstance(k.value, Str) and k.value.s in TARGETS):
        max_lineno = max(getattr(n, 'lineno', node.lineno - 1) for n in walk(node))
        for i in range(node.lineno - 1, max_lineno):
            lines[i] = None  # Leave a sentinel so we don't mess up further line numbers.
        # This is kinda awkward, ast doesn't keep the actual end of the function call
        # anywhere, so we have to keep searching forth until we find an ending parenthesis.
        for i in range(max_lineno, len(lines)):
            if lines[i].startswith(')'):
                lines[i] = None
                # Strip a following blank line too
                if i < len(lines) - 1 and not lines[i + 1].strip():
                    lines[i + 1] = None
                break
            lines[i] = None
        else:
            raise Exception("Didn't find end of function beginning on line %d" % node.lineno)

with _open(FILENAME, 'w') as f:
    for line in lines:
        if line is not None:
            f.write(line)
