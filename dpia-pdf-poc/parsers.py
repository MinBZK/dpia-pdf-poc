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
    def parse_form_definition(cls, form_definitions: Iterable[dict[str, Any]]) -> list[FormComponent]:
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
    def parse_form_definition(cls, form_steps: Iterable[dict[str, Any]]) -> list[Step]:
        """Parse the complete form definition"""

        return [
            Step(
                index=form_step["index"],
                components=[cls.parse_component(component) for component in form_step["configuration"]["components"]],
            )
            for form_step in form_steps
        ]


@dataclass
class Author:
    """Data class representing an author in the template"""

    name: str
    email: str
    role: str


@dataclass
class TaskTemplate:
    """Data class representing a task template"""

    authors: list[Author]


@dataclass
class Task:
    """Data class representing a DPIA task with its properties"""

    task: str
    urn: str
    type: list[str]
    repeatable: bool
    options: list[str] | None = None
    explanation: str | None = None
    links: list[Any] = field(default_factory=list)
    glossary_references: list[str] | None = None
    template: TaskTemplate | None = None
    tasks: list["Task"] | None = None


@dataclass
class Owner:
    """Data class representing a DPIA template owner"""

    organization: str
    name: str
    email: str
    role: str


@dataclass
class DPIATemplate:
    """Data class representing the complete DPIA template"""

    schema_version: str
    name: str
    description: str
    urn: str
    language: str
    owners: list[Owner]
    date: str
    url: str
    tasks: list[Task]


T = TypeVar("T", bound="DPIATemplateParser")


class DPIATemplateParser:
    """Parser for DPIA template definitions"""

    @staticmethod
    def parse_author(author_data: dict[str, str]) -> Author:
        """Parse an author from the template data"""
        return Author(name=author_data["name"], email=author_data["email"], role=author_data["role"])

    @staticmethod
    def parse_template(template_data: dict[str, Any]) -> TaskTemplate:
        """Parse a task template"""
        return TaskTemplate(authors=[DPIATemplateParser.parse_author(author) for author in template_data["authors"]])

    @classmethod
    def parse_task(cls, task_data: dict[str, Any]) -> Task:
        """Parse a single task from the template definition"""
        subtasks = None
        if task_data.get("tasks"):
            subtasks = [cls.parse_task(subtask) for subtask in task_data["tasks"]]

        template = None
        if task_data.get("template"):
            template = cls.parse_template(task_data["template"])

        return Task(
            task=task_data["task"],
            urn=task_data["urn"],
            type=task_data["type"],
            repeatable=task_data.get("repeatable", False),
            options=task_data.get("options"),
            explanation=task_data.get("explanation"),
            links=task_data.get("links", []),
            glossary_references=task_data.get("glossary_references"),
            template=template,
            tasks=subtasks,
        )

    @staticmethod
    def parse_owner(owner_data: dict[str, str]) -> Owner:
        """Parse an owner from the template data"""
        return Owner(
            organization=owner_data["organization"],
            name=owner_data["name"],
            email=owner_data["email"],
            role=owner_data["role"],
        )

    @classmethod
    def parse_dpia_template(cls, template_data: dict[str, Any]) -> DPIATemplate:
        """Parse the complete DPIA template definition"""
        return DPIATemplate(
            schema_version=template_data["schema_version"],
            name=template_data["name"],
            description=template_data["description"],
            urn=template_data["urn"],
            language=template_data["language"],
            owners=[cls.parse_owner(owner) for owner in template_data["owners"]],
            date=template_data["date"],
            url=template_data["url"],
            tasks=[cls.parse_task(task) for task in template_data["tasks"]],
        )


def convert_type(dpia_type: list[str]) -> str:
    """Convert DPIA task type to FormComponent type"""
    type_mapping = {
        "open_text": "textfield",
        "select_option": "select",
        "task_group": "fieldset",
    }
    # Use the first type in the list that has a mapping
    for t in dpia_type:
        if t in type_mapping:
            return type_mapping[t]
    return "textfield"  # Default fallback


def convert_options(dpia_options: list[str] | None) -> list[dict[str, str]] | None:
    """Convert DPIA options to FormComponent options format"""
    if not dpia_options:
        return None
    return [{"label": opt, "value": opt.lower().replace(" ", "_")} for opt in dpia_options]


def convert_task_to_component(task: Task) -> FormComponent:
    """Convert a DPIA Task to a FormComponent"""
    # For tasks with subtasks, create a fieldset
    if task.tasks:
        sub_components = [convert_task_to_component(subtask) for subtask in task.tasks]
        component_type = "fieldset"
    else:
        sub_components = None
        component_type = convert_type(task.type)

    return FormComponent(
        id=task.urn,
        key=task.urn,
        type=component_type,
        description=task.explanation or "",
        label=task.task,
        options=convert_options(getattr(task, "options", None)),
        components=sub_components,
    )


def convert_dpia_to_form_components(dpia_template: DPIATemplate) -> list[FormComponent]:
    """Convert a DPIA template to a list of FormComponents"""
    return [convert_task_to_component(task) for task in dpia_template.tasks]
