###############################################################################
# Devin API Auto-Fix Script (PowerShell Version)
# 
# This script automates the remediation of GitHub issues using Devin API v3.
# It's designed to be triggered by GitHub Actions or run locally.
#
# Usage: .\devin-autofix.ps1 -IssueNumber <number> [-RepoUrl <url>]
###############################################################################

param(
    [Parameter(Mandatory=$true)]
    [int]$IssueNumber,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoUrl,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

# Error handling
$ErrorActionPreference = "Stop"

# Logging functions
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Log-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Log-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check prerequisites
function Test-Prerequisites {
    Log-Info "Checking prerequisites..."
    
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Log-Error "Python is not installed. Please install it first."
        exit 1
    }
    
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Log-Error "GitHub CLI is not installed. Please install it first."
        Log-Info "Install from: https://cli.github.com"
        exit 1
    }
    
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Log-Error "Git is not installed. Please install it first."
        exit 1
    }
    
    Log-Success "All prerequisites are installed."
}

# Function to setup Devin API configuration
function Initialize-DevinApiConfig {
    Log-Info "Setting up Devin API configuration..."
    
    $devinDir = ".devin"
    if (-not (Test-Path $devinDir)) {
        New-Item -ItemType Directory -Path $devinDir -Force | Out-Null
    }
    
    # Check if config file exists and is valid
    if (Test-Path "$devinDir/api_config.json") {
        try {
            $apiConfig = Get-Content "$devinDir/api_config.json" | ConvertFrom-Json
            if ($apiConfig.api_key -and $apiConfig.org_id) {
                Log-Info "Using existing API configuration from .devin/api_config.json"
                $env:DEVIN_API_KEY = $apiConfig.api_key
                $env:DEVIN_ORG_ID = $apiConfig.org_id
            } else {
                Log-Warning "Existing config file is invalid, recreating from environment variables"
                Remove-Item "$devinDir/api_config.json" -Force
                throw "Invalid config"
            }
        } catch {
            Log-Warning "Failed to read existing config, creating from environment variables"
            # Fall through to create from environment variables
        }
    }
    
    # Create API configuration from environment variables if needed
    if ([string]::IsNullOrEmpty($env:DEVIN_API_KEY) -or [string]::IsNullOrEmpty($env:DEVIN_ORG_ID)) {
        if ([string]::IsNullOrEmpty($env:DEVIN_API_KEY) -or [string]::IsNullOrEmpty($env:DEVIN_ORG_ID)) {
            Log-Error "DEVIN_API_KEY and DEVIN_ORG_ID environment variables must be set"
            Log-Info "Either set them as environment variables or create .devin/api_config.json"
            exit 1
        }
        
        $apiConfig = @{
            api_key = $env:DEVIN_API_KEY
            org_id = $env:DEVIN_ORG_ID
            base_url = "https://api.devin.ai/v3"
            timeout = 600
            poll_interval = 10
            max_poll_attempts = 180
        }
        
        $apiConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "$devinDir/api_config.json" -Encoding utf8
        Log-Success "Created API configuration from environment variables"
    }
    
    # Check if MCP config file exists and extract GITHUB_TOKEN
    if (Test-Path "$devinDir/mcp_config.local.json") {
        Log-Info "Using existing MCP configuration for GitHub token"
        $mcpConfig = Get-Content "$devinDir/mcp_config.local.json" | ConvertFrom-Json
        if ($mcpConfig.mcpServers.github.env.GITHUB_TOKEN) {
            $env:GITHUB_TOKEN = $mcpConfig.mcpServers.github.env.GITHUB_TOKEN
            Log-Info "GITHUB_TOKEN extracted from MCP config"
        }
    }
    
    # Setup MCP configuration for GitHub
    $mcpConfig = @{
        mcpServers = @{
            github = @{
                command = "npx"
                args = @("-y", "@modelcontextprotocol/server-github")
                env = @{
                    GITHUB_TOKEN = $env:GITHUB_TOKEN
                }
            }
        }
    }
    
    $mcpConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "$devinDir/mcp_config.local.json" -Encoding utf8
    
    Log-Success "Devin API configuration ready."
}

# Function to create custom skill
function Initialize-CustomSkill {
    Log-Info "Creating custom Devin skill..."
    
    $skillDir = ".devin/skills/superset-autofix"
    if (-not (Test-Path $skillDir)) {
        New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
    }
    
    $skillContent = @"
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
"@
    
    $skillContent | Out-File -FilePath "$skillDir/SKILL.md" -Encoding utf8
    
    Log-Success "Custom skill created."
}

