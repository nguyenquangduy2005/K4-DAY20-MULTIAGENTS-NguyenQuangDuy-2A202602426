---
name: normalize-and-validate-data-before-analysis
description: use this skill when processing input data files to ensure consistent formatting, deduplication, and correct data types before analysis
---
Read the input data fully and inspect for inconsistencies such as extra spaces, case differences, or formatting variations.
Normalize categorical fields (e.g., region names) by trimming whitespace and applying consistent casing.
Parse dates into a uniform timezone-aware datetime format (preferably UTC).
Convert monetary values to a consistent unit and type (e.g., integer cents) and handle special missing or invalid values explicitly.
Remove duplicate records based on unique identifiers, keeping the first or most relevant occurrence.
Validate the cleaned data against expected schema and rules before performing calculations or generating outputs.