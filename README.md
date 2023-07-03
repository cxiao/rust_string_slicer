# Rust String Slicer

## Development

### Setting up a development environment

To set up a development environment, including setting up a Python virtual environment:

```
python -m venv .venv && . .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r dev-requirements.txt
python $PATH_TO_BINARY_NINJA_INSTALLATION/scripts/install_api.py
```

For formatting, linting, and running unit tests locally, install [Nox](https://nox.thea.codes/en/stable/tutorial.html), then:

```
nox
```

You can also invoke each task separately; see [noxfile.py](noxfile.py) for more details on available tasks:

```
nox -s format
nox -s lint
nox -s test
```

Linting and unit testing (both against multiple Python versions) are also set up in CI on [GitHub Actions](.github/workflows/ci.yml).

### Testing local versions of the plugin

To test the plugin locally in your own Binary Ninja installation during development, create a symbolic link between your development folder, and the [Binary Ninja user plugins folder](https://docs.binary.ninja/guide/index.html#user-folder), so that your development folder is loaded by Binary Ninja on startup as a plugin.

- MacOS:

    ```sh
    ln -s --relative . ~/Library/Application\ Support/Binary\ Ninja/plugins/rust_string_slicer
    ```

- Linux:

    ```sh
    ln -s --relative . ~/.binaryninja/plugins/rust_string_slicer
    ```

- Windows (Powershell):
    ```powershell
    New-Item -ItemType Junction -Value $(Get-Location) -Path "$env:APPDATA\Binary Ninja\plugins\rust_string_slicer
    ```

You should then change the values of the following Python settings in Binary Ninja to point to inside your development folder's virtual environment:

- `python.binaryOverride`: Set this to the path of the Python interpreter inside your development virtual environment, e.g. `$DEVELOPMENT_FOLDER/rust_string_slicer/.venv/bin/python/`
- `python.virtualenv`: Set this to the path of the `site-packages` directory inside your development virtual environment, e.g. `$DEVELOPMENT_FOLDER/rust_string_slicer/.venv/lib/python3.11/site-packages`