# Function to setup GitHub remote repository
function Initialize-GitHubRemote {
    Log-Info "Setting up GitHub remote repository..."
    
    try {
        # Check if GitHub CLI is authenticated
        $authStatus = gh auth status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Log-Warning "GitHub CLI is not authenticated"
            Log-Info "Attempting to use GitHub API as fallback"
            return $false
        }
        
        # Set default repository if origin exists
        $remoteUrl = git remote get-url origin 2>&1
        if ($LASTEXITCODE -eq 0) {
            gh repo set-default origin 2>&1
            if ($LASTEXITCODE -eq 0) {
                Log-Success "GitHub default repository set to origin"
                return $true
            } else {
                Log-Warning "Could not set default repository, continuing with current setup"
                return $true
            }
        } else {
            Log-Warning "No git remote named 'origin' found"
            return $false
        }
    } catch {
        Log-Warning "GitHub remote setup failed: $_"
        return $false
    }
}

# Function to get issue details
function Get-IssueDetails {
    param([int]$IssueNumber, [string]$RepoUrl)
    
    Log-Info "Fetching issue #$IssueNumber details..."
    
    # Ensure GITHUB_TOKEN is set for GitHub CLI
    if ([string]::IsNullOrEmpty($env:GITHUB_TOKEN)) {
        Log-Error "GITHUB_TOKEN environment variable is not set"
        Log-Info "Please set GITHUB_TOKEN in your MCP config file or as environment variable"
        exit 1
    }
    
    # Try to get repository URL from git remote
    if ([string]::IsNullOrEmpty($RepoUrl)) {
        try {
            $RepoUrl = git remote get-url origin
            if ($LASTEXITCODE -ne 0) {
                Log-Warning "Could not get repository URL from git remote"
                $RepoUrl = "https://github.com/sreeramvasu/superset"
            }
        } catch {
            Log-Warning "Git command failed, using default repository URL"
            $RepoUrl = "https://github.com/sreeramvasu/superset"
        }
    }
    
    # Clean repository URL (remove .git suffix)
    $RepoUrl = $RepoUrl -replace '\.git$', ''
    
    $script:IssueUrl = "$RepoUrl/issues/$IssueNumber"
    $script:RepoUrl = $RepoUrl  # Store for later use
    
    # Check if issue exists before attempting to fetch details
    try {
        $issueCheck = gh issue view $IssueNumber --json title -q .title 2>&1
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Issue #$IssueNumber does not exist in the repository"
            Log-Info "Please verify the issue number or create the issue first"
            
            # Prompt user for action
            $response = Read-Host "Do you want to: (1) Enter a different issue number, (2) Continue anyway, (3) Exit"
            switch ($response) {
                "1" {
                    $newIssueNumber = Read-Host "Enter the correct issue number"
                    Get-IssueDetails -IssueNumber $newIssueNumber -RepoUrl $RepoUrl
                    return
                }
                "2" {
                    Log-Warning "Continuing with non-existent issue #$IssueNumber"
                    $script:IssueTitle = "Issue #$IssueNumber (non-existent)"
                    $script:IssueBody = "This issue does not exist in the repository"
                    return
                }
                default {
                    Log-Info "Exiting as requested"
                    exit 1
                }
            }
        }
    } catch {
        Log-Error "Failed to check issue existence: $_"
        Log-Info "This could be due to:"
        Log-Info "  - Issue #$IssueNumber doesn't exist"
        Log-Info "  - GitHub authentication issues"
        Log-Info "  - Network connectivity problems"
        
        # Prompt user for action
        $response = Read-Host "Do you want to: (1) Enter a different issue number, (2) Continue anyway, (3) Exit"
        switch ($response) {
            "1" {
                $newIssueNumber = Read-Host "Enter the correct issue number"
                Get-IssueDetails -IssueNumber $newIssueNumber -RepoUrl $RepoUrl
                return
            }
            "2" {
                Log-Warning "Continuing with non-existent issue #$IssueNumber"
                $script:IssueTitle = "Issue #$IssueNumber (could not verify)"
                $script:IssueBody = "Could not verify issue existence from GitHub"
                return
            }
            default {
                Log-Info "Exiting as requested"
                exit 1
            }
        }
    }
    
    try {
        $script:IssueTitle = gh issue view $IssueNumber --json title -q .title
        $script:IssueBody = gh issue view $IssueNumber --json body -q .body
        Log-Success "Issue details retrieved: $IssueTitle"
    } catch {
        Log-Error "Failed to fetch issue details from GitHub"
        Log-Info "Ensure the issue #$IssueNumber exists in the repository"
        exit 1
    }
}

