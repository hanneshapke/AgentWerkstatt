# CI/CD Pipeline Setup

This document explains how to set up and configure the CI/CD pipeline for AgentWerkstatt.

## Overview

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:

1. **Quality Checks**: Runs linting, formatting, type checking, and tests across Python 3.10, 3.11, and 3.12
2. **Build**: Creates distribution packages and validates them
3. **Test Publishing**: Publishes to Test PyPI on pushes to main branch
4. **Production Publishing**: Publishes to PyPI when you create version tags

## Workflow Triggers

- **Pull Requests**: Runs quality checks and build
- **Push to main/develop**: Runs quality checks, build, and publishes to Test PyPI
- **Version Tags**: Runs quality checks, build, and publishes to production PyPI

## Required Secrets

To enable publishing, you need to set up the following secrets in your GitHub repository:

### 1. Test PyPI Token (for automatic test releases)

1. Go to [Test PyPI](https://test.pypi.org/manage/account/token/)
2. Create a new API token
3. In your GitHub repository, go to Settings → Secrets and variables → Actions
4. Add a new secret:
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: Your Test PyPI token (including the `pypi-` prefix)

### 2. Production PyPI Token (for production releases)

1. Go to [PyPI](https://pypi.org/manage/account/token/)
2. Create a new API token
3. In your GitHub repository, go to Settings → Secrets and variables → Actions
4. Add a new secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token (including the `pypi-` prefix)

## GitHub Environments (Optional but Recommended)

For better security, set up GitHub environments:

1. Go to Settings → Environments
2. Create two environments:
   - `test-pypi`: For Test PyPI publishing
   - `pypi`: For production PyPI publishing
3. Configure protection rules for the `pypi` environment (e.g., require review)

## Release Workflow

### Development Releases (Test PyPI)

Automatic releases to Test PyPI happen when you push to the main branch:

```bash
git checkout main
git pull origin main
# Make your changes, commit, and push
git push origin main
```

### Production Releases (PyPI)

Production releases happen when you create and push a version tag:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

The version is automatically determined by `setuptools-scm` based on your git tags.

## Monitoring

1. **Actions Tab**: Monitor workflow runs in your repository's Actions tab
2. **Coverage**: Coverage reports are uploaded to Codecov (optional)
3. **Package Status**: Check your packages on [PyPI](https://pypi.org/project/agentwerkstatt/) and [Test PyPI](https://test.pypi.org/project/agentwerkstatt/)

## Local Development

Before pushing, run the same checks locally:

```bash
# Install development dependencies
uv sync --dev

# Run all quality checks
uv run ruff check --fix
uv run ruff format
uv run mypy .
uv run pytest

# Or use the pre-commit script
uv run pre-commit
```

## Troubleshooting

### Common Issues

1. **Tests failing**: Make sure all tests pass locally first
2. **Import errors**: Ensure your package structure is correct and `__init__.py` files are present
3. **Publishing fails**: Check that your API tokens are correctly set in GitHub secrets
4. **Version conflicts**: Use `setuptools-scm` versioning - avoid manual version numbers

### Useful Commands

```bash
# Check what version would be generated
uv run python -c "from setuptools_scm import get_version; print(get_version())"

# Test build locally
uv tool install build
uv tool run build

# Test package installation locally
pip install dist/*.whl
```

## Customization

You can customize the workflow by:

1. **Adding more Python versions**: Update the matrix in `quality-checks` job
2. **Adding more checks**: Add steps to the quality checks
3. **Changing triggers**: Modify the `on:` section
4. **Environment-specific configuration**: Use GitHub environments with different settings

## Next Steps

1. Set up the required secrets
2. Make a test commit to trigger the workflow
3. Create your first version tag for a production release
4. Monitor the Actions tab to ensure everything works correctly
