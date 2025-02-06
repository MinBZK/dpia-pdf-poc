import os
from typing import Any, ClassVar

from pdfrw import IndirectPdfDict, PdfName, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from parsers import FormComponent, FormParser, StepParser


class InteractivePDFGenerator:
    """Generates interactive PDF forms using paragraphs"""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter
        self.margin = 50
        self.text_width = self.width - 2 * self.margin

    def _create_paragraph(self, text: str, style: Any | None = None) -> Paragraph:  # noqa
        """Create a paragraph with optional styling"""
        if style is None:
            style = self.styles["Normal"]
        p = Paragraph(text, style)
        return p

    def _draw_paragraph(self, canvas: canvas.Canvas, paragraph: Paragraph, x: float, y: float) -> float:
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
        title_para = self._create_paragraph("<b>DPIA Form</b>", self.styles["Title"])
        current_y = self._draw_paragraph(c, title_para, self.margin, current_y) - 20

        def process_component(component: FormComponent) -> None:
            nonlocal current_y

            # Label paragraph
            if component.type == "fieldset":
                label_para = self._create_paragraph(f"<b>{component.label}</b>", self.styles["Heading2"])
            else:
                label_para = self._create_paragraph(f"<b>{component.label}</b>")

            current_y = self._draw_paragraph(c, label_para, self.margin, current_y) - 10

            # Description paragraph (if exists)
            if component.description:
                desc_para = self._create_paragraph(component.description)
                current_y = self._draw_paragraph(c, desc_para, self.margin, current_y) - 10

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


class PDFJavaScriptManager:
    ANNOT_KEYS: ClassVar = {"annots": PdfName.Annots, "field": PdfName.T, "javascript": PdfName.AA, "blur": PdfName.Bl}

    @staticmethod
    def create_autofill_js(source_field: str, target_field: str) -> str:
        return f"""
        var sourceField = this.getField("{source_field}");
        var targetField = this.getField("{target_field}");
        if (targetField === null) {{
            app.alert("Target field not found!");
        }} else {{
            targetField.value = sourceField.value;
        }}
        """

    def add_javascript(self, input_pdf: str, output_pdf: str, field_connections: list[tuple[str, str]]) -> None:
        """Add JavaScript functionality to PDF form fields"""
        pdf = PdfReader(input_pdf)

        # Create JavaScript actions for connected fields
        js_actions = {
            source: IndirectPdfDict(JS=self.create_autofill_js(source, target), S=PdfName.JavaScript)
            for source, target in field_connections
        }

        # Apply JavaScript to form fields
        for page in pdf.pages:
            if self.ANNOT_KEYS["annots"] not in page:
                continue

            for annotation in page[self.ANNOT_KEYS["annots"]]:
                field_name = str(annotation[self.ANNOT_KEYS["field"]]).strip("()'\"")
                print(f"Found field name: {field_name}")

                if field_name in js_actions:
                    print(f"Attaching JavaScript to field: {field_name}")
                    if self.ANNOT_KEYS["javascript"] not in annotation:
                        annotation[self.ANNOT_KEYS["javascript"]] = IndirectPdfDict()
                    annotation[self.ANNOT_KEYS["javascript"]][self.ANNOT_KEYS["blur"]] = js_actions[field_name]

        PdfWriter(output_pdf, trailer=pdf).write()


def create_interactive_form(
    form_definitions: list[dict[str, Any]],
    form_steps: list[dict[str, Any]],
    output_path: str,
) -> None:
    """Create an interactive PDF form with JavaScript functionality."""

    # Parse and order form components.
    components = FormParser.parse_form_definition(form_definitions)
    steps = StepParser.parse_form_definition(form_steps)
    ordered_components = [
        components_dict[step_comp.id]
        for step in sorted(steps, key=lambda s: s.index)
        for step_comp in step.components
        if (step_comp.id in (components_dict := {comp.id: comp for comp in components}))
    ]

    # Generate form.
    temp_pfd_name = "temp_output.pdf"
    generator = InteractivePDFGenerator()
    generator.generate_form(ordered_components, temp_pfd_name)

    # Add JavaScript.
    js_manager = PDFJavaScriptManager()
    js_manager.add_javascript(
        temp_pfd_name,
        output_path,
        [
            ("categoriePersoonsgegevens21", "categoriePersoonsgegevens31"),
            ("categoriePersoonsgegevens22", "categoriePersoonsgegevens32"),
            ("categoriePersoonsgegevens23", "categoriePersoonsgegevens33"),
        ],
    )

    # Cleanup temporary file.
    os.remove(temp_pfd_name)
