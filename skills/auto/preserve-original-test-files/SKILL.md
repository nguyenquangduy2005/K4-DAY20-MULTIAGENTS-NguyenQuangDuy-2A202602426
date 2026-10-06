---
name: preserve-original-test-files
description: use this skill when modifying code to ensure original test files remain unchanged and only new test files are added
---
Before editing or adding tests, list the test directory contents to confirm existing test files.
Never modify existing test files; instead, create new test files for additional tests.
Verify that your changes do not alter any existing test files by comparing file hashes or timestamps.
Run checks to confirm no original test files were changed before submitting.