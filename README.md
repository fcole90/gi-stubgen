# gi-stubgen

⚠️ This is a work in progress! ⚠️

Generate Python stubs for GObject-based libraries.

Requires [gi-docgen](https://gitlab.gnome.org/GNOME/gi-docgen).

## Usage

```bash
source ./scripts/venv.sh
./scripts/generate-intermediate.sh
./scripts/generate-stubs.sh
```

Point your linter/static analysis tool to the resulting `.stubs` folder.
