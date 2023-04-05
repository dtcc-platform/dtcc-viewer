# Introduction

This template supports the creation of Python packages that include
extensions implemented in C++ using [pybind](https://github.com/pybind).
The template is based on the template
[scikit-build-example](https://github.com/pybind/scikit_build_example)
provided by the pybind and uses
[scikit-build-core](https://github.com/scikit-build/scikit-build-core)
to create pip-installable Python packages that may leverage CMake for
building the C++ extensions.

The template differs from the original `scikit-build-example` only in a few
minor ways:

* The addition of some DTCC Platform specific files: `README.md`, `LICENSE`
* The addition of documentation templates: the `docs` folder
* The addition or example Python and C++ code under `src`
* Renaming the bindings file and module: `bindings.cpp`, `_bindings`