# Function to run Devin API remediation
function Invoke-DevinApiRemediation {
    param([int]$IssueNumber, [string]$IssueUrl, [string]$RepoUrl, [bool]$DryRun = $false)
    
    $branchName = "feature/$IssueNumber"
    
    Log-Info "Starting Devin API remediation..."
    Log-Info "Issue URL: $IssueUrl"
    Log-Info "Repository: $RepoUrl"
    Log-Info "Branch: $branchName"
    if ($DryRun) {
        Log-Info "Mode: DRY RUN (no actual API calls will be made)"
    }
    Log-Info "=========================================="
    
    # Install Python dependencies
    Log-Info "Installing Python dependencies..."
    pip install requests -q
    
    # Build argument list
    $arguments = @(
        ".devin/scripts/devin_api_autofix.py",
        "--issue-number", $IssueNumber,
        "--issue-url", $IssueUrl,
        "--repo-url", $script:RepoUrl,
        "--branch-name", $branchName
    )
    
    if ($DryRun) {
        $arguments += "--dry-run"
    }
    
    # Run the Python API automation script
    $process = Start-Process -FilePath "python" -ArgumentList $arguments -NoNewWindow -Wait -PassThru
    
    Log-Info "=========================================="
    
    if ($process.ExitCode -eq 0) {
        Log-Success "Devin API remediation completed successfully"
        return $true
    } else {
        Log-Error "Devin API remediation failed with exit code: $($process.ExitCode)"
        return $false
    }
}

# Function to add label and comment
function Set-IssueCompletion {
    param([int]$IssueNumber, [bool]$Success)
    
    Log-Info "Finalizing issue..."
    
    # Create label if it doesn't exist
    try {
        gh label create "fixed-by-devin" --color "00ff00" --description "Issue fixed by Devin API automation" 2>$null
    } catch {
        # Label might already exist
    }
    
    if ($Success) {
        # Add label
        gh issue edit $IssueNumber --add-label "fixed-by-devin"
        
        # Check for PR link in logs
        $logFiles = Get-ChildItem ".devin/logs/devin-api-result-*.json" -ErrorAction SilentlyContinue
        if ($logFiles) {
            $latestLog = $logFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $logContent = Get-Content $latestLog.FullName | ConvertFrom-Json
            $prUrl = $logContent.pr_url
        }
        
        # Add comment
        if ($prUrl) {
            $comment = @"
✅ **Devin API Auto-Fix Completed**

I've successfully processed this issue and created a pull request with the fix.

**PR:** $prUrl
**Branch:** `feature/$IssueNumber`
**Status:** Changes implemented and PR created

Please review the PR and provide feedback.
"@
        } else {
            $comment = @"
✅ **Devin API Auto-Fix Completed**

I've successfully processed this issue #$IssueNumber.

**Branch:** `feature/$IssueNumber`
**Status:** Changes implemented

Please check the created pull request for details.
"@
        }
        gh issue comment $IssueNumber --body $comment
        
        Log-Success "Issue finalized with success"
    } else {
        # Add comment for failure
        $comment = @"
❌ **Devin API Auto-Fix Failed**

I encountered issues while trying to fix this issue automatically.

**Issue:** #$IssueNumber
**Status:** Processing failed

Please check the logs for details and consider fixing this manually.
"@
        gh issue comment $IssueNumber --body $comment
        
        Log-Warning "Issue finalized with failure status"
    }
}

# Function to cleanup
function Remove-TempFiles {
    Log-Info "Cleaning up..."
    
    # Only remove generated MCP config (not user's API config)
    if (Test-Path ".devin/mcp_config.local.json") {
        Remove-Item ".devin/mcp_config.local.json" -Force
    }
    
    # Note: We don't remove api_config.json as it contains user's credentials
    # and should persist between runs
    
    Log-Success "Cleanup completed"
}

# Main execution
try {
    Log-Info "=========================================="
    Log-Info "Devin API Auto-Fix Automation"
    Log-Info "=========================================="
    Log-Info "Issue: #$IssueNumber"
    if (-not [string]::IsNullOrEmpty($RepoUrl)) {
        Log-Info "Repository: $RepoUrl"
    }
    Log-Info "=========================================="
    
    # Check prerequisites
    Test-Prerequisites
    
    # Setup configuration
    Initialize-DevinApiConfig
    
    # Setup GitHub remote repository
    Initialize-GitHubRemote
    
    # Create custom skill
    Initialize-CustomSkill
    
    # Get issue details (this will set $script:RepoUrl if not provided)
    Get-IssueDetails -IssueNumber $IssueNumber -RepoUrl $RepoUrl
    
    # Run Devin API remediation (use the repo URL from issue details)
    $success = Invoke-DevinApiRemediation -IssueNumber $IssueNumber -IssueUrl $script:IssueUrl -RepoUrl $script:RepoUrl -DryRun $DryRun
    
    if ($success) {
        Set-IssueCompletion -IssueNumber $IssueNumber -Success $true
    } else {
        Set-IssueCompletion -IssueNumber $IssueNumber -Success $false
        Remove-TempFiles
        exit 1
    }
    
    # Cleanup
    Remove-TempFiles
    
    Log-Success "=========================================="
    Log-Success "Auto-fix process completed successfully"
    Log-Success "=========================================="
    
} catch {
    Log-Error "An error occurred: $_"
    Remove-TempFiles
    exit 1
}
