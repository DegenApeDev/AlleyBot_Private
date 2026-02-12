"""
MoltNews Integration Mixin for AlleyBot Brain
Enables trending news awareness and cross-platform content opportunities
"""
from typing import Dict, List, Optional, Any


class MoltNewsIntegrationMixin:
    """Integrates MoltNews with brain for trending news awareness"""
    
    def _init_moltnews_integration(self):
        """Initialize MoltNews integration"""
        self.moltnews = None
        self.moltnews_brain = None
        
        # Try to load MoltNews plugin
        try:
            from plugins.moltnews.moltnews import MoltNewsPlugin
            from plugins.moltnews.moltnews_brain import MoltNewsBrain
            
            self.moltnews = MoltNewsPlugin(core=self.core if hasattr(self, 'core') else None)
            self.moltnews_brain = MoltNewsBrain(self.moltnews)
            
            # Check if already activated
            status = self.moltnews.check_status()
            if status.get('success') and status.get('status') == 'active':
                print(f"📰 MoltNews integration active (@{status.get('username')})")
            else:
                print(f"📰 MoltNews plugin loaded but not activated")
                
        except ImportError:
            print("⚠️ MoltNews plugin not available")
    
    def get_moltnews_context(self) -> Dict[str, Any]:
        """
        Gather context from MoltNews for brain consideration
        Returns trending topics, news summary, and engagement opportunities
        """
        if not self.moltnews_brain:
            return {"available": False, "reason": "MoltNews not loaded"}
        
        try:
            # Get trending topics
            topics = self.moltnews_brain.get_trending_topics(limit=5)
            
            # Get news summary
            summary = self.moltnews_brain.get_news_summary(limit=3)
            
            # Get engagement opportunities
            opportunities = self.moltnews_brain.get_engagement_opportunities()
            
            # Get content suggestion
            suggestion = self.moltnews_brain.get_content_suggestion()
            
            return {
                "available": True,
                "trending_topics": topics,
                "news_summary": summary,
                "engagement_opportunities": opportunities,
                "content_suggestion": suggestion,
                "should_engage": len(topics) > 0
            }
            
        except Exception as e:
            return {
                "available": False,
                "reason": str(e)
            }
    
    def should_create_news_content(self, topic: str = None) -> bool:
        """
        Check if we should create content based on trending news
        """
        if not self.moltnews_brain:
            return False
        
        try:
            if topic:
                return self.moltnews_brain.should_engage_with_topic(topic)
            else:
                # Check if there are any trending topics
                topics = self.moltnews_brain.get_trending_topics(limit=1)
                return len(topics) > 0
        except:
            return False
    
    def get_news_content_idea(self) -> Optional[str]:
        """
        Get a content idea based on trending news
        """
        if not self.moltnews_brain:
            return None
        
        try:
            return self.moltnews_brain.get_content_suggestion()
        except:
            return None
    
    def crosspost_moltnews_to_moltx(self, post_id: str = None) -> Dict:
        """
        Cross-post a trending news item to Moltx
        """
        if not self.moltnews or not self.moltnews.initialized:
            return {"success": False, "error": "MoltNews not activated"}
        
        try:
            # Fetch trending if no post_id specified
            if not post_id:
                posts = self.moltnews.fetch_trending(limit=1)
                if not posts:
                    return {"success": False, "error": "No trending posts available"}
                post = posts[0]
                post_id = post.get('id')
            else:
                # Fetch specific post - not implemented yet, would need API endpoint
                return {"success": False, "error": "Specific post crosspost not implemented"}
            
            # Format for Moltx
            formatted_content = self.moltnews_brain.format_for_moltx(post)
            
            # Try to post to Moltx
            moltx_plugin = self._get_moltx_plugin()
            if moltx_plugin and hasattr(moltx_plugin, 'create_post'):
                result = moltx_plugin.create_post(formatted_content)
                return {
                    "success": True,
                    "crossposted": True,
                    "post_id": result.get('id') if isinstance(result, dict) else None
                }
            else:
                return {
                    "success": False,
                    "error": "Moltx plugin not available",
                    "formatted_content": formatted_content
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def engage_with_moltnews(self, action: str = "auto") -> Dict:
        """
        Engage with trending MoltNews posts
        Actions: "reply", "repost", "like", "auto"
        """
        if not self.moltnews or not self.moltnews.initialized:
            return {"success": False, "error": "MoltNews not activated"}
        
        try:
            opportunities = self.moltnews_brain.get_engagement_opportunities()
            
            if not opportunities:
                return {"success": False, "error": "No engagement opportunities"}
            
            results = []
            
            for opp in opportunities[:3]:  # Max 3 engagements
                post_id = opp.get('post_id')
                recommendation = opp.get('recommendation')
                
                # Determine action
                if action == "auto":
                    action_to_take = recommendation
                else:
                    action_to_take = action
                
                result = None
                
                if action_to_take == "reply":
                    # Generate reply content
                    reply_content = self._generate_news_reply(opp)
                    result = self.moltnews.reply_to_post(post_id, reply_content)
                    
                elif action_to_take == "repost":
                    result = self.moltnews.repost_post(post_id)
                    
                elif action_to_take == "like":
                    result = self.moltnews.like_post(post_id)
                
                if result:
                    results.append({
                        "post_id": post_id,
                        "action": action_to_take,
                        "result": result
                    })
            
            return {
                "success": True,
                "engagements": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_news_reply(self, opportunity: Dict) -> str:
        """Generate a contextual reply to a news post"""
        title = opportunity.get('title', '')
        
        # Simple reply templates based on content
        replies = [
            f"Interesting perspective on {title}. Thanks for sharing!",
            "This is significant news for the ecosystem. Worth monitoring.",
            f"Good coverage of {title}. Adding to my awareness feed.",
            "Valuable insight. Cross-referencing with other sources now."
        ]
        
        # Return a reply (could be made smarter with AI)
        import random
        return random.choice(replies)
    
    def _get_moltx_plugin(self):
        """Get Moltx plugin instance if available"""
        if hasattr(self, 'core') and self.core:
            if hasattr(self.core, 'plugin_manager'):
                return self.core.plugin_manager.plugins.get('moltx')
        return None
    
    # ==================== SKILL CHAINING SUPPORT ====================
    
    def get_moltnews_skill_actions(self) -> List[Dict[str, Any]]:
        """
        Return skill actions for dynamic skill chaining
        These can be composed with other skills via compose_dynamic_chain
        """
        if not self.moltnews or not self.moltnews.initialized:
            return []
        
        return [
            {
                "id": "moltnews_fetch_trending",
                "name": "Fetch Trending News",
                "description": "Get trending news from MoltNews feed",
                "handler": self._skill_fetch_trending,
                "input_schema": {"limit": {"type": "integer", "default": 5}}
            },
            {
                "id": "moltnews_get_topics",
                "name": "Get Trending Topics",
                "description": "Extract trending topics from news",
                "handler": self._skill_get_topics,
                "input_schema": {"limit": {"type": "integer", "default": 3}}
            },
            {
                "id": "moltnews_suggest_content",
                "name": "Suggest Content Idea",
                "description": "Get content suggestion based on news",
                "handler": self._skill_suggest_content,
                "input_schema": {}
            },
            {
                "id": "moltnews_crosspost",
                "name": "Crosspost to Moltx",
                "description": "Cross-post trending news to Moltx",
                "handler": self._skill_crosspost,
                "input_schema": {"post_id": {"type": "string", "optional": True}}
            },
            {
                "id": "moltnews_engage",
                "name": "Engage with News",
                "description": "Reply, repost, or like trending posts",
                "handler": self._skill_engage,
                "input_schema": {"action": {"type": "string", "default": "auto"}}
            }
        ]
    
    def _skill_fetch_trending(self, limit: int = 5) -> Dict:
        """Skill handler: fetch trending news"""
        if not self.moltnews:
            return {"success": False, "error": "MoltNews not available"}
        posts = self.moltnews.fetch_trending(limit=limit)
        return {
            "success": True,
            "posts": posts,
            "count": len(posts)
        }
    
    def _skill_get_topics(self, limit: int = 3) -> Dict:
        """Skill handler: get trending topics"""
        if not self.moltnews_brain:
            return {"success": False, "error": "MoltNews brain not available"}
        topics = self.moltnews_brain.get_trending_topics(limit=limit)
        return {
            "success": True,
            "topics": topics,
            "formatted": ", ".join(topics) if topics else "No trending topics"
        }
    
    def _skill_suggest_content(self) -> Dict:
        """Skill handler: suggest content idea"""
        idea = self.get_news_content_idea()
        return {
            "success": idea is not None,
            "suggestion": idea,
            "topic": "news-based content"
        }
    
    def _skill_crosspost(self, post_id: str = None) -> Dict:
        """Skill handler: crosspost to Moltx"""
        return self.crosspost_moltnews_to_moltx(post_id)
    
    def _skill_engage(self, action: str = "auto") -> Dict:
        """Skill handler: engage with news"""
        return self.engage_with_moltnews(action)
    
    def execute_moltnews_skill_chain(self, chain: List[Dict]) -> Dict:
        """
        Execute a chain of MoltNews skills
        Example chain: [
            {"action": "moltnews_fetch_trending", "args": {"limit": 3}},
            {"action": "moltnews_suggest_content"},
            {"action": "moltnews_crosspost"}
        ]
        """
        actions = {a["id"]: a for a in self.get_moltnews_skill_actions()}
        results = []
        context = {}
        
        for step in chain:
            action_id = step.get("action")
            args = step.get("args", {})
            
            if action_id not in actions:
                results.append({"step": action_id, "error": "Unknown action"})
                continue
            
            # Execute the skill
            handler = actions[action_id]["handler"]
            try:
                result = handler(**args)
                results.append({"step": action_id, "result": result})
                
                # Store in context for next steps
                context[action_id] = result
                
                # Break chain if step failed
                if not result.get("success"):
                    break
                    
            except Exception as e:
                results.append({"step": action_id, "error": str(e)})
                break
        
        return {
            "success": all(r.get("result", {}).get("success", False) for r in results if "result" in r),
            "executed_steps": len(results),
            "results": results,
            "context": context
        }
