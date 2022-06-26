"""NOX config."""

import glob
import importlib

import nox

nox.options.sessions = ["lint", "test", "coverage", "build"]

src_dir = "code_wake_sql14_store"
pkg_meta_src = f"{src_dir}/pkg_meta.py"


pkg_meta_spec = importlib.util.spec_from_file_location(
    "pkg_meta",
    pkg_meta_src,
)
pkg_meta = importlib.util.module_from_spec(pkg_meta_spec)
pkg_meta_spec.loader.exec_module(pkg_meta)


default_pyvsn = "3"
test_pyvsns = ["3.6", "3.7", "3.8", "3.9", "3.10"]
lintable_src = (src_dir, "test", "setup.py", "noxfile.py")
black_args = ("--line-length", "120", *lintable_src)
isort_args = ("--profile", "black", src_dir, *lintable_src)
coverage_args = ("run", "--branch", "--source=" + src_dir, "--omit=" + pkg_meta_src, "-m", "pytest", "test")
mypy_args = (src_dir,)

dev_deps = (*pkg_meta.install_requires, *pkg_meta.extras_require["dev"])


@nox.session(python=[default_pyvsn])
def lint(session):
    session.install(*dev_deps)

    session.run("black", "--check", *black_args)
    session.run("isort", "--check", *isort_args)


@nox.session(python=test_pyvsns)
def test(session):
    session.install(*dev_deps)

    session.run("pytest")


@nox.session(python=[default_pyvsn])
def mypy(session):
    session.install(*dev_deps)

    session.run("mypy", *mypy_args)


@nox.session(python=[default_pyvsn])
def coverage(session):
    session.install(*dev_deps)

    session.run("coverage", *coverage_args)
    session.run("coverage", "report")
    session.run("coverage", "html")
    session.run("coverage", "xml")


@nox.session(python=[default_pyvsn])
def build(session):
    session.install("setuptools", "wheel")

    session.run("python3", "setup.py", "sdist", "bdist_wheel")


@nox.session(python=[default_pyvsn])
def format(session):
    session.install(*dev_deps)

    session.run("black", *black_args)
    session.run("isort", *isort_args)
