# Another SDSE

Script editor for Danganronpa games.

Supports:
- Legacy **DRAT XML** scripts (`.xml`)
- **DRAT 1.5.2+** gettext scripts (`.po`)

## Status

![tests](https://github.com/samsungapore/Another-SDSE/actions/workflows/tests.yml/badge.svg)

## Run from source

### Requirements

- Python **3.10+**
- For the GUI: **PyQt5** + **qtpy**

### Setup

```bash
cd Another-SDSE
python -m venv .venv
source .venv/bin/activate
pip install -U pip

# Dev / tests
pip install -r requirements-dev.txt

# GUI runtime deps
pip install PyQt5 qtpy
```

### Data folder

The app expects a `./script_data/` folder.

Example:

```text
script_data/
  dr1/
    e00_000_000.xml
  dr1po/
    e00_000_000.po
```

### Launch

Run from the repository root (so `gui/*.ui` files can be found):

```bash
python editor_ui.py
```

## Development

Run tests:

```bash
pytest
```

Run tests + coverage:

```bash
coverage run -m pytest
coverage report -m
```

Notes:
- CI runs tests on every push / PR.
- The test suite uses lightweight Qt stubs, so it can run without installing PyQt5.

## License

See `LICENSE`.
