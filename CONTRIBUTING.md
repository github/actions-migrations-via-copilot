# Contributing

Contributions are welcome — whether that's fixing a typo, improving an agent prompt, or adding support for a new CI/CD platform.

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Ways to contribute

### Migration agents (`agents/`)

- Improve existing agent prompts for better accuracy
- Add support for new CI/CD platforms
- Update agent instructions based on real migration feedback

### Knowledgebase (`knowledge/`)

- Add or update action mappings for CI/CD plugins and tasks
- Document new migration patterns and best practices
- Improve security patterns for credential handling
- Expand report templates

### Documentation (`docs/`)

- Improve deployment and operations guides
- Add troubleshooting tips and FAQs
- Document edge cases and workarounds

### Migration automation (`.github/workflows/`)

- Improve bulk migration workflows
- Add or adjust automation triggers
- Optimize workflow performance and reliability

### Adding a new CI/CD platform

To add support for a new platform:

1. Create a new agent file in `agents/` (follow existing agent structure)
2. Add action mappings in `knowledge/actions-mapping/`
3. Add security patterns in `knowledge/patterns/<platform>/`
4. Add a report template in `knowledge/report-template/`
5. Update README.md to include the new platform

## AI contributions

This project runs on LLMs, so AI-assisted contributions are welcome. That said, AI tools can produce a lot of low-quality issues and PRs fast — please review what you're submitting before you submit it.

### Issues

- Keep issues narrow and specific. "Update guardrails to prevent old action versions from being chosen" is a good issue. "Redesign the agent architecture" is not — that needs a conversation first.
- Issues proposing architectural changes or major new functionality need maintainer sign-off before any work starts.

### Pull requests

- Every PR needs a linked issue. PRs without one will be rejected automatically.
- You're responsible for AI-generated code you submit. Read it before sending it.

Maintainers can reject any issue or PR, for any reason or none.

## Opening an issue

[Open an issue][issues] before you start work. It gives maintainers a chance to weigh in early, which saves everyone time if the change isn't a good fit.

**All pull requests must reference an open issue. PRs without a linked issue will be rejected automatically.**

## Submitting a pull request

[Pull requests][pulls] are how changes get made — new agents, patterns, mappings, docs, or improvements to existing ones.

### With write access

1. Clone the repository
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your changes
1. Push and [submit a pull request][pr]
1. Wait for your pull request to be reviewed and merged

### Without write access

1. [Fork][fork] and clone the repository
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your changes
1. Push to your fork and [submit a pull request][pr]
1. Wait for your pull request to be reviewed and merged

### Tips for a good PR

- Link the related issue.
- One change per PR. If you have unrelated changes, open separate pull requests.
- Write [good commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Test agent changes with real CI/CD configurations when you can.
- Follow the existing structure and formatting in the knowledgebase.

Not ready? Open a draft PR to get early feedback.

- Use a branch name like `user/branch-purpose`
- Mark the pull request as a draft

## Releasing

If you are a maintainer:

1. Create a [tag](https://stackoverflow.com/questions/18216991/create-a-tag-in-a-github-repository) following semantic versioning
2. Draft a [release](https://help.github.com/en/github/administering-a-repository/managing-releases-in-a-repository) document explaining the changes
3. Obtain approval from [CODEOWNERS](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners)

## Resources

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Copilot Custom Agents](https://docs.github.com/en/copilot)
- [Workflow Syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

[issues]: https://github.com/github/actions-migrations-via-copilot/issues
[pulls]: https://github.com/github/actions-migrations-via-copilot/pulls
[pr]: https://github.com/github/actions-migrations-via-copilot/compare
[fork]: https://github.com/github/actions-migrations-via-copilot/fork