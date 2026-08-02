#!/bin/bash
###############################################################################
# Devin API Auto-Fix Script
# 
# This script automates the remediation of GitHub issues using Devin API v3.
# It's designed to be triggered by GitHub Actions or run locally.
#
# Usage: ./devin-autofix.sh <issue_number> [repo_url] [--dry-run]
###############################################################################

set -e  # Exit on error

# Parse arguments
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

ISSUE_NUMBER=$1
REPO_URL=${2:-}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required tools are installed
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI is not installed. Please install it first."
        log_info "Install from: https://cli.github.com"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install it first."
        exit 1
    fi
    
    log_success "All prerequisites are installed."
}

# Function to setup Devin API configuration
setup_devin_api_config() {
    log_info "Setting up Devin API configuration..."
    
    mkdir -p .devin
    
    # Check if config file exists and is valid
    if [ -f ".devin/api_config.json" ]; then
        if python3 -c "import json; json.load(open('.devin/api_config.json'))" 2>/dev/null; then
            log_info "Using existing API configuration from .devin/api_config.json"
            # Extract API key and org ID from config file for environment variables
            DEVIN_API_KEY=$(python3 -c "import json; print(json.load(open('.devin/api_config.json'))['api_key'])")
            DEVIN_ORG_ID=$(python3 -c "import json; print(json.load(open('.devin/api_config.json'))['org_id'])")
            export DEVIN_API_KEY
            export DEVIN_ORG_ID
        else
            log_warning "Existing config file is invalid, recreating from environment variables"
            rm -f .devin/api_config.json
            # Fall through to create from environment variables
        fi
    fi
    
    # Create API configuration from environment variables if needed
    if [ ! -f ".devin/api_config.json" ]; then
        if [ -z "$DEVIN_API_KEY" ] || [ -z "$DEVIN_ORG_ID" ]; then
            log_error "DEVIN_API_KEY and DEVIN_ORG_ID environment variables must be set"
            log_info "Either set them as environment variables or create .devin/api_config.json"
            exit 1
        fi
        
        cat > .devin/api_config.json << EOF
{
  "api_key": "$DEVIN_API_KEY",
  "org_id": "$DEVIN_ORG_ID",
  "base_url": "https://api.devin.ai/v3",
  "timeout": 600,
  "poll_interval": 10,
  "max_poll_attempts": 180
}
EOF
        log_success "Created API configuration from environment variables"
    fi
    
    # Check if MCP config file exists and extract GITHUB_TOKEN
    if [ -f ".devin/mcp_config.local.json" ]; then
        log_info "Using existing MCP configuration for GitHub token"
        GITHUB_TOKEN=$(python3 -c "import json; print(json.load(open('.devin/mcp_config.local.json'))['mcpServers']['github']['env']['GITHUB_TOKEN'])")
        export GITHUB_TOKEN
        log_info "GITHUB_TOKEN extracted from MCP config"
    fi
    
    # Setup MCP configuration for GitHub
    cat > .devin/mcp_config.local.json << EOF
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN:-}"
      }
    }
  }
}
EOF
    
    log_success "Devin API configuration ready."
}

# Function to create custom skill
create_custom_skill() {
    log_info "Creating custom Devin skill..."
    
    mkdir -p .devin/skills/superset-autofix
    
    cat > .devin/skills/superset-autofix/SKILL.md << 'EOF'
---
name: superset-autofix
description: Automatically fix Apache Superset issues following project guidelines
---

You are an automated remediation agent for Apache Superset. Your task is to fix GitHub issues systematically.

## Process
1. Read and understand the GitHub issue carefully
2. Create a feature branch named "feature/ISSUE_NUMBER"
3. Analyze the codebase to identify the problem
4. Implement the fix following AGENTS.md guidelines:
   - Use @superset-ui/core components, not direct antd imports
   - Add proper TypeScript types (no 'any')
   - Follow existing code patterns
   - Run pre-commit before finalizing
5. Test the changes if possible
6. Commit changes with descriptive messages
7. Push the branch to remote
8. Create a pull request
9. Add "fixed-by-devin" label to the issue
10. Comment on the issue with PR link

## Guidelines
- Always reference the original issue in commit messages and PR description
- Follow Apache Superset coding standards
- Be thorough in testing and validation
- Provide observable outputs for technical audience
- If you encounter obstacles, document them clearly
- Use conventional commit format: "fix(scope): description"
EOF
    
    log_success "Custom skill created."
}

