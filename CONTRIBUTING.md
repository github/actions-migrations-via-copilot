# Contributing

:wave: Hi there!
We're thrilled that you'd like to contribute to the GitHub Actions Migration Agents project. Your help is essential for keeping our migration agents, knowledgebase, and patterns up-to-date and effective.

## Ways to Contribute

### Migration Agents (`agents/`)

- Improve existing migration agent prompts for better accuracy
- Add support for new CI/CD platforms
- Enhance agent instructions based on real-world migration feedback

### Knowledgebase (`knowledge/`)

- Add or update action mappings for CI/CD plugins and tasks
- Document new migration patterns and best practices
- Improve security patterns for credential handling
- Expand report templates with additional insights

### Documentation (`docs/`)

- Improve deployment and operations guides
- Add troubleshooting tips and FAQs
- Document edge cases and workarounds

### Migration Automation (`.github/workflows/`)

- Enhance bulk migration workflows
- Improve automation triggers and scheduling
- Add new automation capabilities for enterprise-scale migrations
- Optimize workflow performance and reliability

## Submitting a Pull Request

[Pull Requests][pulls] are used for adding new agents, patterns, mappings, and documentation, or improving existing ones.

### With Write Access

1. Clone the repository
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your changes
1. Push and [submit a pull request][pr]
1. Wait for your pull request to be reviewed and merged

### Without Write Access

1. [Fork][fork] and clone the repository
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your changes
1. Push to your fork and [submit a pull request][pr]
1. Wait for your pull request to be reviewed and merged

### Tips for a Successful PR

- Keep your change as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
- Write [good commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Test agent changes with real CI/CD configurations when possible.
- Follow the existing structure and formatting conventions in the knowledgebase.

Work in Progress pull requests are also welcome to get feedback early on, or if there is something blocking you.

- Create a branch with a name that identifies the user and nature of the changes (similar to `user/branch-purpose`)
- Open a pull request and mark it as a draft

## Adding a New CI/CD Platform

To add support for a new CI/CD platform:

1. Create a new agent file in `agents/` (follow existing agent structure)
2. Add action mappings in `knowledge/actions-mapping/`
3. Add security patterns in `knowledge/patterns/<platform>/`
4. Add a report template in `knowledge/report-template/`
5. Update the README.md to include the new platform

## Releasing

If you are a maintainer of this project:

1. Create a [Tag](https://stackoverflow.com/questions/18216991/create-a-tag-in-a-github-repository) following semantic versioning
2. Draft a [Release](https://help.github.com/en/github/administering-a-repository/managing-releases-in-a-repository) document explaining the changes
3. Obtain approval from [CODEOWNERS](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners)

## Resources

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Copilot Custom Agents](https://docs.github.com/en/copilot)
- [Workflow Syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

[pulls]: https://github.com/github/actions-migrations-via-copilot/pulls
[pr]: https://github.com/github/actions-migrations-via-copilot/compare
[fork]: https://github.com/github/actions-migrations-via-copilot/fork