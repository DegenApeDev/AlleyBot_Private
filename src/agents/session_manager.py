"""
Session State Management for AlleyBot
Handles per-session storage, RAG context, and chat history
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class SessionManager:
    """Manages session state and RAG memory"""
    
    def __init__(self, sessions_dir: str = "src/config/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.rag_system = None  # Will be injected with existing RAG
        
    async def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load session state from storage"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if session_file.exists():
                with open(session_file, 'r') as f:
                    session = json.load(f)
                print(f"📂 Loaded session: {session_id}")
                return session
            else:
                # Create new session
                session = {
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat(),
                    "chat_history": [],
                    "context": {},
                    "metadata": {}
                }
                print(f"🆕 Created new session: {session_id}")
                return session
                
        except Exception as e:
            print(f"❌ Failed to load session {session_id}: {e}")
            return {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "chat_history": [],
                "context": {},
                "metadata": {}
            }
    
    async def save_session(self, session_id: str, session: Dict[str, Any]):
        """Persist session state to storage"""
        try:
            session["last_active"] = datetime.now().isoformat()
            session_file = self.sessions_dir / f"{session_id}.json"
            
            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)
            
            print(f"💾 Saved session: {session_id}")
            
        except Exception as e:
            print(f"❌ Failed to save session {session_id}: {e}")
    
    async def get_rag_context(self, session_id: str, query: str, max_tokens: int = 3000) -> str:
        """
        Retrieve relevant RAG context for the query
        Uses hybrid keyword + semantic retrieval
        """
        try:
            if not query:
                return ""
            
            # Use existing RAG system if available
            if self.rag_system:
                context = await self.rag_system.retrieve(query, max_tokens=max_tokens)
                print(f"🧠 Retrieved RAG context: {len(context)} chars")
                return context
            
            # Fallback: load from session chat history
            session = await self.load_session(session_id)
            chat_history = session.get("chat_history", [])
            
            # Get last N messages as context
            recent_messages = chat_history[-5:] if len(chat_history) > 5 else chat_history
            context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_messages
            ])
            
            print(f"📝 Using chat history as context: {len(context)} chars")
            return context
            
        except Exception as e:
            print(f"❌ Failed to get RAG context: {e}")
            return ""
    
    async def update_rag_memory(self, session_id: str, query: str, response: str):
        """Update RAG memory with new interaction"""
        try:
            session = await self.load_session(session_id)
            
            # Add to chat history
            if "chat_history" not in session:
                session["chat_history"] = []
            
            session["chat_history"].append({
                "timestamp": datetime.now().isoformat(),
                "role": "user",
                "content": query
            })
            
            session["chat_history"].append({
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response
            })
            
            # Keep last 50 messages
            if len(session["chat_history"]) > 50:
                session["chat_history"] = session["chat_history"][-50:]
            
            await self.save_session(session_id, session)
            
            # Update RAG system if available
            if self.rag_system:
                await self.rag_system.add_memory(query, response)
            
            print(f"🧠 Updated RAG memory for session: {session_id}")
            
        except Exception as e:
            print(f"❌ Failed to update RAG memory: {e}")
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get full session context including metadata"""
        session = await self.load_session(session_id)
        return session.get("context", {})
    
    async def update_session_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context metadata"""
        session = await self.load_session(session_id)
        session["context"].update(context)
        await self.save_session(session_id, session)
    
    def list_sessions(self) -> List[str]:
        """List all active sessions"""
        try:
            sessions = [f.stem for f in self.sessions_dir.glob("*.json")]
            return sessions
        except Exception as e:
            print(f"❌ Failed to list sessions: {e}")
            return []
    
    async def cleanup_old_sessions(self, days: int = 30):
        """Clean up sessions older than N days"""
        try:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            
            cleaned = 0
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session = json.load(f)
                    
                    last_active = datetime.fromisoformat(session.get("last_active", ""))
                    if last_active < cutoff:
                        session_file.unlink()
                        cleaned += 1
                        
                except Exception as e:
                    print(f"⚠️ Failed to process {session_file}: {e}")
            
            if cleaned > 0:
                print(f"🧹 Cleaned up {cleaned} old sessions")
                
        except Exception as e:
            print(f"❌ Failed to cleanup sessions: {e}")
