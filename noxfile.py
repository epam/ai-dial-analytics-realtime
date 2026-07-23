import os

import nox

nox.options.reuse_existing_virtualenvs = True
if os.environ.get("CI"):
    nox.options.default_venv_backend = "none"
nox.options.sessions = ["lint", "tests"]

SRC = ["aidial_analytics_realtime", "tests", "noxfile.py"]


@nox.session(python=["3.12"])
def lint(session):
    """Runs linters and fixers"""
    session.run("poetry", "install", "--with", "lint", external=True)
    session.run("poetry", "check", "--lock", "--strict", external=True)
    session.run("ruff", "check", *SRC)
    session.run("ruff", "format", "--check", *SRC)
    session.run("pyright", *SRC)


@nox.session(python=["3.12"])
def format(session):
    """Runs linters and fixers"""
    session.run("poetry", "install", "--only", "lint", external=True)
    session.run("ruff", "check", "--fix", *SRC)
    session.run("ruff", "format", *SRC)


@nox.session(python=["3.12"])
def tests(session):
    """Runs tests"""
    session.run("poetry", "install", external=True)
    session.run("pytest", *session.posargs)
