"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Thymed."""


if __name__ == "__main__":
    main(prog_name="thymed")  # pragma: no cover