# Function to setup GitHub remote repository
setup_github_remote() {
    log_info "Setting up GitHub remote repository..."
    
    # Check if GitHub CLI is authenticated
    if ! gh auth status > /dev/null 2>&1; then
        log_warning "GitHub CLI is not authenticated"
        log_info "Attempting to use GitHub API as fallback"
        return 1
    fi
    
    # Set default repository if origin exists
    if git remote get-url origin > /dev/null 2>&1; then
        if gh repo set-default origin > /dev/null 2>&1; then
            log_success "GitHub default repository set to origin"
            return 0
        else
            log_warning "Could not set default repository, continuing with current setup"
            return 0
        fi
    else
        log_warning "No git remote named 'origin' found"
        return 1
    fi
}

# Function to get issue details
get_issue_details() {
    local issue_number=$1
    local repo_url=${2:-}
    
    log_info "Fetching issue #$issue_number details..."
    
    # Ensure GITHUB_TOKEN is set for GitHub CLI
    if [ -z "$GITHUB_TOKEN" ]; then
        log_error "GITHUB_TOKEN environment variable is not set"
        log_info "Please set GITHUB_TOKEN in your MCP config file or as environment variable"
        exit 1
    fi
    
    # Try to get repository URL from git remote if not provided
    if [ -z "$repo_url" ]; then
        repo_url=$(git remote get-url origin 2>/dev/null || echo "")
        if [ -z "$repo_url" ]; then
            log_warning "Could not get repository URL from git remote"
            repo_url="https://github.com/sreeramvasu/superset"
        fi
    fi
    
    # Clean repository URL (remove .git suffix)
    repo_url=$(echo "$repo_url" | sed 's/\.git$//')
    
    ISSUE_URL="$repo_url/issues/$issue_number"
    REPO_URL="$repo_url"
    
    # Check if issue exists before attempting to fetch details
    if ! gh issue view "$issue_number" --json title -q .title > /dev/null 2>&1; then
        log_error "Issue #$issue_number does not exist in the repository"
        log_info "Please verify the issue number or create the issue first"
        log_info "This could be due to:"
        log_info "  - Issue #$issue_number doesn't exist"
        log_info "  - GitHub authentication issues"
        log_info "  - Network connectivity problems"
        
        # Prompt user for action
        echo "Do you want to: (1) Enter a different issue number, (2) Continue anyway, (3) Exit"
        read -r response
        case "$response" in
            1)
                read -p "Enter the correct issue number: " new_issue_number
                get_issue_details "$new_issue_number" "$repo_url"
                return
                ;;
            2)
                log_warning "Continuing with non-existent issue #$issue_number"
                ISSUE_TITLE="Issue #$issue_number (could not verify)"
                ISSUE_BODY="Could not verify issue existence from GitHub"
                return
                ;;
            *)
                log_info "Exiting as requested"
                exit 1
                ;;
        esac
    fi
    
    if ! ISSUE_TITLE=$(gh issue view "$issue_number" --json title -q .title 2>/dev/null); then
        log_error "Failed to fetch issue details from GitHub"
        log_info "Ensure the issue #$issue_number exists in the repository"
        exit 1
    fi
    
    if ! ISSUE_BODY=$(gh issue view "$issue_number" --json body -q .body 2>/dev/null); then
        log_error "Failed to fetch issue body from GitHub"
        exit 1
    fi
    
    log_success "Issue details retrieved: $ISSUE_TITLE"
}

