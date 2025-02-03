from collections.abc import Iterable
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from parsers import FormComponent, FormParser, Step, StepParser


def order_components(steps: Iterable[Step], components: Iterable[FormComponent]) -> list[FormComponent]:
    components_by_id = {comp.id: comp for comp in components}
    return [
        components_by_id[step_comp.id]
        for step in sorted(steps, key=lambda s: s.index)
        for step_comp in step.components
        if step_comp.id in components_by_id
    ]


class InteractivePDFGenerator:
    """Generates interactive PDF forms using paragraphs"""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter
        self.margin = 50
        self.text_width = self.width - 2 * self.margin

    def create_paragraph(self, text: str, style: Any | None = None) -> Paragraph:
        """Create a paragraph with optional styling"""
        if style is None:
            style = self.styles["Normal"]
        p = Paragraph(text, style)
        return p

    def draw_paragraph(self, canvas: canvas.Canvas, paragraph: Paragraph, x: float, y: float) -> float:
        """Draw a paragraph on the canvas and return new y position"""
        paragraph.wrapOn(canvas, self.text_width, inch)
        paragraph.drawOn(canvas, x, y - paragraph.height)
        return y - paragraph.height

    def generate_form(self, components: list[FormComponent], output_path: str) -> None:
        """Generate the interactive PDF form"""
        c = canvas.Canvas(output_path, pagesize=letter)
        form = c.acroForm
        current_y = self.height - self.margin

        # Title
        title_para = self.create_paragraph("<b>DPIA Form</b>", self.styles["Title"])
        current_y = self.draw_paragraph(c, title_para, self.margin, current_y) - 20

        def process_component(component: FormComponent) -> None:
            nonlocal current_y

            # Label paragraph
            if component.type == "fieldset":
                label_para = self.create_paragraph(f"<b>{component.label}</b>", self.styles["Heading2"])
            else:
                label_para = self.create_paragraph(f"<b>{component.label}</b>")

            current_y = self.draw_paragraph(c, label_para, self.margin, current_y) - 10

            # Description paragraph (if exists)
            if component.description:
                desc_para = self.create_paragraph(component.description)
                current_y = self.draw_paragraph(c, desc_para, self.margin, current_y) - 10

            # Create form field
            if component.type == "select":
                form.choice(
                    name=component.key,
                    value=component.options[0]["label"] if component.options else "",
                    options=[opt["label"] for opt in component.options] if component.options else [],
                    x=self.margin,
                    y=current_y - 40,
                    width=self.text_width,
                    height=30,
                )
                current_y -= 50
            elif component.type == "textarea":
                form.textfield(name=component.key, x=self.margin, y=current_y - 60, width=self.text_width, height=50)
                current_y -= 70
            elif component.type == "textfield":
                form.textfield(name=component.key, x=self.margin, y=current_y - 40, width=self.text_width, height=30)
                current_y -= 50
            elif component.type == "fieldset" and component.components:
                for sub_component in component.components:
                    process_component(sub_component)
                current_y -= 20  # Add spacing between fieldsets

            # Start new page if running out of space
            if current_y < 100:
                c.showPage()
                current_y = self.height - self.margin

        # Process all components
        for component in components:
            process_component(component)

        c.save()


def create_interactive_form(
    form_definitions: list[dict[str, Any]],
    form_steps: list[dict[str, Any]],
    output_path: str,
) -> None:
    """Convenience function to create an interactive PDF form"""
    components = FormParser.parse_form_definition(form_definitions)
    steps = StepParser.parse_form_definition(form_steps)
    components = order_components(steps, components)
    generator = InteractivePDFGenerator()
    generator.generate_form(components, output_path)
