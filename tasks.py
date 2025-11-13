from invoke.tasks import task


@task
def test(c, html=False, ci=False):
    command = "pytest --cov=dt31"
    if html:
        command += " --cov-report html"
    if ci:
        command += " --cov-report xml --cov-report term"
    command += " tests"
    c.run(command, pty=True)


@task
def coverage_badge(c):
    """Generate coverage badge from coverage.xml"""
    c.run("genbadge coverage -i coverage.xml -o coverage-badge.svg", pty=True)


@task
def docs(c):
    """Update documentation files."""
    c.run("pdoc --docformat google src/dt31 -t docs/templates -o docs/site")


@task
def serve_docs(c):
    """Serve the documentation website locally."""
    c.run("pdoc --docformat google -t docs/templates src/dt31")


@task
def docs_sphinx(c):
    """Build Sphinx documentation."""
    c.run("sphinx-build -b html docs-sphinx/source docs-sphinx/build")


@task
def serve_docs_sphinx(c, port=8080):
    """Serve the Sphinx documentation website locally."""
    c.run(f"python -m http.server {port} --directory docs-sphinx/build")


@task
def clean_docs_sphinx(c):
    """Clean Sphinx build directory."""
    c.run("rm -rf docs-sphinx/build")


@task
def sync(c):
    """Sync dev dependencies."""
    c.run("uv sync --locked --group dev")
