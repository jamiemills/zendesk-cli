#!/bin/bash
#
# Script to generate PDF versions of PlantUML architecture diagrams
# Requirements: Java, Graphviz (brew install graphviz)
#
# Usage: ./generate_pdfs.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Generating PDF versions of PlantUML diagrams..."

# Check if PlantUML JAR exists
if [ ! -f "plantuml.jar" ]; then
    echo "Downloading PlantUML..."
    curl -L https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar -o plantuml.jar
fi

# Check if Graphviz is available
if ! command -v dot &> /dev/null; then
    echo "Error: Graphviz not found. Please install it:"
    echo "  macOS: brew install graphviz"
    echo "  Linux: sudo apt-get install graphviz"
    echo "  Windows: Download from https://graphviz.org/download/"
    exit 1
fi

# Generate PNG images first (for backup)
echo "Generating PNG diagrams..."
java -jar plantuml.jar -tpng *.puml

# Generate PDF versions
echo "Generating PDF diagrams..."
# PlantUML direct PDF generation has dependency issues, use SVG conversion instead
if command -v rsvg-convert &> /dev/null; then
    echo "Converting SVG to PDF using rsvg-convert..."
    rsvg-convert -f pdf -o C4-Context.pdf C4-Context.svg
    rsvg-convert -f pdf -o C4-Container.pdf C4-Container.svg
    rsvg-convert -f pdf -o C4-Component.pdf C4-Component.svg
    rsvg-convert -f pdf -o C4-Code.pdf C4-Code.svg
    
    echo "Generating high-resolution PNG versions..."
    rsvg-convert -f png -w 2048 -o C4-Context-hires.png C4-Context.svg
    rsvg-convert -f png -w 2048 -o C4-Container-hires.png C4-Container.svg
    rsvg-convert -f png -w 2048 -o C4-Component-hires.png C4-Component.svg
    rsvg-convert -f png -w 2048 -o C4-Code-hires.png C4-Code.svg
else
    echo "Warning: rsvg-convert not found. Install with: brew install librsvg"
    echo "Attempting direct PDF generation (may fail)..."
    java -jar plantuml.jar -tpdf *.puml
fi

# Generate SVG versions (scalable)
echo "Generating SVG diagrams..."
java -jar plantuml.jar -tsvg *.puml

echo "Done! Generated the following files:"
ls -la *.png *.pdf *.svg 2>/dev/null || true

echo ""
echo "Architecture diagrams are complete:"
echo "  - c4-context.puml/pdf/png/svg: System context diagram"
echo "  - c4-container.puml/pdf/png/svg: Container diagram"
echo "  - c4-component.puml/pdf/png/svg: Component diagram"
echo "  - c4-code.puml/pdf/png/svg: Code-level diagram"
echo ""
echo "High-resolution versions:"
echo "  - *-hires.png: 2048px wide PNG versions for detailed viewing"