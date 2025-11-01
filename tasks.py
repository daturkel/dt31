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
