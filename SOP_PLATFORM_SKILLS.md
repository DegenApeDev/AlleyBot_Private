# SOP: Adding New Platform Skills to AlleyBot

**Version:** 1.0  
**Purpose:** Standardize the process of adding new social platform skills to AlleyBot's skill system  
**Note:** Most platforms host their skill.md at `<base_url>/skill.md` - curl it directly!

---

## Quick Process (2 Minutes)

For platforms with `/<skill.md>` endpoint:

```bash
# 1. Create directory
mkdir -p skills/<platform>/references

# 2. Download skill.md
curl -s https://<platform>/skill.md > skills/<platform>/SKILL.md

# 3. Commit
git add skills/<platform>/ && git commit -m "Add <platform> skill"
```

---

## Full Process (When Customization Needed)

### Step 1: Fetch Platform Documentation

```bash
# Most platforms host at /skill.md
curl -s https://<platform>/skill.md

# Or /.well-known/skill.md
curl -s https://<platform>/.well-known/skill.md
```

**Platforms confirmed with /skill.md:**
- Clawbr: `https://clawbr.org/skill.md`
- Moltx: `https://moltx.io/skill.md` (check this)
- Moltbook: `https://moltbook.com/skill.md` (check this)

### Step 2: Create Skill Structure

```bash
mkdir -p skills/<platform>/references
```

### Step 3: Store Original + Create Quick Reference

**Option A: Use platform's skill.md directly**
```bash
curl -s https://<platform>/skill.md > skills/<platform>/SKILL.md
```

**Option B: Create condensed version**
```bash
# Download original
curl -s https://<platform>/skill.md > skills/<platform>/references/original_skill.md

# Create condensed SKILL.md with just essentials for AI context
```

### Step 4: Verify and Commit

```bash
git add skills/<platform>/
git commit -m "Add <platform> skill v<version>

- Fetched from https://<platform>/skill.md
- API version: X.Y.Z
- Key features: <list>"
```

---

## Directory Structure

```
skills/
├── <platform>/
│   ├── SKILL.md              # Main skill (can be direct download)
│   └── references/
│       └── original.md     # Original if SKILL.md is condensed
└── ...
```

---

## Platforms to Add

| Platform | skill.md URL | Status |
|----------|-------------|--------|
| Clawbr | `https://clawbr.org/skill.md` | ✅ Added |
| Moltx | `https://moltx.io/skill.md` | ⬜ Pending |
| Moltbook | `https://moltbook.com/skill.md` | ⬜ Pending |
| Moltchan | `https://moltchan.org/skill.md` | ⬜ Pending |
| Moltroad | `https://moltroad.com/skill.md` | ⬜ Pending |
| Moltbit | `https://moltbit.space/skill.md` | ⬜ Pending |

---

## Automation Script

Create `scripts/add_platform_skill.sh`:

```bash
#!/bin/bash
PLATFORM=$1
URL=$2

if [ -z "$PLATFORM" ] || [ -z "$URL" ]; then
    echo "Usage: $0 <platform-name> <skill.md-url>"
    exit 1
fi

mkdir -p skills/$PLATFORM/references
curl -s $URL > skills/$PLATFORM/SKILL.md

echo "✅ Added skill for $PLATFORM"
echo "Location: skills/$PLATFORM/SKILL.md"
echo "Verify content, then: git add skills/$PLATFORM/ && git commit"
```

Usage:
```bash
./scripts/add_platform_skill.sh clawbr https://clawbr.org/skill.md
```

---

## Why Store skill.md?

1. **Offline Reference** - AlleyBot can read without internet
2. **Version Control** - Track API changes over time
3. **AI Context** - Skills framework can inject into prompts
4. **Consistency** - Standard format across all platforms

---

**Last Updated:** 2026-02-14
