#!/usr/bin/env python3
"""
Script to generate PDF versions of documentation files.
This can be run independently of PlantUML/Graphviz dependencies.
"""

import os
import sys
from pathlib import Path

def generate_html_from_markdown(md_file: Path) -> str:
    """Convert markdown to HTML using simple replacements."""
    content = md_file.read_text()
    
    # Simple markdown to HTML conversion
    html = content
    
    # Headers
    html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
    html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
    html = html.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
    html = html.replace('#### ', '<h4>').replace('\n', '</h4>\n', 1)
    
    # Code blocks
    lines = html.split('\n')
    in_code_block = False
    result_lines = []
    
    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                result_lines.append('</pre>')
                in_code_block = False
            else:
                result_lines.append('<pre><code>')
                in_code_block = True
        elif line.startswith('- '):
            result_lines.append(f'<li>{line[2:]}</li>')
        else:
            result_lines.append(line)
    
    html = '\n'.join(result_lines)
    
    # Wrap in basic HTML structure
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{md_file.stem}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3, h4 {{ color: #333; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

def main():
    """Generate HTML versions of markdown documentation for PDF conversion."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_docs_pdf.py <markdown_file>")
        print("Example: python generate_docs_pdf.py README.md")
        print("\nThis script converts a single markdown file to HTML for PDF conversion.")
        print("Use only when needed - HTML files should not be committed to the repository.")
        return
    
    md_file = Path(sys.argv[1])
    
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return
    
    print(f"Converting {md_file} to HTML...")
    html_content = generate_html_from_markdown(md_file)
    html_file = md_file.with_suffix('.html')
    
    html_file.write_text(html_content)
    print(f"Generated: {html_file}")
    
    print("\nTo convert to PDF:")
    print("1. Open the HTML file in a browser and print to PDF")
    print("2. Use wkhtmltopdf: wkhtmltopdf file.html file.pdf")
    print("3. Use pandoc: pandoc -f html -t pdf file.html -o file.pdf")
    print(f"\nRemember to delete {html_file} after conversion!")

if __name__ == "__main__":
    main()