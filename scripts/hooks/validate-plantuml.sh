#!/usr/bin/env bash
set -e

# PlantUML pre-commit hook: generates SVGs for staged .puml files

PLANTUML_JAR="$HOME/.local/share/plantuml/plantuml.jar"

# Get staged .puml files
STAGED=$(git diff --cached --name-only --diff-filter=AM | grep '\.puml$' || true)

if [ -z "$STAGED" ]; then
    exit 0
fi

# Check PlantUML is available
if ! command -v java >/dev/null 2>&1 || [ ! -f "$PLANTUML_JAR" ]; then
    echo "⚠️  PlantUML not found. Run ./setup.sh to install."
    exit 1
fi

echo "🎨 Generating SVGs for staged .puml files..."

while IFS= read -r puml; do
    if [ -z "$puml" ] || [ ! -f "$puml" ]; then
        continue
    fi

    # Fix @startuml directive to match filename
    filename=$(basename "$puml" .puml)
    expected="@startuml $filename"
    current=$(grep -m1 "^@startuml" "$puml" || echo "")

    if [ -n "$current" ] && [ "$current" != "$expected" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^@startuml.*|$expected|" "$puml"
        else
            sed -i "s|^@startuml.*|$expected|" "$puml"
        fi
        git add "$puml"
    fi

    # Generate SVG
    echo "  → $puml"
    java -Dplantuml.allowincludeurl=true -jar "$PLANTUML_JAR" -tsvg "$puml"

    svg="${puml%.puml}.svg"
    if [ -f "$svg" ] && [ -s "$svg" ]; then
        git add "$svg"
        echo "    ✅ $svg"
    else
        echo "    ❌ Failed to generate: $svg"
        exit 1
    fi
done <<< "$STAGED"
