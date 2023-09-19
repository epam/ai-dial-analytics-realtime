import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["lint", "tests"]


@nox.session
def lint(session):
    """Runs linters and fixers"""
    session.run("poetry", "install", external=True)
    session.run("isort", "--profile", "black", "dial_analytics")
    session.run("black", "dial_analytics")
    session.run("flake8", "dial_analytics")
    session.run("pyright", "dial_analytics")


@nox.session(python=["3.11"])
def tests(session):
    """Runs tests"""
    session.run("poetry", "install", external=True)
    session.run("pytest")
