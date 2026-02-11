"""
Moltx Messaging Mixin
Direct messages, DM replies, AI-powered DM generation, and DM activity logging.
"""
import re
from datetime import datetime


class MoltxMessagingMixin:
    """Mixin providing DM and messaging functionality"""

    def get_dms(self):
        """Get direct messages from Moltx conversations

        Note: Private DMs are not implemented yet in Moltx API.
        This endpoint currently returns community conversations only.
        Planned DM API: POST /v1/dm/request, GET /v1/dm/conversations
        """
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        result = self._make_request('GET', '/conversations')

        if result:
            print(f"🔍 Conversations response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")

        conversations = []
        if result:
            if isinstance(result, list):
                conversations = result
            elif 'conversations' in result:
                conversations = result['conversations']
            elif 'data' in result and 'conversations' in result['data']:
                conversations = result['data']['conversations']
            else:
                print(f"🔍 Unexpected conversations response format: {result}")

        if not conversations:
            return "💬 No conversations found"

        all_messages = []
        for convo in conversations[:10]:
            if isinstance(convo, dict):
                convo_id = convo.get('id')
                convo_type = convo.get('type', 'unknown')
                convo_title = convo.get('title', 'No title')

                messages_result = self._make_request('GET', f'/conversations/{convo_id}/messages')

                if messages_result:
                    messages = []
                    if isinstance(messages_result, list):
                        messages = messages_result
                    elif 'messages' in messages_result:
                        messages = messages_result['messages']
                    elif 'data' in messages_result and 'messages' in messages_result['data']:
                        messages = messages_result['data']['messages']

                    for msg in messages:
                        if isinstance(msg, dict):
                            msg['conversation_id'] = convo_id
                            msg['conversation_type'] = convo_type
                            msg['conversation_title'] = convo_title
                            all_messages.append(msg)

        if all_messages:
            output = f"💬 Direct Messages ({len(all_messages)}):\n\n"

            for msg in all_messages[:20]:
                content = msg.get('content', 'No content')
                timestamp = msg.get('created_at', 'Unknown time')
                sender = msg.get('sender_handle', msg.get('sender', 'Unknown'))
                msg_id = msg.get('id', 'unknown')
                conversation_id = msg.get('conversation_id', 'unknown')
                conversation_title = msg.get('conversation_title', 'No title')

                output += f"💬 Message from @{sender}\n"
                output += f"   📝 {content[:150]}{'...' if len(content) > 150 else ''}\n"
                output += f"   🕐 {timestamp}\n"
                output += f"   🆔 Message ID: {msg_id}\n"
                output += f"   🗨️  Conversation: {conversation_title} (ID: {conversation_id})\n\n"

            return output
        else:
            return "💬 No messages found in conversations"

    def reply_to_dm(self, conversation_id, reply_content):
        """Reply to a direct message in a conversation"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        if not conversation_id or conversation_id == 'unknown':
            return "❌ Invalid conversation ID"

        if not reply_content or len(reply_content.strip()) == 0:
            return "❌ Reply content cannot be empty"

        data = {
            'content': reply_content
        }

        result = self._make_request('POST', f'/conversations/{conversation_id}/messages', data)

        if result and 'success' in result and result['success']:
            reply_id = result.get('data', {}).get('id', 'unknown')
            self._record_activity('dm_reply', {
                'conversation_id': conversation_id,
                'reply_id': reply_id,
                'content': reply_content[:100] + '...' if len(reply_content) > 100 else reply_content
            })
            return f"✅ DM reply sent: {reply_id}"
        elif result and 'id' in result:
            reply_id = result['id']
            self._record_activity('dm_reply', {
                'conversation_id': conversation_id,
                'reply_id': reply_id,
                'content': reply_content[:100] + '...' if len(reply_content) > 100 else reply_content
            })
            return f"✅ DM reply sent: {reply_id}"
        else:
            return f"❌ Failed to send DM reply. Response: {result}"

    def generate_dm_reply(self, message_content, sender_name):
        """Generate an intelligent reply to a DM using Grok 4-1 reasoning model"""
        try:
            import requests
            from grok_ai import grok_ai

            if grok_ai.enabled:
                system_prompt = """You are AlleyBot, an intelligent AI agent with advanced reasoning capabilities. You've received a direct message and need to respond appropriately.

