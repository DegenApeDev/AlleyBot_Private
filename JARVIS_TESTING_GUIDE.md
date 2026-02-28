# JARVIS Systems Testing Guide

**Date:** February 28, 2026  
**Systems to Test:** 9 JARVIS systems (Phases 1-3)

---

## 🚀 Quick Start

### **1. Restart AlleyBot**

```bash
cd /home/alley/AlleyBot
python alleybot_core.py
```

**Look for these startup messages:**
```
✅ Conversational Memory integrated (multi-turn dialogue active)
✅ Intent Recognizer integrated (deep intent understanding active)
✅ Dialogue Manager integrated (JARVIS-style conversation active)
✅ Predictive Suggestions integrated (proactive assistance active)
✅ Contextual Awareness integrated (situational understanding active)
✅ Opportunity Detector integrated (opportunity awareness active)
✅ Personality Engine integrated (consistent character active)
✅ Emotional Intelligence integrated (empathy active)
✅ Adaptive Response integrated (JARVIS-style responses active)
```

If you see all 9 ✅ messages, the systems are loaded!

---

## 📋 Testing Checklist

### **Phase 1: Natural Conversation** (3 systems)

- [ ] Conversational Memory tracks multi-turn dialogue
- [ ] Intent Recognition detects user intent
- [ ] Dialogue Manager handles complex conversations

### **Phase 2: Proactive Intelligence** (3 systems)

- [ ] Predictive Suggestions anticipates needs
- [ ] Contextual Awareness understands user state
- [ ] Opportunity Detector spots opportunities

### **Phase 3: Personality & Emotion** (3 systems)

- [ ] Personality Engine applies consistent character
- [ ] Emotional Intelligence detects emotions
- [ ] Adaptive Response generates perfect responses

---

## 🧪 Test 1: Conversational Memory

### **What to Test:**
Multi-turn dialogue tracking and context preservation

### **How to Test:**

**Via Telegram:**
```
You: "Post about DeFi"
AlleyBot: [Response]

You: "What about yield farming?"  ← Follow-up
AlleyBot: [Should understand this refers to DeFi]

You: "Make it technical"  ← Another follow-up
AlleyBot: [Should know we're still talking about DeFi yield farming]
```

**Via Python Console:**
```python
# Access conversational memory
memory = core.agi_kernel.conversational_memory

# Add a turn
memory.add_turn(
    user_input="Post about DeFi",
    agent_response="I'll create a DeFi post",
    context={'platform': 'telegram'}
)

# Add follow-up
memory.add_turn(
    user_input="What about yield farming?",
    agent_response="Focusing on yield farming",
    context={'platform': 'telegram'}
)

# Check if follow-up detected
is_followup = memory.is_follow_up("What about yield farming?")
print(f"Follow-up detected: {is_followup}")  # Should be True

# Get conversation context
context = memory.get_conversation_context()
print(f"Recent turns: {len(context)}")

# Get summary
summary = memory.get_conversation_summary()
print(summary)
```

**Expected Results:**
- ✅ Follow-ups are detected
- ✅ Context is maintained across turns
- ✅ Topic shifts are identified
- ✅ Conversation summary shows history

---

## 🧪 Test 2: Intent Recognition

### **What to Test:**
Deep understanding of user intent and emotion

### **How to Test:**

**Via Python Console:**
```python
# Access intent recognizer
intent = core.agi_kernel.intent_recognizer

# Test different intents
test_cases = [
    "This isn't working!",  # Frustrated
    "It worked! Finally!",  # Excited
    "I don't understand",   # Confused
    "Thanks so much!",      # Grateful
    "Post about DeFi",      # Command
    "What's trending?",     # Question
]

for user_input in test_cases:
    result = intent.recognize_intent(user_input)
    print(f"\nInput: {user_input}")
    print(f"Intent: {result.intent_type.value}")
    print(f"Emotion: {result.emotion.value}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Reasoning: {result.reasoning}")
```

**Expected Results:**
- ✅ Commands detected as "command"
- ✅ Questions detected as "question"
- ✅ Emotions detected correctly (frustrated, excited, etc.)
- ✅ Confidence scores are reasonable (>50%)

---

## 🧪 Test 3: Dialogue Manager

### **What to Test:**
Multi-turn conversation orchestration

### **How to Test:**

**Via Python Console:**
```python
# Access dialogue manager
dialogue = core.agi_kernel.dialogue_manager

# Process a vague request (should ask for clarification)
response = dialogue.process_turn("Post something")

print(f"Type: {response['type']}")  # Should be 'clarification'
print(f"Message: {response['message']}")

# Provide clarification
response = dialogue.process_turn("About DeFi")

print(f"Type: {response['type']}")  # Should be 'response'
print(f"Intent: {response['intent']}")
```

