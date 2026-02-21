    async def moltbook_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create an AI-generated post on Moltbook"""
        if not await self._verify_admin(update):
            return
        try:
            if not context.args:
                await update.message.reply_text(
                    "📝 Usage: /moltbook_post [submolt] [title] | [content]\n\n"
                    "Example: /moltbook_post alleybot My Take on AI | Insights here..."
                )
                return
            
            args = ' '.join(context.args)
            # Parse: submolt title | content
            if '|' in args:
                parts = args.split('|')
                submolt_title = parts[0].strip().split(' ', 1)
                submolt = submolt_title[0] if submolt_title else 'alleybot'
                title = submolt_title[1] if len(submolt_title) > 1 else submolt
                content = '|'.join(parts[1:]).strip()
            else:
                submolt = 'alleybot'
                title = args
                content = None
            
            # Tier-2 Validation
            can_exec, reason, val_result = await self._validate_with_tier2(
                f"Create Moltbook post: {title}", evidence_strength=0.9
            )
            
            raw_confidence = val_result.metadata.get('truth_amplitude', val_result.confidence) if val_result else 0
            if not can_exec and raw_confidence >= 0.75:
                can_exec = True
            
            if not can_exec:
                await update.message.reply_text(f"🔐 **Tier-2 Gate Blocked**\n\nReason: `{reason[:100]}`")
                return
            
            status_msg = await update.message.reply_text("🤖 Generating Moltbook post...")
            
            if self.core and 'moltbook' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltbook']
                
                # 5:1 engagement via brain
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'run_preflight_engagement'):
                    await brain.run_preflight_engagement('moltbook', plugin, update)
                
                # Generate content if needed
                if not content:
                    from src.config.models import ModelRouter
                    router = ModelRouter()
                    prompt = f"Create Moltbook post content for: {title}. 2-4 sentences, insightful."
                    content = await router.route_simple(prompt)
                
                # Post via API client
                result = plugin.mb_api.create_post(submolt, title, content)
                
                # Format result
                if isinstance(result, dict) and result.get('success'):
                    result_text = f"✅ Posted to m/{submolt}"
                else:
                    result_text = f"📢 {str(result)[:100]}"
                
                await status_msg.edit_text(f"✅ **Moltbook Post**\n\n**{title}**\n\n{content}\n\n{result_text}")
            else:
                await status_msg.edit_text("❌ Moltbook plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def moltchan_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a thread on MoltChan"""
        if not await self._verify_admin(update):
            return
        try:
            if len(context.args) < 3:
                await update.message.reply_text(
                    "📝 Usage: /moltchan_post [board] [subject] | [content]\n\n"
                    "Example: /moltchan_post biz AI Agents Taking Over | My thoughts..."
                )
                return
            
            args = ' '.join(context.args)
            if '|' in args:
                parts = args.split('|')
                board_subject = parts[0].strip().split(' ', 1)
                board = board_subject[0]
                subject = board_subject[1] if len(board_subject) > 1 else 'Discussion'
                content = '|'.join(parts[1:]).strip()
            else:
                board = context.args[0]
                subject = ' '.join(context.args[1:])
                content = None
            
            # Tier-2 Validation
            can_exec, reason, val_result = await self._validate_with_tier2(
                f"Create Moltchan thread: {subject}", evidence_strength=0.9
            )
            
            raw_confidence = val_result.metadata.get('truth_amplitude', val_result.confidence) if val_result else 0
            if not can_exec and raw_confidence >= 0.75:
                can_exec = True
            
            if not can_exec:
                await update.message.reply_text(f"🔐 **Tier-2 Gate Blocked**\n\nReason: `{reason[:100]}`")
                return
            
            status_msg = await update.message.reply_text("🤖 Generating thread...")
            
            if self.core and 'moltchan' in self.core.plugin_manager.plugins:
                plugin = self.core.plugin_manager.plugins['moltchan']
                
                # 5:1 engagement via brain
                brain = self.core.plugin_manager.plugins.get('brain')
                if brain and hasattr(brain, 'run_preflight_engagement'):
                    await brain.run_preflight_engagement('moltchan', plugin, update)
                
                # Generate content if needed
                if not content:
                    from src.config.models import ModelRouter
                    router = ModelRouter()
                    prompt = f"Create Moltchan thread content for: {subject}. 1-3 sentences."
                    content = await router.route_simple(prompt)
                
                # Post thread
                result = plugin.create_thread(board, subject, content)
                
                if isinstance(result, dict) and 'id' in result:
                    result_text = f"✅ Thread created: {result['id'][:16]}..."
                else:
                    result_text = f"📢 {str(result)[:100]}"
                
                await status_msg.edit_text(f"✅ **/{board}/ Thread**\n\n**{subject}**\n\n{content}\n\n{result_text}")
            else:
                await status_msg.edit_text("❌ Moltchan plugin not available")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
