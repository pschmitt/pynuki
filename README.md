# pynuki

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
