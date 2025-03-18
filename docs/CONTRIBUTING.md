# Contributing to Job Search Assistant

First time contributors can refer to [First Contributions](https://github.com/firstcontributions/first-contributions) for learning basics.

## Table of Contents

- [Contributing to Job Search Assistant](#contributing-to-job-search-assistant)
  - [Table of Contents](#table-of-contents)
- [Filing Github issue](#filing-github-issue)
  - [Bug Reports](#bug-reports)
  - [Feature Requests](#feature-requests)
  - [Branch Rules](#branch-rules)
  - [Version Control](#version-control)
  - [Release Process](#release-process)
  - [Pull Request Process](#pull-request-process)
  - [Merging Pull Requests](#merging-pull-requests)
  - [Code Style Guidelines](#code-style-guidelines)
  - [Development Setup](#development-setup)
  - [Testing](#testing)
  - [Communication](#communication)

[Development Diagrams](./docs/development_diagrams.md)

# Filing Github issue

Refer to [project management docs](/docs/project_management.md#issue-labels) for tagging appropriate labels.

## Bug Reports

When submitting a bug report, please include:

- A clear, descriptive title prefixed with [BUG]
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any error messages or screenshots
- Your environment details (OS, Python version, etc.)
- Check skipped.json, error.json - make sure you add job portal link so that others can reproduce and fix the issue.

## Feature Requests

For feature requests, please:

- Prefix the title with [FEATURE]
- Include a feature summary
- Provide a detailed feature description
- Explain your motivation for the feature
- List any alternatives you've considered

## Branch Rules

- `main` - tested code, protected branch
- Contributors need to create their working branch from `main` and point pull requests to `main`

## Version Control

- Semantic versioning: `vMAJOR.MINOR.PATCH`
- Release tags on `main` branch only
- Package versions match git tags

## Release Process

Week one for `release/v4.1.0`:

- Planning meeting for `release/v4.1.0` with release scope and milestone objectives set by the maintainers. Release and maintainer meeting agendas and schedules are posted on the project repository [wiki](https://github.com/AIHawk/AIHawk/wiki) and shared in the `#releases` channel on Discord.
- `release/v4.0.0` release candidate ready for release
- `release/v4.0.0` merge into `develop`, `main`
- Tag `main` as `release/v4.0.0`
- `release/v4.0.0` published to AIHawk/releases and PyPI as a package with release documentation
- Delete `release/v4.0.0` branch

Release/v4.1.0 release weeks:

- Contributors work on issues and PRs, prioritizing next milestone
- Maintainers review PRs from `feature/*`, `bugfix/*` branches and issues, merging into `develop`
- Maintainers review PRs from `hotfix/*` branches and issues, merged into `main` and `develop`, `main` tagged and merged into `4.0.1` package and `release/v4.0.1` and `release/v4.1.0`, documentation is updated

Last week, release candidate:

- `develop` is frozen, only bug fixes
- Create release branch `release/v4.1.0` from `develop`
- Only bug fixes are merged into `release/v4.1.0`
- Additional testing and release candidate review

Week one is repeated for `release/v4.2.0`.

```mermaid
gantt
    title Release Cycle Process
    dateFormat  YYYY-MM-DD
    section Retro/Plan
    Planning release/v4.1.0    : 2025-01-01, 2d
    Publish release/v4.0.0     :milestone, m1, 2025-01-01, 1d
    
    section Dev Cycle
    Feature Development        :2025-01-03, 27d
    PR Reviews                 :2025-01-03, 27d
    
    section Release
    Freeze develop              :milestone, m3, 2025-01-30, 1d
    Create release/v4.1.0   :milestone, m4, 2025-01-30, 1d
    Bug Fixes Only         :2025-01-30, 2d
    RC Testing             :2025-01-30, 2d
    
    section Next Cycle
    Skip Weekend             :2025-02-01, 2d
    Planning release/v4.2.0      :2025-02-03, 2d
    Publish release/v4.1.0     :milestone, m4, 2025-02-03, 1d
```

## Pull Request Process

1. Fork the repository
2. Create a new branch for your feature or bug
3. Write clear commit messages
4. Update documentation as needed
5. Add tests for new functionality
6. Ensure tests pass
7. Submit a pull request with a clear description

## Merging Pull Requests

- All PRs are reviewed by maintainers
- At least 2 maintainers approve PRs for merge
- PRs are merged into `develop`
- PRs are tested and verified to work as expected

## Code Style Guidelines

- Follow PEP 8 standards for Python code
- Include docstrings for new functions and classes
- Add comments for complex logic
- Maintain consistent naming conventions
- Security best practices
- Any performance considerations

## Development Setup

1. Clone the repository
2. Install dependencies from requirements.txt
3. Set up necessary API keys and configurations

## Testing

Before submitting a PR:

- Test your changes thoroughly
- Ensure existing tests pass
- Add new tests for new functionality
- Verify functionality with different configurations

## Communication

- Be respectful and constructive in discussions
- Use clear and concise language
- Reference relevant issues in commits and PRs
- Ask for help when needed

The project maintainers reserve the right to reject any contribution that doesn't meet these guidelines or align with the project's goals.
