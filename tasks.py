from invoke.tasks import task


@task
def test(c, html=False):
    command = "pytest --cov=dt31"
    if html:
        command += " --cov-report html"
    command += " tests"
    c.run(command, pty=True)
