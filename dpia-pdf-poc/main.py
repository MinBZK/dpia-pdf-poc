import json

import click

from generate import create_interactive_form


@click.command()
@click.option(
    "-d",
    "--definitions",
    "definitions_dir",
    required=True,
    type=click.Path(exists=True),
)
@click.option("-o", "--output", "output_file", required=True, type=click.Path(), help="Path to the output PDF file")
def main(definitions_dir: str, output_file: str) -> None:
    with open(f"{definitions_dir}/formDefinitions.json") as f:
        form_definitions = json.load(f)
    with open(f"{definitions_dir}/formSteps.json") as f:
        form_steps = json.load(f)
    create_interactive_form(form_definitions, form_steps, output_file)


if __name__ == "__main__":
    main()
