# Troubleshooting

This document provides solutions to common problems that may be encountered
while working with this project.

## Git

### `unrelated histories` error when pulling from `origin/main`

This error can occur if the local `main` branch has a different commit history
from the remote `main` branch. This can happen if you have made local commits
that have not been pushed to the remote repository, and the remote repository
has been updated with new commits.

**Solution:**

1.  **Reset the local `main` branch to match the remote `main` branch:**

    ```bash
    git reset --hard origin/main
    ```

2.  **If you have local commits that you want to keep, you can use `git rebase`
    to re-apply them on top of the remote `main` branch:**

    ```bash
    git rebase origin/main
    ```

## Testing

### Test failures due to unresolved merge conflict markers

If you have unresolved merge conflict markers in your code (e.g.,
`<<<<<<< HEAD`, `=======`, `>>>>>>>`), your tests will fail with syntax errors.

**Solution:**

1.  **Search for and resolve all merge conflict markers in your code.** You can
    use the `grep` command to find all instances of the markers:

    ```bash
    grep -r "<<<<<<<" .
    ```

2.  **Once you have resolved all the conflicts, run the tests again to confirm
    that they pass.**

### `NameError` and `TypeError` exceptions in tests

These errors can be caused by a variety of issues, such as missing imports or
incorrect function arguments.

**Solution:**

1.  **Carefully read the error message to identify the source of the error.**
2.  **If the error is a `NameError`, make sure that you have imported all the
    necessary modules.**
3.  **If the error is a `TypeError`, make sure that you are passing the correct
    arguments to the function.**

### Network errors in `hsp` and `services` tests

These tests may fail with network errors if the required MQTT broker service is
not available in the environment.

**Solution:**

- **Skip these tests if the MQTT broker is not available.** You can use the
  `@unittest.skipIf` decorator to skip tests based on a condition.

### `KeyError` in translation tool test

This error can be caused by a subtle logic error in the `_execute_translation`
method in `tool_dispatcher.py`.

**Solution:**

- **Ensure that the `if` condition in the `_execute_translation` method
  correctly handles both success and failure cases.** The condition should check
  for the presence of the `'error_message'` key in the response, and should also
  check for the string `"not supported"` in the error message.
