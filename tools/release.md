# Release process

Versions follow [Semantic Versioning](https://semver.org/). The version
string lives in `pyproject.toml` (`project.version`) and
`pycontourlet/__init__.py` (`__version__`); both must be updated
together for a release.

When to bump which segment:

- **PATCH** (0.2.0 → 0.2.1): bug fix that doesn't change the API
  surface. New parity tests count too.
- **MINOR** (0.2.0 → 0.3.0): new public function, new keyword
  argument, or any other backwards-compatible API addition.
- **MAJOR** (0.x → 1.0): breaking change. The first 1.0 release should
  be reserved for "this API is now stable" -- not just "we have lots
  of features".

## Steps to cut a release

1. **Update versions**:
   ```sh
   # pyproject.toml: project.version = "X.Y.Z"
   # pycontourlet/__init__.py: __version__ = "X.Y.Z"
   ```

2. **Move CHANGELOG.md `[Unreleased]` entries to a new release
   section**:
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD
   ### Added
   - ...
   ### Fixed
   - ...
   ```
   And update the link references at the bottom of the file.

3. **Run the full test suite**, including Octave parity:
   ```sh
   pytest tests/
   ```
   Don't release if anything fails.

4. **Commit and tag**:
   ```sh
   git add pyproject.toml pycontourlet/__init__.py CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin develop --tags
   ```

5. **Build the wheel**:
   ```sh
   pip install --upgrade build
   rm -rf dist/ build/
   python -m build
   ```
   This produces `dist/pycontourlet-X.Y.Z-py3-none-any.whl` and
   `dist/pycontourlet-X.Y.Z.tar.gz`.

6. **Sanity-check the wheel** by installing it in a fresh venv:
   ```sh
   python -m venv /tmp/release-test
   /tmp/release-test/bin/pip install dist/pycontourlet-X.Y.Z-py3-none-any.whl
   /tmp/release-test/bin/python -m pycontourlet --out-dir /tmp/pyc-release-test
   ```

7. **(Optional) Upload to PyPI**:
   ```sh
   pip install --upgrade twine
   # Test first on TestPyPI:
   twine upload --repository testpypi dist/*
   # Then production:
   twine upload dist/*
   ```
   Requires a PyPI account and an API token in `~/.pypirc` or via env
   `TWINE_USERNAME=__token__ TWINE_PASSWORD=<token>`.

8. **Create the GitHub release**:
   ```sh
   gh release create vX.Y.Z \
     --title "vX.Y.Z" \
     --notes-from-tag dist/*
   ```
   Or via the GitHub UI by selecting the tag.

## Rollback

If a release breaks something:

1. **Don't delete the tag** -- tags are immutable contract with users.
2. Cut a new patch (`X.Y.Z+1`) that fixes the issue.
3. If the broken version was uploaded to PyPI, mark it as yanked:
   ```sh
   twine yank pycontourlet --version X.Y.Z --reason "broken release; use X.Y.(Z+1)"
   ```
   Yanked versions stay installable for users who pinned to them but
   don't get installed by default.
