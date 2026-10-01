"""
Architectural integrity test.
Guarantees that production modules never import test doubles, mocks, or the test suite.
"""

import ast
from pathlib import Path


def test_no_mock_or_test_imports_in_production():
    production_roots = [
        Path("backend/app"),
        Path("agents"),
        Path("automation"),
        Path("multimodal"),
        Path("tools"),
    ]

    violations = []

    for root in production_roots:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            try:
                tree = ast.parse(content, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.lower()
                        if "test" in name.split(".") or "mock" in name.split("."):
                            violations.append(f"{py_file}:{node.lineno} imports '{alias.name}'")
                elif isinstance(node, ast.ImportFrom):
                    mod = (node.module or "").lower()
                    if "test" in mod.split(".") or "mock" in mod.split("."):
                        violations.append(f"{py_file}:{node.lineno} imports from '{node.module}'")
                    for alias in node.names:
                        name = alias.name.lower()
                        if "mock" in name:
                            violations.append(f"{py_file}:{node.lineno} imports symbol '{alias.name}'")

    assert not violations, "Production code imports mocks or test code:\n" + "\n".join(violations)
