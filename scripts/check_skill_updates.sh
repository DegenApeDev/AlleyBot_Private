#!/bin/bash
# Check for skill.md updates from platforms
# Usage: ./scripts/check_skill_updates.sh

set -e

PLATFORMS=(
    "clawbr:https://clawbr.org/skill.md"
    "moltx:https://moltx.io/skill.md"
    "moltbook:https://moltbook.com/skill.md"
    "moltchan:https://moltchan.org/skill.md"
    "moltroad:https://moltroad.com/skill.md"
    "moltbit:https://moltbit.space/skill.md"
)

UPDATES_FOUND=0

echo "🔍 Checking for skill.md updates..."
echo ""

for platform_info in "${PLATFORMS[@]}"; do
    IFS=':' read -r platform url <<< "$platform_info"
    skill_path="skills/$platform/SKILL.md"
    
    if [ ! -f "$skill_path" ]; then
        echo "❌ $platform: No local skill.md found"
        echo "   Run: ./scripts/add_platform_skill.sh $platform $url"
        echo ""
        continue
    fi
    
    # Download remote and compare
    remote=$(curl -s "$url" 2>/dev/null || echo "")
    
    if [ -z "$remote" ]; then
        echo "⚠️  $platform: Could not fetch from $url"
        continue
    fi
    
    # Check if different
    if ! diff -q "$skill_path" <(echo "$remote") >/dev/null 2>&1; then
        echo "🆕 $platform: Update available!"
        
        # Get version info if available
        local_version=$(grep -i "version" "$skill_path" 2>/dev/null | head -1 || echo "unknown")
        remote_version=$(echo "$remote" | grep -i "version" 2>/dev/null | head -1 || echo "unknown")
        
        echo "   Local:  $local_version"
        echo "   Remote: $remote_version"
        echo "   To update:"
        echo "     cp $skill_path skills/$platform/references/SKILL.backup.md"
        echo "     curl -s $url > $skill_path"
        echo "     git diff $skill_path"
        echo ""
        UPDATES_FOUND=$((UPDATES_FOUND + 1))
    else
        echo "✅ $platform: Up to date"
    fi
done

echo ""
if [ $UPDATES_FOUND -eq 0 ]; then
    echo "All platforms are up to date!"
else
    echo "Found $UPDATES_FOUND platform(s) with updates available"
fi
