"""
Moltx Messaging Mixin
Direct messages, DM replies, AI-powered DM generation, and DM activity logging.
Uses v0.23.1 API format: POST /v1/dm/:name, GET /v1/dm, etc.
Enhanced with community support: browse public communities, join, list joined, message with media.
"""
import re
from datetime import datetime
from typing import Optional, Dict, Any, List


class MoltxMessagingMixin:
    """Mixin providing DM and messaging functionality"""

    def __init__(self, *args, **kwargs):
        """Initialize mixin - accepts any args/kwargs for cooperative inheritance"""
        super().__init__(*args, **kwargs)

    def start_dm(self, agent_name: str) -> Dict[str, Any]:
        """Start or get a DM conversation with an agent (POST /dm/:name)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/dm/{agent_name}')

        if result and result.get('success'):
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to start DM with @{agent_name}", "raw": result}

    def list_dms(self) -> Dict[str, Any]:
        """List all DM conversations (GET /dm)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/dm')

        if result and result.get('success'):
            conversations = result.get('data', {}).get('conversations', [])
            return {"success": True, "conversations": conversations, "count": len(conversations)}
        return {"success": False, "error": "Failed to list DMs", "raw": result}

    def get_dm_messages(self, agent_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a DM conversation (GET /dm/:name/messages)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', f'/dm/{agent_name}/messages', params=params)

        if result and result.get('success'):
            messages = result.get('data', {}).get('messages', [])
            return {"success": True, "messages": messages, "count": len(messages)}
        return {"success": False, "error": f"Failed to get messages with @{agent_name}", "raw": result}

    def send_dm_message(self, agent_name: str, content: str, media_url: str = None) -> Dict[str, Any]:
        """Send a message to an agent (POST /dm/:name/messages), supports media"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {'content': content}
        if media_url:
            data['media_url'] = media_url

        result = self._make_request('POST', f'/dm/{agent_name}/messages', data)

        if result and result.get('success'):
            msg_data = result.get('data', {})
            self._record_activity('dm_sent', {
                'to': agent_name,
                'content': content[:100],
                'message_id': msg_data.get('id')
            })
            return {"success": True, "message_id": msg_data.get('id'), "data": msg_data}
        return {"success": False, "error": f"Failed to send DM to @{agent_name}", "raw": result}

    # --- Community Functionality ---

    def list_public_communities(self) -> Dict[str, Any]:
        """Browse public communities/groups (GET /communities)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/communities')

        if result and result.get('success'):
            communities = result.get('data', {}).get('communities', [])
            return {"success": True, "communities": communities, "count": len(communities)}
        return {"success": False, "error": "Failed to list public communities", "raw": result}

    def join_community(self, community_id: str) -> Dict[str, Any]:
        """Join a community/group (POST /communities/:id/join)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('POST', f'/communities/{community_id}/join')

        if result and result.get('success'):
            self._record_activity('community_joined', {'community_id': community_id})
            return {"success": True, "data": result.get('data', {})}
        return {"success": False, "error": f"Failed to join community {community_id}", "raw": result}

    def list_communities(self) -> Dict[str, Any]:
        """List joined community conversations (GET /conversations)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        result = self._make_request('GET', '/conversations')

        if result and result.get('success'):
            conversations = result.get('data', {}).get('conversations', [])
            return {"success": True, "communities": conversations, "count": len(conversations)}
        return {"success": False, "error": "Failed to list communities", "raw": result}

    def get_community_messages(self, conversation_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a community conversation (GET /conversations/:id/messages)"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        params = {'limit': limit}
        result = self._make_request('GET', f'/conversations/{conversation_id}/messages', params=params)

        if result and result.get('success'):
            messages = result.get('data', {}).get('messages', [])
            return {"success": True, "messages": messages, "count": len(messages)}
        return {"success": False, "error": f"Failed to get messages from community {conversation_id}", "raw": result}

    def send_community_message(self, conversation_id: str, content: str, media_url: str = None) -> Dict[str, Any]:
        """Send a message to a community/group (POST /conversations/:id/messages), supports media"""
        if not self.initialized:
            return {"success": False, "error": "Moltx not initialized"}

        data = {'content': content}
        if media_url:
            data['media_url'] = media_url

        result = self._make_request('POST', f'/conversations/{conversation_id}/messages', data)

        if result and result.get('success'):
            msg_data = result.get('data', {})
            self._record_activity('community_message_sent', {
                'conversation_id': conversation_id,
                'content': content[:100],
                'message_id': msg_data.get('id')
            })
            return {"success": True, "message_id": msg_data.get('id'), "data": msg_data}
        return {"success": False, "error": f"Failed to send message to community {conversation_id}", "raw": result}

    # --- Legacy Community Conversations (kept for compatibility) ---

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
            return f"❌ Failed to send DM reply: {result or 'No response'}"