**Expected Results:**
- ✅ Vague requests trigger clarification
- ✅ Follow-ups are handled with context
- ✅ State tracking works (listening, clarifying, etc.)

---

## 🧪 Test 4: Predictive Suggestions

### **What to Test:**
Proactive suggestion generation

### **How to Test:**

**Via Python Console:**
```python
# Access predictive suggestions
predict = core.agi_kernel.predictive_suggestions

# Generate suggestions
suggestions = predict.generate_proactive_suggestions(limit=3)

for i, suggestion in enumerate(suggestions, 1):
    print(f"\n{i}. {suggestion.suggestion_type}")
    print(f"   Message: {suggestion.message}")
    print(f"   Confidence: {suggestion.confidence:.0%}")
    print(f"   Priority: {suggestion.priority}/10")
```

**Via AGI Cycle:**
Wait for the AGI cycle to run and check logs for:
```
💡 Predictive suggestion: [message]
```

**Expected Results:**
- ✅ Suggestions are generated based on patterns
- ✅ Morning briefings appear in morning hours
- ✅ Goal progress suggestions appear
- ✅ Timing-based suggestions trigger

---

## 🧪 Test 5: Contextual Awareness

### **What to Test:**
User state detection and interruption appropriateness

### **How to Test:**

**Via Python Console:**
```python
# Access contextual awareness
context = core.agi_kernel.contextual_awareness

# Get current context
snapshot = context.get_current_context()

print(f"User State: {snapshot.user_state.value}")
print(f"Can Interrupt: {snapshot.can_interrupt}")
print(f"Reasoning: {snapshot.reasoning}")
print(f"Time Context: {snapshot.time_context}")

# Record activity (simulates user doing something)
context.record_activity("coding")

# Check state again
snapshot = context.get_current_context()
print(f"New State: {snapshot.user_state.value}")  # Might be 'focused'
```

**Expected Results:**
- ✅ User state is detected (available, busy, focused, idle, away)
- ✅ Interruption appropriateness is assessed
- ✅ Time context is tracked
- ✅ Activity history is maintained

---

## 🧪 Test 6: Opportunity Detector

### **What to Test:**
Opportunity detection across platforms

### **How to Test:**

**Via Python Console:**
```python
# Access opportunity detector
detector = core.agi_kernel.opportunity_detector

# Detect opportunities
opportunities = detector.detect_opportunities()

for opp in opportunities:
    print(f"\n{opp.opportunity_type}: {opp.title}")
    print(f"Description: {opp.description}")
    print(f"Impact: {opp.potential_impact}")
    print(f"Action: {opp.action_suggestion}")
    print(f"Confidence: {opp.confidence:.0%}")

# Get summary
summary = detector.get_opportunity_summary()
print(summary)
```

**Expected Results:**
- ✅ Trending topics are detected
- ✅ High-engagement posts are identified
- ✅ Mentions are caught
- ✅ Timing opportunities are found

---

## 🧪 Test 7: Personality Engine

### **What to Test:**
Consistent character across responses

### **How to Test:**

**Via Python Console:**
```python
# Access personality engine
personality = core.agi_kernel.personality_engine

# Test personality application
test_responses = [
    ("Task completed successfully.", {'situation': 'achievement'}),
    ("I found an error.", {'situation': 'error'}),
    ("Good morning!", {'hour': 9}),
]

for base_response, context in test_responses:
    result = personality.apply_personality(base_response, context)
    print(f"\nBase: {base_response}")
    print(f"With Personality: {result}")

# Check personality profile
profile = personality.get_personality_summary()
print(profile)
```

**Expected Results:**
- ✅ Responses have personality touches
- ✅ Tone adapts to situation
- ✅ Character is consistent
- ✅ Traits are applied (helpful, witty, confident, etc.)

---

## 🧪 Test 8: Emotional Intelligence

### **What to Test:**
Emotion detection and empathetic responses

### **How to Test:**

**Via Python Console:**
```python
# Access emotional intelligence
emotions = core.agi_kernel.emotional_intelligence

# Test emotion detection
test_inputs = [
    ("This isn't working! I've tried 3 times!", {'repeated_failures': True}),
    ("It worked! Finally!", {'achievement': True}),
    ("I don't understand what you mean", {}),
    ("Thanks so much, that really helped!", {}),
]

for user_input, context in test_inputs:
    state = emotions.detect_emotion(user_input, context)
    
    print(f"\nInput: {user_input}")
    print(f"Emotion: {state.primary_emotion.value}")
    print(f"Intensity: {state.intensity:.0%}")
    print(f"Confidence: {state.confidence:.0%}")
    print(f"Triggers: {state.triggers}")
    
    # Test response adaptation
    adapted = emotions.adjust_response_style(
        state.primary_emotion,
        "I can help with that."
    )
    print(f"Adapted Response: {adapted}")

# Get emotional summary
summary = emotions.get_emotional_summary()
print(summary)
```

