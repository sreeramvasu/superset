#!/usr/bin/env python3
"""
Utility script to manually check Devin session status
Usage: python check_session.py <session_id>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from devin_api_client import DevinAPIClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_session.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    
    try:
        client = DevinAPIClient()
        
        print(f"Checking session: {session_id}")
        print(f"Web interface: https://app.devin.ai/sessions/{session_id}")
        print("=" * 50)
        
        # Get session details
        session_data = client.get_session(session_id)
        print(f"Status: {session_data.get('status', 'unknown')}")
        print(f"Created: {session_data.get('created_at', 'unknown')}")
        print(f"Updated: {session_data.get('updated_at', 'unknown')}")
        
        # Get recent messages
        messages = client.get_messages(session_id, limit=10)
        print(f"\nRecent messages ({len(messages)}):")
        print("-" * 50)
        
        for msg in messages[-10:]:  # Show last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            print(f"[{role}] {content[:200]}...")
        
        # Get attachments
        attachments = client.get_attachments(session_id)
        print(f"\nAttachments ({len(attachments)}):")
        print("-" * 50)
        for att in attachments:
            print(f"  - {att.get('filename', 'unknown')}")
        
    except Exception as e:
        print(f"Error checking session: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()