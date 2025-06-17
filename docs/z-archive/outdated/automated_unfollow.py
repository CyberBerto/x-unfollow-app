#!/usr/bin/env python3
"""
Automated X Unfollow Script
Unfollows users at 15-minute intervals to respect rate limits.
"""

import time
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from api import XAPIClient
from config import CLIENT_ID, CLIENT_SECRET, CALLBACK_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_unfollow.log'),
        logging.StreamHandler()
    ]
)

class AutomatedUnfollower:
    def __init__(self):
        self.client = XAPIClient(CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)
        self.unfollow_queue_file = 'unfollow_queue.json'
        self.state_file = 'unfollow_state.json'
        self.queue = []
        self.state = {
            'last_unfollow_time': 0,
            'total_unfollowed': 0,
            'failed_attempts': 0,
            'current_session_start': time.time()
        }
        self.load_queue()
        self.load_state()
    
    def load_queue(self):
        """Load the unfollow queue from file."""
        try:
            if os.path.exists(self.unfollow_queue_file):
                with open(self.unfollow_queue_file, 'r') as f:
                    self.queue = json.load(f)
                logging.info(f"Loaded {len(self.queue)} users from unfollow queue")
            else:
                logging.info("No existing unfollow queue found")
        except Exception as e:
            logging.error(f"Error loading queue: {str(e)}")
            self.queue = []
    
    def save_queue(self):
        """Save the unfollow queue to file."""
        try:
            with open(self.unfollow_queue_file, 'w') as f:
                json.dump(self.queue, f, indent=2)
            logging.info(f"Saved {len(self.queue)} users to unfollow queue")
        except Exception as e:
            logging.error(f"Error saving queue: {str(e)}")
    
    def load_state(self):
        """Load the automation state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    saved_state = json.load(f)
                    self.state.update(saved_state)
                logging.info("Loaded automation state")
        except Exception as e:
            logging.error(f"Error loading state: {str(e)}")
    
    def save_state(self):
        """Save the automation state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving state: {str(e)}")
    
    def add_users_to_queue(self, usernames):
        """Add users to the unfollow queue."""
        added = 0
        for username in usernames:
            if username not in self.queue:
                self.queue.append(username)
                added += 1
        
        self.save_queue()
        logging.info(f"Added {added} new users to queue. Total queue: {len(self.queue)}")
        return added
    
    def get_rate_limit_info(self):
        """Get current rate limit information."""
        try:
            rate_limits = self.client.get_rate_limit_status(refresh_from_api=True)
            return rate_limits.get('unfollow', {})
        except Exception as e:
            logging.error(f"Error getting rate limits: {str(e)}")
            return {'remaining': 'unknown', 'limit': 'unknown', 'reset_time': 0}
    
    def time_until_next_unfollow(self):
        """Calculate seconds until next unfollow is allowed."""
        current_time = time.time()
        last_unfollow = self.state['last_unfollow_time']
        
        # 15 minutes = 900 seconds
        time_since_last = current_time - last_unfollow
        time_until_next = max(0, 900 - time_since_last)
        
        return time_until_next
    
    def can_unfollow_now(self):
        """Check if we can unfollow now based on rate limits."""
        rate_info = self.get_rate_limit_info()
        time_until_next = self.time_until_next_unfollow()
        
        # Check API rate limits
        if rate_info['remaining'] != 'unknown' and rate_info['remaining'] <= 0:
            return False, f"API rate limit exceeded. Remaining: {rate_info['remaining']}"
        
        # Check our 15-minute timer
        if time_until_next > 0:
            return False, f"Must wait {int(time_until_next)} seconds since last unfollow"
        
        return True, "Ready to unfollow"
    
    def unfollow_next_user(self):
        """Unfollow the next user in the queue."""
        if not self.queue:
            return False, "No users in queue"
        
        can_unfollow, reason = self.can_unfollow_now()
        if not can_unfollow:
            return False, reason
        
        username = self.queue[0]
        
        try:
            # Get user info first (for logging)
            user_id = self.client.resolve_username_to_id(username)
            if not user_id:
                # Remove from queue if user not found
                self.queue.pop(0)
                self.save_queue()
                return False, f"User {username} not found, removed from queue"
            
            # Attempt unfollow
            success = self.client.unfollow_user(self.client.get_user_info()['id'], user_id)
            
            if success:
                # Remove from queue and update state
                self.queue.pop(0)
                self.state['last_unfollow_time'] = time.time()
                self.state['total_unfollowed'] += 1
                
                self.save_queue()
                self.save_state()
                
                logging.info(f"✅ Successfully unfollowed @{username}. Queue remaining: {len(self.queue)}")
                return True, f"Successfully unfollowed @{username}"
            else:
                self.state['failed_attempts'] += 1
                self.save_state()
                logging.error(f"❌ Failed to unfollow @{username}")
                return False, f"Failed to unfollow @{username}"
                
        except Exception as e:
            self.state['failed_attempts'] += 1
            self.save_state()
            error_msg = f"Error unfollowing @{username}: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_status(self):
        """Get current automation status."""
        rate_info = self.get_rate_limit_info()
        time_until_next = self.time_until_next_unfollow()
        can_unfollow, reason = self.can_unfollow_now()
        
        session_duration = time.time() - self.state['current_session_start']
        
        return {
            'queue_length': len(self.queue),
            'next_username': self.queue[0] if self.queue else None,
            'can_unfollow_now': can_unfollow,
            'reason': reason,
            'time_until_next': int(time_until_next),
            'rate_limits': rate_info,
            'stats': {
                'total_unfollowed': self.state['total_unfollowed'],
                'failed_attempts': self.state['failed_attempts'],
                'session_duration_minutes': int(session_duration / 60)
            }
        }
    
    def run_continuous(self, check_interval=60):
        """Run the automation continuously."""
        logging.info("🤖 Starting automated unfollow service...")
        logging.info(f"Check interval: {check_interval} seconds")
        
        while True:
            try:
                if not self.queue:
                    logging.info("⏸️  Queue is empty. Waiting for users to be added...")
                    time.sleep(check_interval)
                    continue
                
                success, message = self.unfollow_next_user()
                
                if success:
                    # Wait 15 minutes before next attempt
                    logging.info(f"⏰ Waiting 15 minutes before next unfollow...")
                    time.sleep(900)  # 15 minutes
                else:
                    if "wait" in message.lower():
                        # Rate limited, wait shorter time
                        wait_time = self.time_until_next_unfollow()
                        if wait_time > 0:
                            logging.info(f"⏰ Rate limited. Waiting {int(wait_time)} seconds...")
                            time.sleep(min(wait_time + 10, check_interval))  # Add 10 second buffer
                        else:
                            time.sleep(check_interval)
                    else:
                        # Other error, wait normal interval
                        time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info("🛑 Received interrupt signal. Stopping automation...")
                break
            except Exception as e:
                logging.error(f"💥 Unexpected error in automation loop: {str(e)}")
                time.sleep(check_interval)
        
        logging.info("🏁 Automated unfollow service stopped")

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated X Unfollow Script')
    parser.add_argument('command', choices=['add', 'status', 'run', 'clear'], 
                       help='Command to execute')
    parser.add_argument('--users', nargs='+', help='Usernames to add to queue')
    parser.add_argument('--file', help='File containing usernames (one per line)')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Check interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    unfollower = AutomatedUnfollower()
    
    if args.command == 'add':
        users_to_add = []
        
        if args.users:
            users_to_add.extend(args.users)
        
        if args.file:
            try:
                with open(args.file, 'r') as f:
                    file_users = [line.strip().replace('@', '') for line in f 
                                 if line.strip() and not line.startswith('#')]
                    users_to_add.extend(file_users)
            except Exception as e:
                print(f"Error reading file: {e}")
                return
        
        if users_to_add:
            added = unfollower.add_users_to_queue(users_to_add)
            print(f"Added {added} users to unfollow queue")
        else:
            print("No users specified. Use --users or --file")
    
    elif args.command == 'status':
        status = unfollower.get_status()
        print("\n📊 Automated Unfollow Status:")
        print(f"Queue length: {status['queue_length']}")
        if status['next_username']:
            print(f"Next user: @{status['next_username']}")
        print(f"Can unfollow now: {status['can_unfollow_now']}")
        print(f"Reason: {status['reason']}")
        if status['time_until_next'] > 0:
            print(f"Time until next: {status['time_until_next']} seconds")
        print(f"Rate limits: {status['rate_limits']}")
        print(f"Total unfollowed: {status['stats']['total_unfollowed']}")
        print(f"Failed attempts: {status['stats']['failed_attempts']}")
        print(f"Session duration: {status['stats']['session_duration_minutes']} minutes")
    
    elif args.command == 'run':
        unfollower.run_continuous(args.interval)
    
    elif args.command == 'clear':
        unfollower.queue = []
        unfollower.save_queue()
        print("Cleared unfollow queue")

if __name__ == '__main__':
    main()