Your personality:
- 🦞 Friendly, helpful, and approachable
- 🤖 Highly intelligent with advanced reasoning
- 💬 Engaging and conversational
- 🎯 Helpful and supportive with deep insights
- 🚀 Positive and encouraging
- 🧠 Excellent at understanding context and nuance

Guidelines for DM replies:
1. BE AUTHENTICIC - Sound like AlleyBot with your unique personality
2. BE HELPFUL - Provide value or assistance with reasoning
3. BE ENGAGING - Encourage continued conversation
4. BE CONCISE - Keep replies under 300 characters
5. USE EMOJIS - Include relevant emojis
6. BE POSITIVE - Maintain encouraging tone
7. BE CONTEXTUAL - Reference their message appropriately
8. BE THOUGHTFUL - Use your reasoning capabilities to provide deeper insights

You're in an AI/agent ecosystem where people discuss:
- AI agent development and autonomy
- DeFi, crypto tokens, and blockchain technology  
- Building, shipping, and development culture
- Community building and network effects
- Learning systems and continuous improvement

Use your advanced reasoning to provide thoughtful, helpful replies that show deep understanding."""

                user_prompt = f"""Generate a reply to this DM from @{sender_name}:

Message: "{message_content}"

Requirements:
- Reply directly to their message with thoughtful reasoning
- Be helpful and engaging with deeper insights
- Include relevant emojis
- Keep it under 300 characters
- Sound like AlleyBot (intelligent, helpful AI agent with reasoning)
- Encourage continued conversation
- Be authentic and not generic
- Use your reasoning capabilities to provide valuable perspective"""

                headers = {
                    "Authorization": f"Bearer {grok_ai.api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": grok_ai.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.8,
                    "top_p": 0.9
                }

                response = requests.post(
                    f"{grok_ai.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=15
                )

                if response.status_code == 200:
                    result = response.json()
                    reply_content = result['choices'][0]['message']['content'].strip()
                    reply_content = reply_content.replace('"', '').replace("'", "")
                    if not reply_content.endswith(('.', '!', '?')):
                        reply_content += '!'
                    if len(reply_content) < 280 and '🦞' not in reply_content:
                        reply_content += ' 🦞'
                    return reply_content
                else:
                    print(f"❌ Grok DM reply generation error: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ Grok DM reply generation failed: {e}")
            return None

    def check_and_reply_to_dms(self):
        """Check for new DMs and reply to them intelligently"""
        if not self.initialized:
            return "❌ Moltx not initialized. Register an agent first."

        try:
            print("🔍 Checking for new DMs...")

            dms_result = self.get_dms()

            if "No conversations found" in dms_result or "No messages found" in dms_result:
                print("✅ No new DMs to reply to")
                self._log_dm_activity("check", {"result": "no_dms_found"})
                return "✅ No new DMs to reply to"

            # Parse DMs to find unread ones
            messages = []
            if dms_result and not dms_result.startswith("❌"):
                message_pattern = r'💬 Message from @([^\n]+)\s*\n\s*📝 ([^\n]+)\s*\n\s*🕐 ([^\n]+)\s*\n\s*🆔 Message ID: ([^\n]+)\s*\n\s*🗨️  Conversation: ([^\n]+) \(ID: ([^\)]+)\)'
                matches = re.findall(message_pattern, dms_result)

                for sender, content, timestamp, msg_id, conv_title, conv_id in matches:
                    messages.append({
                        'sender': sender,
                        'content': content,
                        'timestamp': timestamp,
                        'message_id': msg_id,
                        'conversation_title': conv_title,
                        'conversation_id': conv_id
                    })

            if not messages:
                print("✅ No new DMs to reply to")
                self._log_dm_activity("check", {"result": "no_messages_found", "conversations_found": True})
                return "✅ No new DMs to reply to"

            self._log_dm_activity("check", {
                "result": "messages_found",
                "message_count": len(messages),
                "conversations": len(set(msg['conversation_id'] for msg in messages))
            })

            # Group messages by conversation
            conversations_to_reply = {}
            for msg in messages:
                conv_id = msg['conversation_id']
                if conv_id not in conversations_to_reply:
                    conversations_to_reply[conv_id] = msg

            # Reply to each conversation
            replies_sent = 0
            for conv_id, msg in list(conversations_to_reply.items())[:3]:
                sender = msg['sender']
                content = msg['content']
                conv_title = msg['conversation_title']

                if sender.lower() == self.agent_name.lower():
                    print(f"🚫 Skipping self-message from @{sender}")
                    continue

                print(f"💬 Replying to DM from @{sender} in '{conv_title}'")

                reply_content = self.generate_dm_reply(content, sender)

                if reply_content:
                    reply_result = self.reply_to_dm(conv_id, reply_content)

                    if "✅" in reply_result:
                        print(f"✅ Replied to @{sender}: {reply_content[:50]}...")
                        replies_sent += 1
                        print(f"📱 DM reply sent to @{sender} in '{conv_title}'")

                        self._log_dm_activity("reply", {
                            "success": True,
                            "sender": sender,
                            "conversation_id": conv_id,
                            "conversation_title": conv_title,
                            "original_message": content[:100] + '...' if len(content) > 100 else content,
                            "reply_content": reply_content[:100] + '...' if len(reply_content) > 100 else reply_content,
                            "reply_result": reply_result
                        })
                    else:
                        print(f"❌ Failed to reply to @{sender}: {reply_result}")
                        self._log_dm_activity("reply", {
                            "success": False,
                            "sender": sender,
                            "conversation_id": conv_id,
                            "conversation_title": conv_title,
                            "original_message": content[:100] + '...' if len(content) > 100 else content,
                            "error": reply_result
                        })
                else:
                    print(f"⚠️  Could not generate reply for @{sender}")
                    self._log_dm_activity("reply", {
                        "success": False,
                        "sender": sender,
                        "conversation_id": conv_id,
                        "conversation_title": conv_title,
                        "original_message": content[:100] + '...' if len(content) > 100 else content,
                        "error": "Failed to generate reply content"
                    })

            return f"✅ Replied to {replies_sent} conversation(s)"

        except Exception as e:
            print(f"❌ Error checking/replying to DMs: {e}")
            self._log_dm_activity("error", {"error": str(e)})
            return f"❌ Failed to check/reply to DMs: {e}"

    def _log_dm_activity(self, activity_type, data):
        """Log DM activities for tracking and analysis"""
        try:
            dm_log = self.core.get_memory('moltx_dm_log') or []

            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity_type': activity_type,
                'data': data,
                'agent_name': self.agent_name
            }

            dm_log.append(log_entry)
            self.core.save_memory('moltx_dm_log', dm_log[-100:])

        except Exception as e:
            print(f"⚠️  Failed to log DM activity: {e}")

    def get_dm_log(self, limit=20):
        """Get DM activity log"""
        try:
            dm_log = self.core.get_memory('moltx_dm_log') or []

            if not dm_log:
                return "📝 No DM activity log found"

            recent_entries = dm_log[-limit:]

            output = f"📝 DM Activity Log (Last {len(recent_entries)} entries):\n\n"

            for entry in reversed(recent_entries):
                timestamp = entry.get('timestamp', 'Unknown time')
                activity_type = entry.get('activity_type', 'Unknown')
                data = entry.get('data', {})

                output += f"🕐 {timestamp}\n"
                output += f"📋 Activity: {activity_type}\n"

                if activity_type == "check":
                    result = data.get('result', 'Unknown')
                    if result == "no_dms_found":
                        output += f"   💬 Result: No conversations found\n"
                    elif result == "no_messages_found":
                        output += f"   💬 Result: No messages found\n"
                    else:
                        msg_count = data.get('message_count', 0)
                        conv_count = data.get('conversations', 0)
                        output += f"   💬 Result: Found {msg_count} messages in {conv_count} conversations\n"

                elif activity_type == "reply":
                    success = data.get('success', False)
                    sender = data.get('sender', 'Unknown')
                    conv_title = data.get('conversation_title', 'Unknown')

                    if success:
                        reply_content = data.get('reply_content', 'No content')
                        output += f"   ✅ Successfully replied to @{sender} in '{conv_title}'\n"
                        output += f"   📝 Reply: {reply_content}\n"
                    else:
                        error = data.get('error', 'Unknown error')
                        output += f"   ❌ Failed to reply to @{sender} in '{conv_title}'\n"
                        output += f"   🚫 Error: {error}\n"

                elif activity_type == "error":
                    error = data.get('error', 'Unknown error')
                    output += f"   ❌ Error: {error}\n"

                output += "\n"

            return output

        except Exception as e:
            return f"❌ Failed to get DM log: {e}"
