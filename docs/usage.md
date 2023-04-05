# Usage

To use this template, simply make a copy of the files and modify the project
name wherever needed:

* Edit file `pyproject.toml`
* Edit the file `CMakeLists.txt`
* Rename the directory `src/dtcc_template` --> `src/package_name`

Python code should go into the directory

    src/package_name/

C++ header files should go into directory

    src/include/

Python bindings for the C++ code should go into the file

    src/cpp/bindings.cpp

Python scripts should  go into the directory

    src/package_name/

Note that scripts should be *defined as functions* and made installable by
listing them in `pyprojects.toml`; see example `dtcc-template-main`.

That's it - happy hacking!
