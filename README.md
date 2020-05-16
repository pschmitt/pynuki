# pynuki

![PyPI](https://img.shields.io/pypi/v/pynuki)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pynuki)
![PyPI - License](https://img.shields.io/pypi/l/pynuki)
![Python Lint](https://github.com/pschmitt/pynuki/workflows/Python%20Lint/badge.svg)

Python library for interacting with Nuki locks and openers

## Installation

```bash
pip install -U pynuki
```

## Usage

```python
from pynuki import NukiBridge

bridges = NukiBridge.discover()
br = bridges[0]
br.token = "YOUR_TOKEN"

# Locks
br.locks[0].lock()
br.locks[0].unlock()

# Openers
br.openers[0].activate_rto()
br.openers[0].deactivate_rto()
```