**Expected Results:**
- ✅ Emotions are detected accurately
- ✅ Intensity is calculated
- ✅ Responses are adapted to emotion
- ✅ Patterns are tracked over time

---

## 🧪 Test 9: Adaptive Response

### **What to Test:**
Perfectly-tuned responses combining all systems

### **How to Test:**

**Via Python Console:**
```python
from src.agentic.adaptive_response import ResponseContext

# Access adaptive response
adaptive = core.agi_kernel.adaptive_response

# Test different scenarios
scenarios = [
    {
        'user_input': "This isn't working!",
        'base_message': "I found the issue.",
        'context': ResponseContext(
            user_input="This isn't working!",
            user_emotion='frustrated',
            user_state='busy',
            situation='error'
        )
    },
    {
        'user_input': "It worked!",
        'base_message': "Great job!",
        'context': ResponseContext(
            user_input="It worked!",
            user_emotion='excited',
            user_state='available',
            situation='achievement'
        )
    },
]

for scenario in scenarios:
    response = adaptive.generate_response(
        scenario['base_message'],
        scenario['context']
    )
    
    print(f"\nUser: {scenario['user_input']}")
    print(f"Base: {scenario['base_message']}")
    print(f"Adaptive: {response}")
```

**Expected Results:**
- ✅ Responses combine personality + emotion + context
- ✅ Tone matches user emotion
- ✅ Proactive elements added when appropriate
- ✅ Feels natural and human-like

---

## 🔄 Integration Test: Full Conversation Flow

### **Test Complete JARVIS Experience:**

**Via Telegram:**

```
You: "Hey AlleyBot"
AlleyBot: [Greeting with personality]

You: "This isn't working!"
AlleyBot: [Empathetic response, detects frustration]

You: "The MoltX post failed"
AlleyBot: [Understands context, offers help]

You: "Can you fix it?"
AlleyBot: [Clarifies what needs fixing]

You: "The API error"
AlleyBot: [Takes action, provides update]

You: "Thanks!"
AlleyBot: [Acknowledges gratitude, offers next steps]
```

**Expected Flow:**
1. ✅ Greeting uses personality
2. ✅ Frustration is detected
3. ✅ Context is maintained across turns
4. ✅ Clarification is requested when needed
5. ✅ Empathy is shown
6. ✅ Proactive suggestions offered

---

## 📊 Monitoring & Metrics

### **Check Logs for JARVIS Activity:**

```bash
# Watch for JARVIS system activity
tail -f /path/to/alleybot.log | grep -E "💭|🎯|😊|💡|📍|🎭|❤️|🎨"
```

**Look for:**
- `💭` Conversational Memory activity
- `🎯` Intent Recognition
- `😊` Emotional Intelligence
- `💡` Predictive Suggestions
- `📍` Contextual Awareness
- `🎯` Opportunity Detection
- `🎭` Personality Engine
- `🎨` Adaptive Response

---

## 🐛 Common Issues & Fixes

### **Issue: Systems not loading**
```bash
# Check if AGI Kernel initialized
grep "AGI Kernel ready" logs

# Check for initialization errors
grep "ERROR" logs | grep -i jarvis
```

### **Issue: Conversational memory not working**
```python
# Verify memory is initialized
print(core.agi_kernel.conversational_memory)  # Should not be None

# Check turn count
summary = core.agi_kernel.conversational_memory.get_conversation_summary()
print(f"Turns: {summary['turn_count']}")
```

### **Issue: Emotions not detected**
```python
# Test with obvious emotion
result = core.agi_kernel.emotional_intelligence.detect_emotion(
    "This is terrible! Nothing works!",
    {'situation': 'error'}
)
print(f"Emotion: {result.primary_emotion.value}")  # Should be 'frustrated'
```

---

## ✅ Success Criteria

**Phase 1: Natural Conversation**
- [ ] Multi-turn conversations work
- [ ] Follow-ups are detected
- [ ] Intent is recognized accurately
- [ ] Clarifications are requested when needed

**Phase 2: Proactive Intelligence**
- [ ] Suggestions are generated
- [ ] User state is detected
- [ ] Opportunities are spotted
- [ ] Timing is appropriate

**Phase 3: Personality & Emotion**
- [ ] Responses have personality
- [ ] Emotions are detected
- [ ] Tone adapts to situation
- [ ] Feels human-like

**Overall:**
- [ ] All 9 systems load on startup
- [ ] No errors in logs
- [ ] Conversations feel natural
- [ ] AlleyBot feels like JARVIS

---

## 🚀 Next Steps After Testing

1. **Fix any bugs found**
2. **Tune personality traits** if needed
3. **Adjust emotion detection** thresholds
4. **Add metrics/monitoring** for production
5. **Move to Phase 4** (Multi-Modal) or Platform Expansion

---

**Happy Testing!** 🎉
