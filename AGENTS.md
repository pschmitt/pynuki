# Agent notes

`pynuki` provides Python bindings for Nuki bridges and locks.

- Keep the Python API compatible with the examples in `README.md`.
- Run the repository's existing CI workflow and add focused tests for API
  behavior changes. Use a mock or test lock for integration checks; do not
  trigger lock or opener actions on real devices during validation.
- Before changing workflows, check for reusable workflows or actions in
  [ci-workflows](https://github.com/pschmitt/ci-workflows) and preserve
  existing triggers, inputs, and check coverage.
