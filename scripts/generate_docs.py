"""
OmniAgent AI — Master Documentation Compiler
Compiles all 95 sections from doc_modules into a single source-of-truth file:
md/OMNIAGENT_AI_COMPLETE_DOCUMENTATION.md
"""

import os
import sys

from doc_modules.header_toc import get_header_and_toc
from doc_modules.part1 import get_part1
from doc_modules.part2 import get_part2
from doc_modules.part3 import get_part3
from doc_modules.part4 import get_part4

def main():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "md")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "OMNIAGENT_AI_COMPLETE_DOCUMENTATION.md")

    print(f"Compiling complete documentation into: {target_file}")

    content_parts = [
        get_header_and_toc(),
        get_part1(),
        get_part2(),
        get_part3(),
        get_part4()
    ]

    full_documentation = "\n\n".join(content_parts).strip() + "\n"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(full_documentation)

    file_size_bytes = os.path.getsize(target_file)
    total_lines = full_documentation.count("\n") + 1

    print(f"Documentation compiled successfully!")
    print(f"File: {target_file}")
    print(f"Size: {file_size_bytes:,} bytes")
    print(f"Lines: {total_lines:,}")

if __name__ == "__main__":
    main()