# Function to run Devin API remediation
run_devin_api_remediation() {
    local issue_number=$1
    local issue_url=$2
    local repo_url=$3
    local dry_run=$4
    local branch_name="feature/$issue_number"
    
    log_info "Starting Devin API remediation..."
    log_info "Issue URL: $issue_url"
    log_info "Repository: $repo_url"
    log_info "Branch: $branch_name"
    if [ "$dry_run" = true ]; then
        log_info "Mode: DRY RUN (no actual API calls will be made)"
    fi
    log_info "=========================================="
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip3 install requests -q
    
    # Build command arguments
    local cmd_args=(
        --issue-number "$issue_number"
        --issue-url "$issue_url"
        --repo-url "$REPO_URL"
        --branch-name "$branch_name"
    )
    
    if [ "$dry_run" = true ]; then
        cmd_args+=(--dry-run)
    fi
    
    # Run the Python API automation script
    python3 .devin/scripts/devin_api_autofix.py "${cmd_args[@]}"
    
    local exit_code=$?
    
    log_info "=========================================="
    
    if [ $exit_code -eq 0 ]; then
        log_success "Devin API remediation completed successfully"
        return 0
    else
        log_error "Devin API remediation failed with exit code: $exit_code"
        return 1
    fi
}

# Function to add label and comment
finalize_issue() {
    local issue_number=$1
    local success=$2
    
    log_info "Finalizing issue..."
    
    # Create label if it doesn't exist
    gh label create "fixed-by-devin" --color "00ff00" --description "Issue fixed by Devin API automation" 2>/dev/null || true
    
    if [ "$success" = "true" ]; then
        # Add label
        gh issue edit $issue_number --add-label "fixed-by-devin"
        
        # Check for PR link in logs
        PR_URL=$(grep -oP 'PR URL: \K.*' .devin/logs/devin-api-result-*.json 2>/dev/null | head -1 || echo "")
        
        # Add comment
        if [ -n "$PR_URL" ]; then
            gh issue comment $issue_number --body "✅ **Devin API Auto-Fix Completed**

I've successfully processed this issue and created a pull request with the fix.

**PR:** $PR_URL
**Branch:** \`feature/$issue_number\`
**Status:** Changes implemented and PR created

Please review the PR and provide feedback."
        else
            gh issue comment $issue_number --body "✅ **Devin API Auto-Fix Completed**

I've successfully processed this issue #$issue_number.

**Branch:** \`feature/$issue_number\`
**Status:** Changes implemented

Please check the created pull request for details."
        fi
        
        log_success "Issue finalized with success"
    else
        # Add comment for failure
        gh issue comment $issue_number --body "❌ **Devin API Auto-Fix Failed**

I encountered issues while trying to fix this issue automatically.

**Issue:** #$issue_number
**Status:** Processing failed

Please check the logs for details and consider fixing this manually."
        
        log_warning "Issue finalized with failure status"
    fi
}

# Function to cleanup
cleanup_devin_config() {
    log_info "Cleaning up..."
    
    # Only remove generated MCP config (not user's API config)
    rm -f .devin/mcp_config.local.json
    
    # Note: We don't remove api_config.json as it contains user's credentials
    # and should persist between runs
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    local issue_number=$1
    local repo_url=${2:-}
    
    if [ -z "$issue_number" ]; then
        log_error "Issue number is required"
        log_info "Usage: $0 <issue_number> [repo_url] [--dry-run]"
        exit 1
    fi
    
    log_info "=========================================="
    log_info "Devin API Auto-Fix Automation"
    log_info "=========================================="
    log_info "Issue: #$issue_number"
    if [ -n "$repo_url" ]; then
        log_info "Repository: $repo_url"
    fi
    log_info "=========================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Setup configuration
    setup_devin_api_config
    
    # Setup GitHub remote repository
    setup_github_remote
    
    # Create custom skill
    create_custom_skill
    
    # Get issue details (this will set REPO_URL if not provided)
    get_issue_details "$issue_number" "$repo_url"
    
    # Run Devin API remediation (use the repo URL from issue details)
    if run_devin_api_remediation "$issue_number" "$ISSUE_URL" "$REPO_URL" "$DRY_RUN"; then
        finalize_issue "$issue_number" "true"
    else
        finalize_issue "$issue_number" "false"
        cleanup_devin_config
        exit 1
    fi
    
    # Cleanup
    cleanup_devin_config
    
    log_success "=========================================="
    log_success "Auto-fix process completed successfully"
    log_success "=========================================="
}

# Run main function
main "$@"
