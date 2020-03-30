---
layout: default
title: Code structure
nav_order: 4
has_children: true
---

The code follows the guidelines described [here](https://yt-project.org/doc/developing/developing.html#code-style-guide).

Additionally, all classes should be declared in separate files with the filenamen equal to the class name. All tests should go into the tests/ folder, and follow the nomenclature ``test_*`` both for the file names and the functions inside, so they can be easily catched by ``pytest``. 
