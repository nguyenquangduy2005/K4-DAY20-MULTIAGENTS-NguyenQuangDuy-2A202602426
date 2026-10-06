---
name: enforce-type-annotations-on-public-functions
description: use this skill when writing or refactoring code to ensure all public functions have complete type annotations
---
Identify all public functions (names not starting with '_') in the package.
For each public function, add type annotations for all parameters and the return value.
Use consistent and clear type hints, importing necessary types from typing if needed.
Run static type checkers or linters to verify that all public functions have proper annotations.
Fix any missing or incomplete annotations before finalizing the code.