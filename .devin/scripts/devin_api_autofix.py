#!/usr/bin/env python3
"""
Devin API Auto-Fix Script

This script automates the remediation of GitHub issues using Devin API v3.
It's designed to be triggered by GitHub Actions or run locally.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from devin_api_client import DevinAPIClient


class GitHubAPIClient:
    """Simple GitHub API client for fallback operations"""
    
    def __init__(self, token: str):
        """
        Initialize GitHub API client
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_issue(self, owner: str, repo: str, issue_number: str) -> dict:
        """
        Get issue details from GitHub API
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Issue data as dictionary
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def comment_on_issue(self, owner: str, repo: str, issue_number: str, body: str) -> dict:
        """
        Add comment to an issue
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment body
            
        Returns:
            Comment data as dictionary
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": body})
        response.raise_for_status()
        return response.json()
    
    def parse_repo_url(self, repo_url: str) -> tuple:
        """
        Parse repository URL to get owner and repo name
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Tuple of (owner, repo_name)
        """
        # Remove .git suffix if present
        repo_url = repo_url.replace('.git', '')
        
        # Parse URL
        parts = repo_url.rstrip('/').split('/')
        return parts[-2], parts[-1]


# Create logs directory before configuring logging
logs_dir = Path('.devin/logs')
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logging with proper error handling
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('.devin/logs/devin-api-autofix.log'),
            logging.StreamHandler()
        ]
    )
except (OSError, IOError) as e:
    # Fallback to console-only logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    print(f"Warning: Could not configure file logging: {e}. Using console-only logging.")

logger = logging.getLogger(__name__)


