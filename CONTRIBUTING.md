# Contributing to the hetida designer

We greatly appreciate your contribution to the hetida designer!

There are many ways you can help us to make the hetida designer even better:

- [Ask a question or request support](#question)
- [Report an issue or bug](#issue)
- [Request a new feature](#feature)
- [Contribute documentation or code](#submit-pr)
- [Coding Rules](#rules)

## <a name="question"></a> Got a Question or Problem?

Please do not open bug reports for general support questions as we want to keep GitHub
issues for bug reports and feature requests. Don't hesitate to contact us via
[email][email] instead.

## <a name="issue"></a> Found an Issue or Bug?

If you find a bug in the source code or a mistake in the documentation, you can help us by
[submitting an issue](#submit-issue) to our [GitHub Repository][github].

You can help the team even more and [submit a Pull Request](#submit-pr) with a fix.

## <a name="feature"></a> Missing a Feature?

You can _request_ a new feature by [submitting an issue](#submit-issue) to our [GitHub
Repository][github] with your feature proposal.

If you would like to _implement_ a new feature, please submit an issue with
a proposal for your work first, to be sure that we can use it. Once we agree
on whether and how the new feature is to be implemented, you are welcome to
[submit a pull request](#submit-pr) with your implementation.

## <a name="submit-issue"></a> How to submit an Issue?

Before you submit an issue, search the [archive](https://github.com/hetida/hetida-designer/issues). Maybe someone else already
reported the same issue before? Maybe your problem was already discussed and
a decision been taken? Maybe the issue has already been solved in the latest
release?

**If you think that you have found a security vulnerability then please write
us a [private email][email] with your bug report rather than opening a public
issue on GitHub!**

Otherwise: If your issue appears to be a bug, and hasn't been reported before,
[open a new issue on GitHub][new-issue] with the following information:

- **Overview of the Issue** - Brief description of the expected behavior and
  the actual behavior. If an error is being thrown in the browser, a stack trace
  helps. If something is visibly wrong, a screenshot or screencast may be more
  helpful than a textual description.
- **Reproduce the Error** - Provide step-by-step instructions how the error
  can be reproduced.
- **Versions** - Which versions of the hetida designer are affected (e.g. 1.0.1)
- **Browsers, Infrastructure Setup, Operating System** - Is this a problem with
  all browsers or just a specific one? How do you deploy the hetida designer
  Runtime, Backend and Frontend (K8S, Docker, etc.)?
- **Related Issues** - Has a similar issue been reported before?
- **Suggest a Fix** - If you can't fix the bug yourself, perhaps you can point
  to what might be causing the problem (line of code or commit).

### <a name="submit-pr"></a> How to submit a Pull Request (PR)?

Follow the instructions below to open your Pull Request:

- Make sure you've forked our code on [GitHub][github] and fetched the latest
  version.

  If you had never downloaded our code before then get a local copy of your fork:

  ```shell
  git clone https://github.com/your-user/hetida-designer.git
  ```

  Otherwise retrieve latest changes from the remote repository if you
  had cloned the repository before:

  ```shell
  git fetch
  ```

* Start a new git branch:

  To submit a bug fix:

  ```shell
  git checkout -b bugfix/my-fix origin/develop
  ```

  To submit a feature:

  ```shell
  git checkout -b feature/my-feature origin/develop
  ```

* Create your patch, if possible **including appropriate test cases**.
* Follow our [Coding and Formatting Rules](#rules).
* Test your changes in an integrated demo environment (runtime, backend and frontend),
  e.g. by using our [docker compose setup][getting-started].
* Run existing tests and ensure that they all pass.
* If you have contributed a larger feature or introduced a breaking change then
  update the [CHANGELOG.md][changelog] with details of changes to the interface or
  APIs. This includes new environment variables, exposed endpoints, locations
  of important files, container parameters, configuration parameters, etc.
* Commit your changes using a descriptive commit message that mentions the
  issue number e.g. `... (fixes: #123)` for a bug fix or `... (implements: #123)`
  for a feature request.

  ```shell
  git commit -a
  ```

  Note: the optional commit `-a` command line option will automatically "add" and "rm" edited files.

* Push your branch to GitHub:

  ```shell
  git push origin bugfix/my-fix
  ```

* In GitHub, [open a pull request][new-pr] against our `develop` branch.
* We will then review your pull request based on our [coding rules](#rules).
  If we suggest changes then:

  - Make the required updates.
  - Re-run the test suites to ensure tests are still passing.
  - Rebase your branch and force push to your GitHub repository. This will
    automatically update your Pull Request:

    ```shell
    git fetch
    git rebase -i origin/develop
    git push -f
    ```

That's it! Thank you for your contribution!

#### After your pull request is merged...

After your pull request is merged, you can safely delete your branch and pull the changes
from the upstream repository.

```shell
git checkout develop
git pull
```

## <a name="rules"></a> Coding Rules

To ensure consistency throughout the source code, we have defined coding rules
which need to be followed when [submitting a PR](#submit-pr). These rules will
guide our code review when we provide feedback about your PR.

As the hetida designer is developed in two separate technologies - namely Python
for runtime and backend, and Angular/TypeScript for the
frontend - we have specific rules that apply to each one of these technologies:

- [Coding Rules for Runtime and Backend][coding-rules-runtime]
- [Coding Rules for the Frontend][coding-rules-frontend]

[coding-rules-runtime]: https://github.com/hetida/hetida-designer/blob/release/runtime/CODING_STANDARDS.md
[coding-rules-frontend]: https://github.com/hetida/hetida-designer/blob/release/frontend/CODING_STANDARDS.md
[changelog]: https://github.com/hetida/hetida-designer/blob/release/CHANGELOG.md
[email]: mailto:hetida@neusta-sd-west.de
[getting-started]: https://github.com/hetida/hetida-designer/blob/release/README.md#gs-docker-compose
[github]: https://github.com/hetida/hetida-designer
[new-issue]: https://github.com/hetida/hetida-designer/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D
[new-pr]: https://github.com/hetida/hetida-designer/compare/develop
