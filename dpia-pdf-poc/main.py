from pprint import pprint

import click
import yaml

from generate import generate_form
from parsers import DPIATemplateParser, convert_dpia_to_form_components


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
    # with open(f"{definitions_dir}/formDefinitions.json") as f:
    #    form_definitions = json.load(f)
    # with open(f"{definitions_dir}/formSteps.json") as f:
    #    form_steps = json.load(f)
    # create_interactive_form(form_definitions, form_steps, output_file)

    with open("sources/DPIA.yaml") as file:
        template_data = yaml.safe_load(file)

    parser = DPIATemplateParser()
    dpia_template = parser.parse_dpia_template(template_data)

    form_components = convert_dpia_to_form_components(dpia_template)
    pprint(form_components)

    generate_form(form_components, output_file)


if __name__ == "__main__":
    main()
