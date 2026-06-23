#!/bin/bash

# Define paths
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
SEO_PLIST="$LAUNCH_AGENTS_DIR/com.mikke.seo_automation.plist"
NOTE_PLIST="$LAUNCH_AGENTS_DIR/com.mikke.note_auto_post.plist"
PROJECT_DIR="/Users/tsukika/Desktop/affiliate-portal"

echo "=== Starting launchd migration ==="

# 1. Create LaunchAgents directory if not exists
mkdir -p "$LAUNCH_AGENTS_DIR"

# 2. Write com.mikke.seo_automation.plist
cat << 'EOF' > "$SEO_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mikke.seo_automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/tsukika/Desktop/affiliate-portal/scripts/seo_automation.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/tsukika/Desktop/affiliate-portal/seo_automation.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/tsukika/Desktop/affiliate-portal/seo_automation.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/tsukika/Desktop/affiliate-portal</string>
</dict>
</plist>
EOF
echo "Created $SEO_PLIST"

# 3. Write com.mikke.note_auto_post.plist
cat << 'EOF' > "$NOTE_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mikke.note_auto_post</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/tsukika/Desktop/affiliate-portal/scripts/note_auto_post.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>9</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>21</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardOutPath</key>
    <string>/Users/tsukika/Desktop/affiliate-portal/note_auto_post.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/tsukika/Desktop/affiliate-portal/note_auto_post.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/tsukika/Desktop/affiliate-portal</string>
</dict>
</plist>
EOF
echo "Created $NOTE_PLIST"

# 4. Load into launchd (unload first just in case)
echo "Loading jobs into launchd..."
launchctl unload "$SEO_PLIST" 2>/dev/null
launchctl load "$SEO_PLIST"
launchctl unload "$NOTE_PLIST" 2>/dev/null
launchctl load "$NOTE_PLIST"

# 5. Remove from crontab to avoid duplicate runs
echo "Cleaning up crontab..."
crontab -l 2>/dev/null | grep -v "seo_automation.py" | grep -v "note_auto_post.py" > /tmp/cron_temp 2>/dev/null
if [ -s /tmp/cron_temp ]; then
    crontab /tmp/cron_temp
else
    # Clear crontab without confirmation prompt
    crontab /dev/null
fi
rm -f /tmp/cron_temp

echo "=== Migration Complete! ==="
