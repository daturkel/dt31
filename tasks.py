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
def sync(c):
    """Sync dev dependencies."""
    c.run("uv sync --locked --group dev")


@task
def bump(c, level, dry_run=False):
    """Bump version, commit, tag, and push.

    Args:
        level: Version bump level (major, minor, patch, or specific version)
        dry_run: If True, show what would happen without executing
    """
    # Pre-flight check: verify we're on main branch
    result = c.run("git branch --show-current", hide=True)
    current_branch = result.stdout.strip()
    if current_branch != "main":
        print(f"Error: Must be on main branch (currently on '{current_branch}')")
        raise SystemExit(1)

    # Pre-flight check: verify repo is clean
    result = c.run("git status --porcelain", hide=True)
    if result.stdout.strip():
        print(
            "Error: Working directory has uncommitted changes. Please commit or stash them first."
        )
        raise SystemExit(1)

    if dry_run:
        result = c.run(f"uv version --bump {level} --dry-run", hide=True)
        output = result.stdout.strip()
        version = output.split("=>")[-1].strip()
        print(f"[DRY RUN] Would bump version to {version}")
        print(
            f'[DRY RUN] Would commit pyproject.toml and uv.lock with message "bump to {version}"'
        )
        print("[DRY RUN] Would push commit")
        print(f"[DRY RUN] Would create and push tag {version}")
        return

    # Pull latest changes
    c.run("git pull", pty=True)

    # Bump version
    result = c.run(f"uv version --bump {level}", hide=True)
    # Parse version from output (format: "Updated version from X.Y.Z to A.B.C")
    output = result.stdout.strip()
    version = output.split("=>")[-1].strip()
    print(f"Bumped version to {version}")

    # Git commit
    c.run("git add pyproject.toml uv.lock", pty=True)
    c.run(f'git commit -m "bump to {version}"', pty=True)

    # Git push
    c.run("git push", pty=True)

    # Git tag
    c.run(f"git tag {version}", pty=True)
    c.run(f"git push origin {version}", pty=True)

    print(f"Successfully released version {version}")
