# Installation

DTCC Template can be easily installed using [`pip`](https://pypi.org/project/pip/).

To install from the Python Package Index (PyPI):

    pip install dtcc-template

To install from the source directory:

    pip install .

> **NOTE**: Fix for conflicting versions of `pip` and `python`
>
> Sometimes `pip` and `python` may be out of sync which means that `pip` will
> install a package in a location where it will not be found by `python`.
> It is therefore safer to replace the `pip` command by `python -m pip`:
>
>     python -m pip install [ package-name or . ]

> **NOTE**: Fix for broken setuptools in Ubuntu 22.04
>
> A bug in Ubuntu 22.04 prevents [PEP621](https://peps.python.org/pep-0621/)
> compliant Python projects from installing properly with `pip`, resulting in
> package name and version number `UNKNOWN-0.0.0`.
> To fix this, run the following commmand before `pip install`:
>
>     export DEB_PYTHON_INSTALL_LAYOUT=deb_system
