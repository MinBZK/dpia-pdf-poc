import os

def generate_mermaid_html(mermaid_code):
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mermaid Diagram</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js"></script>
</head>
<body>
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>
"""
    
    # Clean the mermaid code - remove any extra whitespace
    mermaid_code = mermaid_code.strip()
    
    # Generate the HTML content
    html_content = html_template.format(mermaid_code=mermaid_code)
    
    # Write to file
    with open('mermaid_diagram.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("HTML file generated as 'mermaid_diagram.html'")

# Your mermaid code
mermaid_code = """
graph TD
    A(Herziene vragen DPIA) --> B[Input Standaard]
    B --> C[Invulbare formulier DPIA]
    C --> D[Output Standaard]
    E(Datamodel J&V) --> B
    F(Begrippenkader) --> B
    G(Deelbaar) --> C
    H(Installatieloos) --> C
    I(Gebruiksvriendelijk) --> C
"""

generate_mermaid_html(mermaid_code)