# Technical Documentation Index

This index is designed to be readable as plain text.
It avoids wide Markdown tables.

READING ORDER:

1. Product Owner Guide
   File:
     docs/technical/product_owner_guide.md
   Purpose:
     Explains what the system does today, what is reliable, what is
     experimental, and how to read the docs.

2. Pipeline Map
   File:
     docs/technical/pipeline_map.md
   Purpose:
     Shows the stage-by-stage flow from environment checks to timeline
     validation.

3. Function Inventory
   File:
     docs/technical/function_inventory.md
   Purpose:
     Lists important functions with FILE and LINE references generated
     from source code.

4. Friction Casebook
   File:
     docs/friction/friction_casebook.md
   Purpose:
     Explains important problems, root causes, resolutions, and reusable
     rules.

5. Stage Technical Docs
   Folder:
     docs/technical/stage_*.md
   Purpose:
     Explains what each stage does, what it reads, what it writes, and
     where to inspect code.

6. Lab Notebook
   Folder:
     docs/lab-notebook/
   Purpose:
     Records execution results, reports, warnings, errors, and friction
     history.

HOW TO NAVIGATE:

- Start with the Product Owner Guide if you want the plain-English view.
- Use the Pipeline Map to understand stage order.
- Use the Function Inventory when you need to locate code.
- Use the Friction Casebook when something failed or changed direction.
- Use the Lab Notebook to see what happened in the latest runs.
