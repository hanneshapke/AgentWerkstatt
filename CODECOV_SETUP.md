# Codecov Setup Guide

This guide explains how to set up dynamic test coverage reporting with Codecov for the AgentWerkstatt project.

## Overview

The project is configured to automatically:
- ✅ Run tests with coverage on every CI build
- ✅ Upload coverage reports to Codecov
- ✅ Display a dynamic coverage badge in README.md
- ✅ Comment on pull requests with coverage changes

## Setup Steps

### 1. GitHub Repository Settings

1. Go to [Codecov.io](https://codecov.io/) and sign in with GitHub
2. Add your repository: `hanneshapke/AgentWerkstatt`
3. Get your Codecov token from the repository settings

### 2. GitHub Secrets

Add the Codecov token to your GitHub repository secrets:

1. Go to `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Name: `CODECOV_TOKEN`
4. Value: Your Codecov token

### 3. Configuration Files

The following files are already configured:

- `.codecov.yml` - Codecov configuration
- `.github/workflows/ci-cd.yml` - GitHub Actions with coverage upload
- `scripts/check_coverage.py` - Local coverage checking script

## How It Works

### CI/CD Pipeline

1. **Tests Run**: GitHub Actions runs `pytest --cov=src/agentwerkstatt --cov-report=xml`
2. **Upload**: Coverage XML report is uploaded to Codecov
3. **Badge Update**: Codecov automatically updates the badge
4. **PR Comments**: Coverage changes are commented on pull requests

### Local Development

```bash
# Quick coverage check
python scripts/check_coverage.py

# Detailed HTML report
uv run pytest --cov=src/agentwerkstatt --cov-report=html
open htmlcov/index.html
```

### Badge in README

The dynamic badge automatically shows current coverage:

```markdown
<a href="https://codecov.io/gh/hanneshapke/AgentWerkstatt">
  <img src="https://codecov.io/gh/hanneshapke/AgentWerkstatt/branch/main/graph/badge.svg" alt="Test Coverage">
</a>
```

## Coverage Targets

- **Project Target**: 90% minimum coverage
- **Patch Target**: 90% coverage for new code
- **Threshold**: 5% change allowed before CI fails

## Benefits

1. **Real-time Updates**: Badge reflects actual coverage from latest CI run
2. **PR Integration**: See coverage impact of changes before merging
3. **Historical Tracking**: Codecov provides coverage trends over time
4. **Professional Look**: Shows commitment to code quality
5. **No Manual Maintenance**: Fully automated

## Troubleshooting

### Badge Not Updating

- Check if Codecov token is correctly set in GitHub secrets
- Verify the repository name in the badge URL
- Ensure CI is running successfully and uploading coverage

### Coverage Upload Failing

- Check GitHub Actions logs for upload errors
- Verify `coverage.xml` file is being generated
- Ensure Codecov action has the correct token

### Local Coverage Issues

```bash
# Ensure all dependencies are installed
uv sync --dev

# Run with verbose output
uv run pytest --cov=src/agentwerkstatt --cov-report=term-missing -v
```

## Links

- [Codecov Repository](https://codecov.io/gh/hanneshapke/AgentWerkstatt)
- [Codecov Documentation](https://docs.codecov.com/)
- [GitHub Actions Codecov](https://github.com/codecov/codecov-action)
