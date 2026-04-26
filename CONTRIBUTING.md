# Actions Migrations via Copilot — Contribution License Agreement

Thanks for contributing! 🎉 This Contribution License Agreement ("Agreement") covers the license rights you grant to GitHub, Inc. and its affiliates ("GitHub") when you contribute to this project. By signing, you ("You") agree to the terms below. This Agreement is effective as of your signature date.

## 1. What This Covers

This Agreement applies to every contribution you make to this repository, now and in the future. You must agree to these terms before contributing.

## 2. Your Work Must Be Original

You represent that each contribution is your own original work.

If you want to contribute materials that aren't entirely yours (e.g., third-party code), you may do so **separately** — provided you:

- retain all original copyright and license notices,
- note in the Submission description: "Contains third-party materials:" followed by the name(s) and any license restrictions you're aware of, and
- follow any additional instructions in the project's [contributing guide](CONTRIBUTING.md).

## 3. Employer Contributions

If you're contributing as part of your work for an employer — or if your employer has IP rights over your work by contract or law — you must get your employer's permission before contributing.

When that's the case, "You" means both you and your employer. If you change employers and want to keep contributing, you need your new employer's permission.

## 4. License Grants

a. Copyright License. You grant GitHub (and anyone who receives the Submission from GitHub, directly or indirectly) a **perpetual, worldwide, non-exclusive, royalty-free, irrevocable** license to reproduce, prepare derivative works of, publicly display, publicly perform, distribute, and sublicense the Submission.

b. Patent License. You grant GitHub (and downstream recipients) a **perpetual, worldwide, non-exclusive, royalty-free, irrevocable** patent license — covering only patent claims necessarily infringed by your Submission or its combination with the Project — to make, have made, use, offer to sell, sell, import, and otherwise dispose of the Submission alone or with the Project.

c. No Other Rights. All rights not expressly granted here are reserved by each party. No additional licenses are implied.

## 5. Your Representations

You represent that:

- You are legally entitled to grant the licenses in Section 5.
- Each contribution is your original work (except as disclosed under Section 3).
- If applicable, you have your employer's permission (see Section 4).
- If contributing on behalf of your employer, you have authority to bind them to this Agreement.

You are not expected to provide support for your Submissions unless you choose to.

EXCEPT FOR THE REPRESENTATIONS IN SECTIONS 3, 4, AND 6, YOUR SUBMISSIONS ARE PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND — INCLUDING WARRANTIES OF NONINFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE — UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING.

## 6. Let Us Know If Something Changes

If you learn of anything that would make your representations in this Agreement inaccurate, notify GitHub in writing.

## 7. Public Record

Contributions to this project — including your name and any information you include with your Submission — may be maintained indefinitely and disclosed publicly.

## 8. Governing Law

This Agreement is governed by the laws of the State of California and the federal laws of the United States. Both parties consent to exclusive jurisdiction and venue in the federal and state courts in San Francisco, California, and waive any objection to personal jurisdiction or forum.

## 9. Entire Agreement

This is the entire agreement between the parties on this subject and supersedes all prior agreements or communications. GitHub may assign this Agreement.

--

## Ways to contribute

Contributions are welcome — whether that's fixing a typo, improving an agent prompt, or adding support for a new CI/CD platform.

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

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

This project runs on LLMs, so AI-assisted contributions are welcome. That said, AI tools can produce a lot of low-quality issues and PRs fast — please review what you're submitting before you submit it. The human submitter is responsible for:

- Reviewing all AI-generated code
- Ensuring compliance with licensing requirements
- Taking full responsibility for the contribution

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

1. Create a [tag](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) following semantic versioning
2. Draft a [release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) document explaining the changes
3. Obtain approval from [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

## Resources

- [Contributing to a Project](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project)
- [Using Pull Requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
- [GitHub Support](https://support.github.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Copilot Custom Agents](https://docs.github.com/en/copilot/customizing-copilot/building-custom-extensions-for-github-copilot)
- [Workflow Syntax for GitHub Actions](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)

[issues]: https://github.com/github/actions-migrations-via-copilot/issues
[pulls]: https://github.com/github/actions-migrations-via-copilot/pulls
[pr]: https://github.com/github/actions-migrations-via-copilot/compare
[fork]: https://github.com/github/actions-migrations-via-copilot/fork
