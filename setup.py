from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path

from itertools import chain

from setuptools import Extension, find_packages, setup

ROOT = Path(__file__).resolve().parent
PYIMGUI_DIR = ROOT / "pyimgui"


try:
    from Cython.Build import cythonize
except ImportError:  # pragma: no cover - cython not installed
    cythonize = lambda extensions, **kwargs: extensions  # type: ignore
    USE_CYTHON = False
else:
    USE_CYTHON = True


_CYTHONIZE_WITH_COVERAGE = bool(os.environ.get("_CYTHONIZE_WITH_COVERAGE"))

if _CYTHONIZE_WITH_COVERAGE and not USE_CYTHON:
    raise RuntimeError("Configured to build with Cython coverage but Cython unavailable.")


if sys.platform in ("cygwin", "win32") and not sysconfig.get_platform().startswith(
    "mingw"
):
    os_specific_flags = [f"/FI{PYIMGUI_DIR / 'config-cpp' / 'py_imconfig.h'}"]
    os_specific_libraries: list[str] = []
    os_specific_macros: list[tuple[str, str | None]] = []
else:
    os_specific_flags = [
        f"-include{PYIMGUI_DIR / 'config-cpp' / 'py_imconfig.h'}",
        "-std=c++11",  # Required for constexpr and other modern C++ features
    ]
    os_specific_libraries = ["imm32"] if sysconfig.get_platform().startswith("mingw") else []
    os_specific_macros = []


if _CYTHONIZE_WITH_COVERAGE:
    compiler_directives = {"linetrace": True}
    cythonize_opts = {"gdb_debug": True}
    general_macros = [("CYTHON_TRACE_NOGIL", "1")]
else:
    compiler_directives = {}
    cythonize_opts = {}
    general_macros: list[tuple[str, str | None]] = []


def extension_sources(module_path: str) -> list[str]:
    suffix = ".pyx" if USE_CYTHON else ".cpp"
    sources = [f"pyimgui/{module_path}{suffix}"]
    # Always include ImGui C++ sources (Cython doesn't automatically find them from directives)
    sources.extend(
        f"pyimgui/{rel}"
        for rel in [
            "imgui-cpp/imgui.cpp",
            "imgui-cpp/imgui_draw.cpp",
            "imgui-cpp/imgui_demo.cpp",
            "imgui-cpp/imgui_widgets.cpp",
            "imgui-cpp/imgui_tables.cpp",
            "config-cpp/py_imconfig.cpp",
        ]
    )
    return sources


def backend_extras(*requirements: str) -> list[str]:
    return ["PyOpenGL"] + list(requirements)


EXTRAS_REQUIRE = {
    "Cython": ["Cython>=3.0"],
    "cocos2d": backend_extras(
        "cocos2d",
        "pyglet>=1.5.6; sys_platform == 'darwin'",
    ),
    "sdl2": backend_extras("PySDL2"),
    "glfw": backend_extras("glfw"),
    "pygame": backend_extras("pygame"),
    "opengl": backend_extras(),
    "pyglet": backend_extras(
        "pyglet; sys_platform != 'darwin'",
        "pyglet>=1.5.6; sys_platform == 'darwin'",
    ),
}

EXTRAS_REQUIRE["full"] = list(set(chain(*EXTRAS_REQUIRE.values())))
EXTRAS_REQUIRE.update(
    {
        "dev": ["easydev", "black"],
        "test": ["pytest"],
    }
)


include_dirs = [
    str(PYIMGUI_DIR / "imgui"),
    str(PYIMGUI_DIR / "config-cpp"),
    str(PYIMGUI_DIR / "imgui-cpp"),
    str(PYIMGUI_DIR / "ansifeed-cpp"),
]

extension_kwargs = dict(
    extra_compile_args=os_specific_flags,
    libraries=os_specific_libraries,
    define_macros=[("PYIMGUI_CUSTOM_EXCEPTION", None)]
    + os_specific_macros
    + general_macros,
    include_dirs=include_dirs,
    language="c++",
)


EXTENSIONS = [
    Extension("imgui.core", extension_sources("imgui/core"), **extension_kwargs),
    Extension("imgui.internal", extension_sources("imgui/internal"), **extension_kwargs),
]

IMGUIPACKAGES = find_packages(where="pyimgui")
DTCC_PACKAGES = find_packages(where="src")


setup(
    packages=DTCC_PACKAGES + IMGUIPACKAGES,
    package_dir={
        "": "src",
        "imgui": "pyimgui/imgui",
    },
    include_package_data=True,
    ext_modules=cythonize(
        EXTENSIONS,
        compiler_directives=compiler_directives,
        include_path=[str(PYIMGUI_DIR)],  # Add pyimgui to Cython include path
        **cythonize_opts
    ),
    extras_require=EXTRAS_REQUIRE,
)
