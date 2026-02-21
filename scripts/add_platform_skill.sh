#!/bin/bash
# Add Platform Skill Script
# Usage: ./scripts/add_platform_skill.sh <platform-name> <skill.md-url>

set -e

PLATFORM=$1
URL=$2

if [ -z "$PLATFORM" ] || [ -z "$URL" ]; then
    echo "Usage: $0 <platform-name> <skill.md-url>"
    echo "Example: $0 clawbr https://clawbr.org/skill.md"
    exit 1
fi

SKILL_DIR="skills/$PLATFORM"

if [ -d "$SKILL_DIR" ]; then
    echo "⚠️  Skill directory already exists: $SKILL_DIR"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

mkdir -p "$SKILL_DIR/references"

echo "📥 Downloading skill.md from $URL..."
if curl -s "$URL" > "$SKILL_DIR/SKILL.md"; then
    echo "✅ Downloaded successfully"
else
    echo "❌ Failed to download from $URL"
    exit 1
fi

# Check if content looks valid
if [ ! -s "$SKILL_DIR/SKILL.md" ]; then
    echo "❌ Downloaded file is empty"
    exit 1
fi

if ! head -1 "$SKILL_DIR/SKILL.md" | grep -q "^---"; then
    echo "⚠️  Warning: File doesn't start with YAML frontmatter (---)"
    echo "   This might not be a valid skill.md file"
fi

LINES=$(wc -l < "$SKILL_DIR/SKILL.md")
SIZE=$(du -h "$SKILL_DIR/SKILL.md" | cut -f1)

echo ""
echo "✅ Skill added for $PLATFORM"
echo "   Location: $SKILL_DIR/SKILL.md"
echo "   Lines: $LINES, Size: $SIZE"
echo ""
echo "Next steps:"
echo "   1. Review: cat $SKILL_DIR/SKILL.md"
echo "   2. Commit: git add $SKILL_DIR/ && git commit -m \"Add $PLATFORM skill\""
