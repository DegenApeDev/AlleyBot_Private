# AlleyBot TODO - Next 10 Days

## Priority 1: Critical Bugs & Stability (Days 1-3)
- [ ] Test all fixes on VPS and verify no more URL encoding errors
- [ ] Manually fix Moltx display name back to "AlleyBot" (use debug script)
- [ ] Monitor logs for any remaining JSON parsing errors
- [ ] Verify skill generation works correctly with Grok AI
- [ ] Test all plugin commands (Moltx, Moltbook, MoltChan, MoltRoad)
- [ ] Ensure no duplicate registrations happening

## Priority 2: Agent Personality & Behavior (Days 4-6)
- [ ] Create SOUL.md file defining AlleyBot's personality and values
- [ ] Define clear boundaries for autonomous actions
- [ ] Establish communication style guidelines
- [ ] Set posting frequency and engagement rules
- [ ] Document decision-making framework for agent

## Priority 3: Platform Optimization (Days 7-9)
- [ ] Optimize Moltx posting schedule and engagement
- [ ] Test Moltbook post creation and content quality
- [ ] Verify MoltChan thread creation and replies
- [ ] Test MoltRoad marketplace listings
- [ ] Create platform-specific posting strategies

## Priority 4: Documentation & Maintenance (Day 10)
- [ ] Update README with latest features and setup instructions
- [ ] Document all plugin APIs and their current status
- [ ] Create troubleshooting guide for common issues
- [ ] Write deployment guide for VPS
- [ ] Document credential management best practices

## Completed ✅
- [x] Fix Moltx API endpoint URL encoding issues
- [x] Update Moltx plugin to match skill.md and heartbeat.md
- [x] Fix Grok nested JSON response parsing
- [x] Prevent raw JSON display in posts and outputs
- [x] Fix Moltbook API method errors (get_feed, get_stats)
- [x] Add community support to Moltx (search, join, leave, message)
- [x] Add parameter validation across all plugins
- [x] Prevent invalid profile updates on Moltx

## Future Skills (After Platforms Stable)
- [ ] Cross-platform content syndication
- [ ] Automated community management
- [ ] Market analysis and trend reporting
- [ ] Content scheduling and optimization
- [ ] Analytics dashboard for performance
- [ ] Advanced AI interaction patterns

## Notes
- All current fixes are in `agentic-enhancements-v2` branch
- Need to merge to main after VPS testing
- Keep monitoring for new API changes from platforms
- Consider rate limiting strategies to avoid bans
