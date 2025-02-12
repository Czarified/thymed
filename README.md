# Thymed

[![PyPI](https://img.shields.io/pypi/v/thymed.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/thymed.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/thymed)][pypi status]
[![License](https://img.shields.io/pypi/l/thymed)][license]

[![Read the documentation at https://thymed.readthedocs.io/](https://img.shields.io/readthedocs/thymed/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/czarified/thymed/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/czarified/thymed/branch/master/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/thymed/
[read the docs]: https://thymed.readthedocs.io/
[tests]: https://github.com/czarified/thymed/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/czarified/thymed
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

- Flexible ChargeCode system with no limits on the number of codes you can define.
- Simple method to "punch" a ChargeCode. Punching logs the current timestamp and changes the "state" of the ChargeCode (active/passive or "on/off the clock").
- All data is stored locally! It's yours, you have complete control over it! There's no online backups, no phoning home, no licensing.
- Command-Line Interface (CLI) for creating, listing, and punching in/out of charge codes.

## Requirements

- No major requirements. If you have a modern Python version, you're good to go! Check out the installation section below.
- Being familiar with the command-line is a plus. If the terminal scares you, this might not be the right tool for you.
- Thymed uses [Rich](https://github.com/Textualize/rich) for console markup. A modern terminal will make output much prettier! :wink:

## Installation

You can install _Thymed_ via [pip] from [PyPI]:

```console
$ pip install thymed
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Thymed_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was originally generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/czarified/thymed/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/czarified/thymed/blob/master/LICENSE
[contributor guide]: https://github.com/czarified/thymed/blob/master/CONTRIBUTING.md
[command-line reference]: https://thymed.readthedocs.io/en/latest/usage.html
