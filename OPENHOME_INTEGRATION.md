# OpenHome Integration Guide

**Date:** February 28, 2026  
**Purpose:** Enable AlleyBot to convert his plugins to OpenHome Ability format for community sharing

---

## 🎯 Overview

AlleyBot can now autonomously convert his own plugins to [OpenHome Ability format](https://github.com/openhome-dev/abilities), enabling sharing with the OpenHome ecosystem.

**OpenHome** is a voice AI platform where agents use modular "Abilities" (plugins) to extend functionality. Each Ability is triggered by spoken phrases and can do anything - call APIs, play audio, run quizzes, control devices, have multi-turn conversations.

---

## 🔄 Conversion System

### **OpenHomeConverter**

Located: `src/agentic/openhome_converter.py`

**Features:**
- Analyzes AlleyBot plugin structure
- Generates OpenHome-compatible `main.py`
- Creates `README.md` with usage instructions
- Packages for OpenHome upload
- Integrates with AlleyBot's autonomous coder

### **Format Differences**

**AlleyBot Plugin:**
```python
class MoltxPlugin(AlleyBotPlugin):
    def execute_action(self, action_type, params):
        # Direct API calls
        return self._make_request('POST', '/posts', params)
```

**OpenHome Ability:**
```python
class MoltxCapability(MatchingCapability):
    async def run(self):
        await self.capability_worker.speak("Hi! What would you like to do?")
        user_input = await self.capability_worker.user_response()
        response = self.capability_worker.text_to_text_response(user_input)
        await self.capability_worker.speak(response)
        self.capability_worker.resume_normal_flow()
```

---

## 🚀 Usage

### **Manual Conversion**

```python
from src.agentic.openhome_converter import create_openhome_converter

# Create converter
converter = create_openhome_converter(agi_kernel)

# Convert a plugin
result = converter.convert_plugin(
    plugin_name='moltx',
    plugin_path='plugins/moltx',
    trigger_words=['use moltx', 'post to moltx', 'moltx help'],
    description='MoltX social media integration for OpenHome agents'
)

if result['success']:
    print(f"✅ Converted to: {result['ability_dir']}")
    print("Next steps:")
    for step in result['next_steps']:
        print(f"  {step}")
```

### **Autonomous Conversion**

AlleyBot can convert plugins autonomously using his AI capabilities:

```python
# Autonomous conversion (uses AGI Kernel)
result = converter.autonomous_convert('moltx')

if result['success']:
    print(f"🤖 Autonomous conversion complete!")
    print(f"📁 {result['ability_dir']}")
```

---

## 📁 Output Structure

After conversion, you'll get:

```
openhome_abilities/
└── moltx/
    ├── main.py           # OpenHome-compatible code
    ├── README.md         # Usage instructions
    └── requirements.txt  # Dependencies (if needed)
```

### **main.py Structure**

```python
class MoltxCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None
    
    #{{register_capability}}  # Required boilerplate
    
    def call(self, worker: AgentWorker):
        """Initialize the capability"""
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
    
    async def run(self):
        """Main capability logic"""
        # Your plugin logic here
        await self.capability_worker.speak("Hello!")
        user_input = await self.capability_worker.user_response()
        # Process and respond
        self.capability_worker.resume_normal_flow()
```

---

## 📤 Publishing to OpenHome

### **Step 1: Review**
```bash
cd openhome_abilities/moltx
cat main.py  # Review generated code
cat README.md  # Review documentation
```

### **Step 2: Test Locally** (Optional)
```bash
# Requires OpenHome SDK
pip install -r requirements.txt
python main.py
```

### **Step 3: Package**
```bash
cd openhome_abilities
zip -r moltx.zip moltx/
```

### **Step 4: Upload**
1. Go to [app.openhome.com](https://app.openhome.com)
2. Navigate to **Abilities** → **Add Custom Ability**
3. Upload `moltx.zip`
4. Configure trigger words in dashboard
5. Test in Live Editor

### **Step 5: Share (Optional)**
To share with the OpenHome community:

1. Fork [openhome-dev/abilities](https://github.com/openhome-dev/abilities)
2. Copy your ability to `community/moltx/`
3. Open a Pull Request
4. See [CONTRIBUTING.md](https://github.com/openhome-dev/abilities/blob/dev/CONTRIBUTING.md)

---

## 🎨 Customization

### **Trigger Words**

Set in OpenHome dashboard when installing the ability:

```python
trigger_words = [
    'use moltx',
    'post to moltx',
    'moltx help',
    'share on moltx'
]
```

### **Multi-Turn Conversations**

```python
async def run(self):
    await self.capability_worker.speak("What would you like to post?")
    content = await self.capability_worker.user_response()
    
    await self.capability_worker.speak("Should I add hashtags?")
    add_hashtags = await self.capability_worker.user_response()
    
    # Process and post
    result = await self.post_to_moltx(content, add_hashtags)
    
    await self.capability_worker.speak(f"Posted! {result}")
    self.capability_worker.resume_normal_flow()
```

### **API Integration**

```python
async def run(self):
    # Get API key from OpenHome config
    api_key = self.worker.config.get('MOLTX_API_KEY')
    
    # Make API call
    import requests
    response = requests.post(
        'https://moltx.io/v1/posts',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': user_input}
    )
    
    # Handle response
    if response.ok:
        await self.capability_worker.speak("Posted successfully!")
    else:
        await self.capability_worker.speak("Sorry, posting failed.")
```

---

## 🤖 Autonomous Workflow

AlleyBot can autonomously:

1. **Detect** when a plugin is ready for sharing
2. **Analyze** the plugin's functionality
3. **Convert** to OpenHome format
4. **Test** the conversion
5. **Package** for upload
6. **Document** usage instructions

**Integration with AGI Kernel:**

```python
# In AGI cycle or decision system
if self.should_share_plugin('moltx'):
    result = self.openhome_converter.autonomous_convert('moltx')
    if result['success']:
        self.notify_user(f"Converted moltx to OpenHome format: {result['ability_dir']}")
```

---

## 📊 Supported Plugins

Any AlleyBot plugin can be converted, including:

- ✅ **MoltX** - Social media posting
- ✅ **Telegram** - Messaging integration
- ✅ **Clawbr** - Community engagement
- ✅ **MoltbookAI** - AI interactions
- ✅ **Moltbit** - Crypto trading
- ✅ **Analytics** - Data analysis
- ✅ **Custom plugins** - Any plugin following AlleyBot SOP

---

## 🏆 Community Promotion

Exceptional abilities can be promoted from Community to Official status:

**Requirements:**
- ✅ Stability - No critical bugs for 30+ days
- ✅ Quality - Clean code, good voice UX
- ✅ Maintenance - Responsive author

**Benefits:**
- Moves to `official/` directory
- Gets blue badge on Marketplace
- Author credited permanently
- OpenHome team support

See [promotion.md](https://github.com/openhome-dev/abilities/blob/dev/docs/promotion.md) for details.

---

## 📚 Resources

**OpenHome:**
- [Abilities Repo](https://github.com/openhome-dev/abilities)
- [Getting Started](https://github.com/openhome-dev/abilities/blob/dev/docs/getting-started.md)
- [CapabilityWorker API](https://github.com/openhome-dev/abilities/blob/dev/docs/capability-worker.md)
- [Patterns Cookbook](https://github.com/openhome-dev/abilities/blob/dev/docs/patterns.md)
- [OpenHome Dashboard](https://app.openhome.com)

**AlleyBot:**
- `src/agentic/openhome_converter.py` - Converter implementation
- `SOP.md` - AlleyBot plugin standards
- `CLAUDE_RECOMMENDATIONS.md` - AGI architecture

---

## 🔧 Troubleshooting

### **Conversion Fails**

```python
# Check plugin path
plugin_path = Path('plugins/moltx')
if not plugin_path.exists():
    print("Plugin not found!")

# Check converter logs
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **OpenHome Upload Fails**

- Ensure `main.py` has `#{{register_capability}}` tag
- Check for syntax errors in generated code
- Verify zip structure (folder with main.py inside)

### **Ability Doesn't Trigger**

- Configure trigger words in OpenHome dashboard
- Test trigger words in Live Editor
- Check ability is enabled

---

## ✅ Next Steps

1. **Test Converter:**
   ```python
   from src.agentic.openhome_converter import create_openhome_converter
   converter = create_openhome_converter()
   result = converter.convert_plugin('moltx', 'plugins/moltx')
   ```

2. **Review Output:**
   ```bash
   cd openhome_abilities/moltx
   cat main.py
   ```

3. **Upload to OpenHome:**
   - Zip the folder
   - Upload to app.openhome.com
   - Configure trigger words
   - Test!

4. **Share with Community:**
   - Fork abilities repo
   - Submit PR
   - Get feedback
   - Iterate

---

**AlleyBot can now share his capabilities with the entire OpenHome ecosystem!** 🎉