class DevinAutoFix:
    """Main automation class for Devin API auto-fix"""
    
    def __init__(self, config_path: str = ".devin/api_config.json"):
        """
        Initialize the auto-fix automation
        
        Args:
            config_path: Path to the API configuration file
        """
        self.client = DevinAPIClient(config_path)
        self.session_id = None
        self.logs_dir = Path(".devin/logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize GitHub API client as fallback
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self.github_client = GitHubAPIClient(github_token)
        else:
            self.github_client = None
            logger.warning("GITHUB_TOKEN not set, GitHub API fallback not available")
        
    def create_feature_branch(self, issue_number: str, repo_url: str) -> str:
        """
        Create a feature branch for the issue
        
        Args:
            issue_number: GitHub issue number
            repo_url: Repository URL
            
        Returns:
            Branch name
        """
        branch_name = f"feature/{issue_number}"
        logger.info(f"Creating feature branch: {branch_name}")
        
        # Git operations would go here
        # For now, we'll pass this info to Devin
        return branch_name
    
    def build_devin_prompt(
        self, 
        issue_number: str, 
        issue_url: str, 
        repo_url: str,
        branch_name: str
    ) -> str:
        """
        Build the prompt for Devin API
        
        Args:
            issue_number: GitHub issue number
            issue_url: GitHub issue URL
            repo_url: Repository URL
            branch_name: Feature branch name
            
        Returns:
            Formatted prompt for Devin
        """
        prompt = f"""
You are an automated remediation agent for Apache Superset. Your task is to fix GitHub issue #{issue_number}.

## Issue Details
- Issue URL: {issue_url}
- Repository: {repo_url}
- Feature Branch: {branch_name}

## Process
1. Read and understand the GitHub issue carefully using GitHub MCP tools
2. Create and checkout the feature branch "{branch_name}"
3. Analyze the codebase to identify the problem
4. Implement the fix following AGENTS.md guidelines:
   - Use @superset-ui/core components, not direct antd imports
   - Add proper TypeScript types (no 'any')
   - Follow existing code patterns
   - Run pre-commit before finalizing
5. Test the changes if possible
6. Commit changes with descriptive messages using conventional commit format
7. Push the branch to remote
8. Create a pull request using GitHub MCP tools
9. **IMPORTANT: Immediately after creating the PR, send a message with the exact PR URL in this format: "PR created: https://github.com/owner/repo/pull/NUMBER"**
10. Report the PR URL in your final response

## Efficiency Guidelines (IMPORTANT)
- SKIP running full installation commands (npm install, pip install) unless absolutely necessary
- The repository likely already has dependencies installed in the environment
- Only install if you encounter import errors or missing dependencies
- Focus on making the minimal code changes required
- Avoid running full test suites - test only the specific changes
- Prioritize speed and efficiency over comprehensive testing

## Guidelines
- Always reference the original issue #{issue_number} in commit messages and PR description
- Follow Apache Superset coding standards from AGENTS.md
- Be thorough in testing and validation
- Provide observable outputs for technical audience
- If you encounter obstacles, document them clearly
- Use conventional commit format: "fix(scope): description"

## Expected Output
At the end, provide:
1. PR URL if created
2. Summary of changes made
3. Any issues encountered
4. Status of the remediation
"""
        return prompt
    
    def run_remediation(
        self, 
        issue_number: str, 
        issue_url: str, 
        repo_url: str,
        branch_name: str,
        dry_run: bool = False
    ) -> dict:
        """
        Run the Devin API remediation process
        
        Args:
            issue_number: GitHub issue number
            issue_url: GitHub issue URL
            repo_url: Repository URL
            branch_name: Feature branch name
            dry_run: If True, skip actual API calls
            
        Returns:
            Result dictionary with status and details
        """
        result = {
            "success": False,
            "session_id": None,
            "pr_url": None,
            "error": None,
            "changes": []
        }
        
        if dry_run:
            logger.info("DRY RUN MODE: Skipping actual API calls")
            logger.info("Would create session with:")
            logger.info(f"  Issue: #{issue_number}")
            logger.info(f"  Branch: {branch_name}")
            logger.info(f"  Repository: {repo_url}")
            result["success"] = True
            result["session_id"] = "dry-run-session-id"
            result["pr_url"] = "https://github.com/test/repo/pull/1"
            result["changes"] = ["dry-run", "test"]
            logger.info("Dry run completed successfully")
            return result
        
        try:
            # Build prompt
            prompt = self.build_devin_prompt(
                issue_number, issue_url, repo_url, branch_name
            )
            
            logger.info("Creating Devin API session...")
            try:
                # Prepare environment variables for the session
                session_environment = {}
                github_token = os.environ.get("GITHUB_TOKEN")
                if github_token:
                    session_environment["GITHUB_TOKEN"] = github_token
                    logger.info("GITHUB_TOKEN will be available in Devin session")
                else:
                    logger.warning("GITHUB_TOKEN not set - GitHub operations may fail")
                
                self.session_id = self.client.create_session(
                    prompt=prompt,
                    repo_url=repo_url,
                    branch=branch_name,
                    skill="superset-autofix",
                    environment=session_environment
                )
                
                if not self.session_id or self.session_id == "None":
                    raise Exception("Session creation returned invalid session ID")
                
                result["session_id"] = self.session_id
                logger.info(f"Session created: {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to create Devin session: {e}")
                logger.error("This could be due to:")
                logger.error("  - Invalid API credentials in .devin/api_config.json")
                logger.error("  - API key permissions insufficient for session creation")
                logger.error("  - Organization ID incorrect")
                logger.error("  - Network connectivity issues")
                logger.error("  - Devin API service unavailable")
                result["error"] = f"Session creation failed: {e}"
                return result
            
            # Wait for completion
            logger.info("Waiting for session completion...")
            logger.info(f"Session ID: {self.session_id}")
            logger.info(f"You can monitor progress at: https://app.devin.ai/sessions/{self.session_id}")
            
            success, pr_url = self.client.wait_for_completion(
                self.session_id,
                repo_url=repo_url,
                branch=branch_name
            )
            
            # Check if PR URL was found even if session timed out
            if pr_url:
                logger.info(f"PR URL found during polling: {pr_url}")
                result["pr_url"] = pr_url
                result["success"] = True  # Consider success if PR was created
                logger.info("Session marked as successful due to PR creation")
            elif success:
                logger.info("Session completed successfully")
                result["success"] = True
                
                # Get final messages to extract PR URL
                messages = self.client.get_messages(self.session_id, limit=10)
                
                # Parse messages for PR URL and summary
                for message in reversed(messages):
                    content = message.get("content", "")
                    if "pull request" in content.lower() or "pr" in content.lower():
                        # Try to extract PR URL
                        if "github.com" in content and "pull" in content:
                            result["pr_url"] = self._extract_pr_url(content)
                
                # Get attachments (changed files)
                attachments = self.client.get_attachments(self.session_id)
                result["changes"] = [att.get("filename") for att in attachments]
                
            else:
                logger.error("Session failed or timed out")
                result["error"] = "Session failed or timed out"
                
                # Even if session failed, check if PR was created (PR-centric success)
                logger.info("Checking for PR URL in final messages despite session failure...")
                try:
                    messages = self.client.get_messages(self.session_id, limit=50)  # Get more messages
                    logger.info(f"Retrieved {len(messages)} final messages for PR detection")
                    
                    for message in reversed(messages):
                        content = message.get("content", "")
                        if content:
                            pr_url = self._extract_pr_url(content)
                            if pr_url:
                                logger.info(f"✓ PR URL found in final messages: {pr_url}")
                                result["pr_url"] = pr_url
                                result["success"] = True  # Override failure if PR was created
                                result["error"] = None  # Clear error since PR creation succeeded
                                logger.info("Session marked as successful due to PR creation")
                                
                                # Try to get attachments for the successful PR
                                try:
                                    attachments = self.client.get_attachments(self.session_id)
                                    result["changes"] = [att.get("filename") for att in attachments]
                                    logger.info(f"Found {len(result['changes'])} changed files")
                                except Exception as e:
                                    logger.warning(f"Failed to get attachments: {e}")
                                break
                except Exception as e:
                    logger.warning(f"Failed to check for PR URL in final messages: {e}")
                
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
            result["error"] = str(e)
            
        finally:
            # Archive session
            if self.session_id:
                try:
                    self.client.archive_session(self.session_id)
                    logger.info("Session archived")
                except Exception as e:
                    logger.warning(f"Failed to archive session: {e}")
        
        return result
    
    def _extract_pr_url(self, text: str) -> str:
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
    
    def save_result(self, result: dict, issue_number: str):
        """
        Save result to log file
        
        Args:
            result: Result dictionary
            issue_number: Issue number
        """
        try:
            # Ensure logs directory exists
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file = self.logs_dir / f"devin-api-result-{issue_number}-{timestamp}.json"
            
            with open(log_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Result saved to {log_file}")
        except Exception as e:
            logger.error(f"Failed to save result to log file: {e}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Devin API Auto-Fix Automation")
    parser.add_argument("--issue-number", required=True, help="GitHub issue number")
    parser.add_argument("--issue-url", required=True, help="GitHub issue URL")
    parser.add_argument("--repo-url", required=True, help="Repository URL")
    parser.add_argument("--branch-name", required=True, help="Feature branch name")
    parser.add_argument("--config", default=".devin/api_config.json", help="API config file path")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without making actual API calls")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("Devin API Auto-Fix Automation")
    logger.info("=" * 50)
    logger.info(f"Issue: #{args.issue_number}")
    logger.info(f"Issue URL: {args.issue_url}")
    logger.info(f"Repository: {args.repo_url}")
    logger.info(f"Branch: {args.branch_name}")
    if args.dry_run:
        logger.info("Mode: DRY RUN (no actual API calls will be made)")
    logger.info("=" * 50)
    
    try:
        # Initialize automation
        autofix = DevinAutoFix(args.config)
        
        # Run remediation
        result = autofix.run_remediation(
            args.issue_number,
            args.issue_url,
            args.repo_url,
            args.branch_name,
            dry_run=args.dry_run
        )
        
        # Save result
        autofix.save_result(result, args.issue_number)
        
        # Output result
        logger.info("=" * 50)
        logger.info("REMEDIATION RESULT")
        logger.info("=" * 50)
        logger.info(f"Success: {result['success']}")
        logger.info(f"Session ID: {result['session_id']}")
        logger.info(f"PR URL: {result['pr_url']}")
        logger.info(f"Changes: {len(result['changes'])} files")
        if result['error']:
            logger.error(f"Error: {result['error']}")
        logger.info("=" * 50)
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()