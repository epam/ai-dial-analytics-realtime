import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["lint", "tests"]

SRC = "."


@nox.session
def lint(session):
    """Runs linters and fixers"""
    session.run("poetry", "install", external=True)
    session.run("poetry", "check", "--lock", external=True)
    session.run("isort", "--check", SRC)
    session.run("black", "--check", SRC)
    session.run("flake8", SRC)
    session.run("pyright", SRC)


@nox.session
def format(session):
    """Runs linters and fixers"""
    session.run("poetry", "install", external=True)
    session.run("isort", SRC)
    session.run("black", SRC)
    session.run("autoflake", SRC)


@nox.session(python=["3.10"])
def tests(session):
    """Runs tests"""
    session.run("poetry", "install", external=True)
    session.run("pytest", *session.posargs)
