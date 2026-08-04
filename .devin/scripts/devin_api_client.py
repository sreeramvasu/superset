#!/usr/bin/env python3
"""
Devin API Client Wrapper

This script provides a Python wrapper for the Devin API v3 to handle
session management, message sending, and file operations for the
auto-fix automation system.
"""

import os
import json
import time
import requests
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path


class DevinAPIClient:
    """Client for interacting with Devin API v3"""
    
    def __init__(self, config_path: str = ".devin/api_config.json"):
        """
        Initialize the Devin API client
        
        Args:
            config_path: Path to the API configuration file
        """
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("api_key")
        self.org_id = self.config.get("org_id")
        self.base_url = self.config.get("base_url", "https://api.devin.ai/v3")
        self.timeout = self.config.get("timeout", 300)
        self.poll_interval = self.config.get("poll_interval", 5)
        self.max_poll_attempts = self.config.get("max_poll_attempts", 120)
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load API configuration from file or environment variables"""
        # Try to load from file first
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
                # Validate required fields
                if not config.get("api_key") or config.get("api_key") == "cog_your_service_user_api_key_here":
                    raise ValueError(
                        "API key is not configured. Please update .devin/api_config.json with your actual API key."
                    )
                
                if not config.get("org_id") or config.get("org_id") == "your_organization_id_here":
                    raise ValueError(
                        "Organization ID is not configured. Please update .devin/api_config.json with your actual organization ID."
                    )
                
                return config
                
        except FileNotFoundError:
            # Fall back to environment variables
            api_key = os.environ.get("DEVIN_API_KEY")
            org_id = os.environ.get("DEVIN_ORG_ID")
            
            if not api_key or not org_id:
                raise FileNotFoundError(
                    f"API config file not found at {config_path} and "
                    "DEVIN_API_KEY/DEVIN_ORG_ID environment variables not set. "
                    "Please create the config file or set environment variables."
                )
            
            return {
                "api_key": api_key,
                "org_id": org_id,
                "base_url": os.environ.get("DEVIN_BASE_URL", "https://api.devin.ai/v3"),
                "timeout": int(os.environ.get("DEVIN_TIMEOUT", "600")),
                "poll_interval": int(os.environ.get("DEVIN_POLL_INTERVAL", "10")),
                "max_poll_attempts": int(os.environ.get("DEVIN_MAX_POLL_ATTEMPTS", "180"))
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with error handling
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def create_session(
        self, 
        prompt: str,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        skill: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new Devin session
        
        Args:
            prompt: Initial prompt for the session
            repo_url: Repository URL to work with
            branch: Branch name to use
            skill: Skill to use for the session
            environment: Environment variables to set in the session
            
        Returns:
            Session ID (devin_id)
            
        Raises:
            Exception: If session creation fails or returns invalid data
        """
        endpoint = f"/organizations/{self.org_id}/sessions"
        
        session_data = {
            "prompt": prompt
        }
        
        # Add optional parameters
        if repo_url:
            session_data["repo_url"] = repo_url
        if branch:
            session_data["branch"] = branch
        if skill:
            session_data["skill"] = skill
        if environment:
            session_data["environment"] = environment
        
        # Add workspace persistence for faster subsequent sessions
        # This may cache dependencies and environment setup
        session_data["persist_workspace"] = True
        session_data["use_cache"] = True
        
        try:
            response = self._make_request("POST", endpoint, session_data)
            
            # Check if response contains session ID
            if not response:
                raise Exception("Empty response from session creation API")
            
            # Try different possible field names for session ID
            session_id = response.get("devin_id") or response.get("id") or response.get("session_id")
            
            if not session_id:
                raise Exception(f"Session creation failed - no session ID in response. Response: {response}")
            
            return session_id
            
        except Exception as e:
            raise Exception(f"Failed to create Devin session: {e}")
    
    def send_message(
        self, 
        session_id: str, 
        message: str,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an existing session
        
        Args:
            session_id: Devin session ID
            message: Message content
            attachments: List of file attachments
            
        Returns:
            Message response data
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/messages"
        
        message_data = {
            "content": message
        }
        
        if attachments:
            message_data["attachments"] = attachments
        
        return self._make_request("POST", endpoint, message_data)
    
    def get_messages(
        self, 
        session_id: str,
        limit: int = 100,
        after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a session
        
        Args:
            session_id: Devin session ID
            limit: Maximum number of messages to retrieve
            after: Cursor for pagination
            
        Returns:
            List of messages
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/messages"
        
        params = {"limit": limit}
        if after:
            params["after"] = after
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("messages", [])
    
    def wait_for_completion(
        self, 
        session_id: str,
        timeout: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Wait for a session to complete by polling for messages
        
        Args:
            session_id: Devin session ID
            timeout: Custom timeout in seconds
            
        Returns:
            Tuple of (success: bool, pr_url: Optional[str])
            
        Raises:
            Exception: If session_id is invalid or polling fails
        """
        # Validate session_id
        if not session_id or session_id == "None":
            raise Exception(f"Invalid session ID: {session_id}. Session creation may have failed.")
        
        timeout = timeout or self.timeout
        start_time = time.time()
        last_message_id = None
        poll_count = 0
        found_pr_url = None
        
        print(f"Starting to poll for session completion (timeout: {timeout}s, interval: {self.poll_interval}s)")
        
        while time.time() - start_time < timeout:
            try:
                poll_count += 1
                elapsed = int(time.time() - start_time)
                
                # Get session status first
                try:
                    session_data = self.get_session(session_id)
                    status = session_data.get("status", "unknown")
                    print(f"Poll #{poll_count}: Session status: {status} (elapsed: {elapsed}s)")
                except Exception as e:
                    print(f"Poll #{poll_count}: Could not get session status: {e}")
                
                # Get messages
                messages = self.get_messages(
                    session_id, 
                    limit=5,  # Get more messages to see progress
                    after=last_message_id
                )
                
                if messages:
                    print(f"Poll #{poll_count}: Retrieved {len(messages)} new message(s)")
                    
                    for message in messages:
                        last_message_id = message.get("id")
                        content = message.get("content", "")
                        role = message.get("role", "unknown")
                        
                        # Show progress messages
                        if content and len(content) < 200:  # Only show short messages
                            print(f"  [{role}] {content[:100]}...")
                        
                        # Check for PR URL during polling
                        if not found_pr_url:
                            found_pr_url = self._extract_pr_url(content)
                            if found_pr_url:
                                print(f"✓ PR URL found: {found_pr_url}")
                                # PR creation is our success condition - we can stop polling
                                print("PR created successfully - marking session as successful")
                                return (True, found_pr_url)
                        
                        # Check for completion indicators in this message
                        content_lower = content.lower()
                        if any(indicator in content_lower for indicator in [
                            "completed", "finished", "done", "error", "failed", 
                            "remediation complete", "fix applied", "changes made",
                            "committed", "pushed", "pull request"
                        ]):
                            print(f"Completion detected in message: {content[:100]}...")
                            return ("error" not in content_lower and "failed" not in content_lower, found_pr_url)
                else:
                    # Check if this is a prolonged silence (might indicate session is stuck)
                    if poll_count > 10 and (poll_count % 10 == 0):
                        print(f"Poll #{poll_count}: No new messages for {elapsed}s - session may be processing complex task")
                    else:
                        print(f"Poll #{poll_count}: No new messages (elapsed: {elapsed}s)")
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"Error polling messages: {e}")
                time.sleep(self.poll_interval)
        
        print(f"Timeout reached after {int(time.time() - start_time)}s")
        return (False, found_pr_url)
    
    def _extract_pr_url(self, text: str) -> Optional[str]:
        """
        Extract PR URL from text
        
        Args:
            text: Text to search for PR URL
            
        Returns:
            PR URL if found, None otherwise
        """
        import re
        pr_pattern = r'https://github\.com/[^/]+/[^/]+/pull/\d+'
        match = re.search(pr_pattern, text)
        return match.group(0) if match else None
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details
        
        Args:
            session_id: Devin session ID
            
        Returns:
            Session data
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}"
        return self._make_request("GET", endpoint)
    
    def get_attachments(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get file attachments from a session
        
        Args:
            session_id: Devin session ID
            
        Returns:
            List of attachments
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/attachments"
        response = self._make_request("GET", endpoint)
        return response.get("attachments", [])
    
    def download_attachment(
        self, 
        session_id: str, 
        attachment_id: str,
        output_path: str
    ) -> str:
        """
        Download a file attachment from a session
        
        Args:
            session_id: Devin session ID
            attachment_id: Attachment ID
            output_path: Local path to save the file
            
        Returns:
            Path to downloaded file
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/attachments/{attachment_id}/download"
        
        response = self.session.get(
            f"{self.base_url}{endpoint}",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return output_path
    
    def upload_file(
        self, 
        session_id: str, 
        file_path: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to a session
        
        Args:
            session_id: Devin session ID
            file_path: Local file path to upload
            description: File description
            
        Returns:
            Upload response data
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/attachments"
        
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f)}
            data = {}
            if description:
                data["description"] = description
            
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session
        
        Args:
            session_id: Devin session ID
            
        Returns:
            True if successful
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}/archive"
        self._make_request("POST", endpoint)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Devin session ID
            
        Returns:
            True if successful
        """
        endpoint = f"/organizations/{self.org_id}/sessions/{session_id}"
        self._make_request("DELETE", endpoint)
        return True


def main():
    """Test the API client"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python devin_api_client.py <test_prompt>")
        sys.exit(1)
    
    try:
        client = DevinAPIClient()
        print(f"Connected to Devin API for org: {client.org_id}")
        
        # Test session creation
        session_id = client.create_session(sys.argv[1])
        print(f"Created session: {session_id}")
        
        # Wait for completion
        print("Waiting for session completion...")
        success = client.wait_for_completion(session_id)
        
        if success:
            print("Session completed successfully")
            
            # Get attachments
            attachments = client.get_attachments(session_id)
            print(f"Found {len(attachments)} attachments")
            
            # Archive session
            client.archive_session(session_id)
            print("Session archived")
        else:
            print("Session failed or timed out")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()