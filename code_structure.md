---
layout: default
title: Code structure
nav_order: 2
has_children: true
---

The code follows the guidelines described [here](https://yt-project.org/doc/developing/developing.html#code-style-guide).

Additionally, all classes should be declared in separate files with the filename equal to the class name. All  *automated* tests should go into the tests/ folder, and follow the nomenclature ``test_*`` both for the file names and the functions inside, so they can be easily catched by ``pytest``.  Those tests that consist of plots, should go to the plot_tests/ folder.

Given that the code will very likely be ported to C/C++, all attributes of the class should be considered to be private, that is, if you want to get the ``age`` attribute of the ``Person`` class, then implement 

```
    def get_age(self):
        return self.age
```



The class diagram can be found at https://drive.google.com/file/d/1YMUAePtUvx1xLVObjnz1n5IkDfJOkmD8/view

