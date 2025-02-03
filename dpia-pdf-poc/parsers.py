from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, TypeVar


@dataclass
class FormComponent:
    """Data class representing a form component with its properties"""

    id: str
    key: str
    type: str
    description: str
    label: str
    options: list[dict[str, str]] | None = None
    components: list["FormComponent"] | None = None


T = TypeVar("T", bound="FormParser")


class FormParser:
    """Responsible for parsing form definitions into structured data"""

    @staticmethod
    def parse_component(component_data: dict[str, Any]) -> FormComponent:
        """Parse a single component from the form definition"""
        options = None
        if component_data.get("data", {}).get("values"):
            options = [{"label": opt["label"], "value": opt["value"]} for opt in component_data["data"]["values"]]

        sub_components = None
        if component_data.get("components"):
            sub_components = [FormParser.parse_component(comp) for comp in component_data["components"]]

        return FormComponent(
            id=component_data["id"],
            key=component_data["key"],
            type=component_data["type"],
            description=component_data["description"],
            label=component_data["label"],
            options=options,
            components=sub_components,
        )

    @classmethod
    def parse_form_definition(cls, form_definitions: Iterable[dict[str, Any]]) -> list[FormComponent]:  # noqa
        """Parse the complete form definition"""
        return [
            cls.parse_component(component)
            for form_definition in form_definitions
            for component in form_definition["configuration"]["components"]
        ]


@dataclass
class StepComponent:
    """Data class representing a step component with its properties"""

    id: str
    key: str
    type: str
    label: str
    components: list["StepComponent"] | None = None


@dataclass
class Step:
    """Data class representing a step component with its properties"""

    index: int
    components: list[StepComponent] = field(default_factory=list)


class StepParser:
    """Responsible for parsing form steps into structured data"""

    @staticmethod
    def parse_component(component_data: dict[str, Any]) -> StepComponent:
        """Parse a single component from the form definition"""
        sub_components = None
        if component_data.get("components"):
            sub_components = [StepParser.parse_component(comp) for comp in component_data["components"]]

        return StepComponent(
            id=component_data["id"],
            key=component_data["key"],
            type=component_data["type"],
            label=component_data["label"],
            components=sub_components,
        )

    @classmethod
    def parse_form_definition(cls, form_steps: Iterable[dict[str, Any]]) -> list[Step]:  # noqa
        """Parse the complete form definition"""

        return [
            Step(
                index=form_step["index"],
                components=[cls.parse_component(component) for component in form_step["configuration"]["components"]],
            )
            for form_step in form_steps
        ]
