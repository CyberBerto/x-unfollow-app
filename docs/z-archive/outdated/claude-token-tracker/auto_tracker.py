#!/usr/bin/env python3
"""Auto-start estimation tracker when starting Claude sessions."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

class AutoEstimationTracker:
    def __init__(self, project_folder="/Users/bob/Documents/projects/x-unfollow-app"):
        self.project_folder = Path(project_folder)
        self.tracker_folder = Path("/Users/bob/Documents/Duh Vault/X Unfollow App/07-TOOLS/claude-token-tracker")
        self.session_log = self.tracker_folder / "current_session.json"
        
    def start_session(self):
        """Initialize a new Claude session with estimation tracking."""
        print("📊 Starting Claude session with estimation tracking...")
        
        # Create session metadata
        session_data = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "project_folder": str(self.project_folder),
            "tracking_method": "estimation",
            "estimation_log": []
        }
        
        # Save session info
        with open(self.session_log, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"📊 Session ID: {session_data['session_id']}")
        print(f"📁 Project: {self.project_folder}")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print("\n" + "="*50)
        print("Estimation tracking ready!")
        print("📊 Automatic workflow estimation active")
        print("📋 Batch summaries every 3-5 exchanges")  
        print("📈 Session summary on completion")
        print("⚠️  Estimates are 2-5x under actual usage")
        print("="*50 + "\n")
        
        return session_data['session_id']
    
    def end_session(self):
        """End session and show estimation summary."""
        if not self.session_log.exists():
            print("❌ No active session found.")
            return
        
        with open(self.session_log, 'r') as f:
            session_data = json.load(f)
        
        session_id = session_data['session_id']
        print(f"🏁 Ending estimation session: {session_id}")
        
        # Generate standardized filename
        session_filename = self._generate_session_filename(session_data)
        
        # Show estimation summary
        estimation_log_file = self.tracker_folder / "estimation_log.json"
        if estimation_log_file.exists():
            print("📊 Generating session summary...")
            try:
                # Import and use estimation tracker
                sys.path.append(str(self.tracker_folder))
                from estimation_tracker import get_session_summary
                
                summary = get_session_summary()
                print(summary)
                
                print(f"\n📁 Suggested filename: {session_filename}")
                print("\n📌 Next steps:")
                print("1. Run: python obsidian_integration.py")
                print("2. Apply 2-5x multiplier for realistic usage estimates")
                print("3. Update INDEX-Chronological.md with session entry")
                print("4. Update Obsidian Token Usage Tracker with session totals")
                        
            except Exception as e:
                print(f"❌ Summary generation error: {e}")
        else:
            print("📊 No estimation data found - session may not have been used")
        
        # Clean up session file
        self.session_log.unlink()
        print(f"\n🎯 Estimation session {session_id} completed!")
    
    def _generate_session_filename(self, session_data):
        """Generate standardized filename following naming conventions."""
        date_time = datetime.fromisoformat(session_data['start_time'])
        date_str = date_time.strftime("%Y%m%d_%H%M")
        
        # Detect phase and type (basic detection - can be enhanced)
        phase = "Phase39"  # Default for current work
        work_type = "Development"  # Default type
        
        # Could add more sophisticated detection based on session data
        filename = f"Session-{date_str}-{phase}-{work_type}.md"
        return filename

def main():
    tracker = AutoEstimationTracker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--end":
        tracker.end_session()
    else:
        tracker.start_session()

if __name__ == "__main__":
    main()