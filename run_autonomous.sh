#!/usr/bin/env fish
# Launch AlleyBot in autonomous mode

echo "🤖 Starting AlleyBot Autonomous Mode..."
echo ""

# Activate virtual environment and run
source venv/bin/activate.fish
python autonomous_mode.py
