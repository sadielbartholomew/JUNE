---
layout: default
title: Code structure
nav_order: 4
has_children: true
---

The code follows the guidelines described [here](https://yt-project.org/doc/developing/developing.html#code-style-guide).

Additionally, all classes should be declared in separate files with the filenamen equal to the class name. All tests should go into the tests/ folder, and follow the nomenclature ``test_*`` both for the file names and the functions inside, so they can be easily catched by ``pytest``. 

Given that the code will very likely be ported to C/C++, all attributes of the class should be considered to be private, that is, if you want to get the ``age`` attribute of the ``Person`` class, then implement 

```
    def get_age(self):
        return self.age
```
