# Devin Automation Guide

## 🤖 Overview

This system provides automated issue remediation for Apache Superset using the Devin AI platform. It automatically fixes GitHub issues by:
- Analyzing the issue description
- Creating a feature branch
- Implementing the fix following Superset coding standards
- Creating a pull request
- Adding labels and comments to track progress

## 🚀 Quick Start

### **Automatic Triggering (Recommended)**

1. **Add the `autofix-devin` label** to any GitHub issue
2. GitHub Actions automatically triggers the automation
3. Wait for the workflow to complete
4. Review the created PR

```bash
gh issue edit <issue_number> --add-label "autofix-devin"
```

### **Manual Triggering**

Trigger the workflow manually for a specific issue:

```bash
gh workflow run devin-autofix.yml -f issue_number=<issue_number>
```

## 📋 Prerequisites

### **GitHub Repository Setup**

1. **Create GitHub Secrets** (Repository Settings → Secrets and variables → Actions):
   - `DEVIN_API_KEY`: Your Devin API key
   - `DEVIN_ORG_ID`: Your Devin organization ID

2. **Create Labels** (only need to do once):
   ```bash
   gh label create autofix-devin --color "00ff00" --description "Trigger Devin API auto-fix automation"
   gh label create fixed-by-devin --color "00ff00" --description "Issue fixed by Devin API automation"
   ```

### **Local Setup**

1. **Install Python dependencies**:
   ```bash
   pip install requests
   ```

2. **Configure Devin API**:
   ```bash
   cp .devin/api_config.template.json .devin/api_config.json
   # Edit .devin/api_config.json with your actual API key and org ID
   ```

## 🔧 How It Works

### **Architecture**

```
GitHub Issue (with label)
    ↓
GitHub Actions Trigger
    ↓
Devin API Session Created
    ↓
Devin AI Analyzes & Fixes Issue
    ↓
Devin Creates PR & Sends URL Message
    ↓
Polling Detects PR URL
    ↓
Workflow Completes (Success)
    ↓
Adds fixed-by-devin Label
    ↓
Comments on Issue with PR Link
```

### **Key Components**

1. **GitHub Actions Workflow** (`.github/workflows/devin-autofix.yml`)
   - Triggers on `autofix-devin` label addition
   - Sets up environment (Python, Node.js, Git)
   - Configures Devin API
   - Runs automation script
   - Adds labels and comments

2. **Devin API Client** (`.devin/scripts/devin_api_client.py`)
   - Handles Devin API communication
   - Creates sessions
   - Polls for completion
   - Detects PR URLs in messages

3. **Automation Script** (`.devin/scripts/devin_api_autofix.py`)
   - Orchestrates the automation process
   - Builds prompts for Devin
   - Handles error cases
   - Logs results

4. **Custom Skill** (`.devin/skills/superset-autofix/SKILL.md`)
   - Provides Superset-specific guidelines
   - Ensures code follows project standards
   - Instructs Devin on PR URL messaging

## 🛠️ Manual Execution

### **Run Locally**

```bash
python .devin/scripts/devin_api_autofix.py \
  --issue-number 19 \
  --issue-url https://github.com/sreeramvasu/superset/issues/19 \
  --repo-url https://github.com/sreeramvasu/superset \
  --branch-name "feature/19"
```

### **Run with Dry-Run Mode**

Test without making actual changes:

```bash
python .devin/scripts/devin_api_autofix.py \
  --issue-number 19 \
  --issue-url https://github.com/sreeramvasu/superset/issues/19 \
  --repo-url https://github.com/sreeramvasu/superset \
  --branch-name "feature/19" \
  --dry-run
```

### **PowerShell Script**

```powershell
cd .devin\scripts
.\devin-autofix.ps1 -IssueNumber 19 -IssueUrl "https://github.com/sreeramvasu/superset/issues/19" -RepoUrl "https://github.com/sreeramvasu/superset" -BranchName "feature/19"
```

### **Bash Script**

```bash
cd .devin/scripts
./devin-autofix.sh -i 19 -u "https://github.com/sreeramvasu/superset/issues/19" -r "https://github.com/sreeramvasu/superset" -b "feature/19"
```

## 📊 Observability

### **Dashboard**

Generate and view the observability dashboard:

```bash
python .devin/scripts/observability_dashboard.py
start .devin/logs/observability_dashboard.html
```

The dashboard shows:
- Total sessions and success rate
- PR creation rate
- Time period analysis (24h, 7d, 30d)
- Recent sessions with detailed information
- PR links and error messages

### **GitHub Actions Artifacts**

Each workflow run uploads observability logs as artifacts:
- Go to Actions tab
- Click on a workflow run
- Download `devin-observability-logs-{run_number}` artifact

## 🔍 Monitoring & Troubleshooting

### **Check Workflow Status**

```bash
gh run list --workflow=devin-autofix.yml
gh run view <run_id> --log
```

### **Common Issues**

#### **1. GITHUB_TOKEN Not Set**
**Error**: "GITHUB_TOKEN not set, GitHub API fallback not available"
**Cause**: Token not passed to workflow step
**Solution**: Fixed in latest workflow update - token is now explicitly passed

#### **2. PR URL Not Detected**
**Error**: Workflow continues polling despite PR creation
**Cause**: Devin not sending PR URL in messages
**Solution**: Devin now instructed to send PR URL message immediately after creation

#### **3. No Polling Messages**
**Error**: Can't see polling progress in logs
**Cause**: Python output buffering
**Solution**: `PYTHONUNBUFFERED=1` added to workflow for real-time output

#### **4. Session Timeout**
**Error**: Session times out before completion
**Cause**: Complex task taking longer than timeout
**Solution**: Timeout increased to 3600s (60 minutes)

### **View Devin Session**

After a session is created, monitor it directly:
```
https://app.devin.ai/sessions/<session_id>
```

## 🎯 Workflow Features

### **Automatic PR Detection**
- Workflow stops immediately when PR is created
- No need to wait for full timeout
- Based on Devin sending PR URL in messages

### **Smart Labeling**
- Only adds `fixed-by-devin` label when PR is successfully created
- Checks for PR URL in issue comments before adding label
- No false positives for failed automation attempts

### **Enhanced Comments**
- Comments include PR URL when available
- Provides clear success/failure status
- Links to relevant resources

### **Efficiency Optimizations**
- Workspace caching enabled (if supported by Devin API)
- Instructions to skip unnecessary installations
- Focus on minimal changes rather than full rebuilds

## 📝 Configuration

### **API Configuration** (`.devin/api_config.json`)

```json
{
  "api_key": "your-api-key",
  "org_id": "your-org-id",
  "base_url": "https://api.devin.ai/v3",
  "timeout": 3600,
  "poll_interval": 10,
  "max_poll_attempts": 360
}
```

### **Timeout Settings**

- **Timeout**: 3600s (60 minutes) - maximum session duration
- **Poll Interval**: 10s - how often to check for updates
- **Max Poll Attempts**: 360 - matches timeout duration

## 🧪 Testing

### **Test with Simple Issue**

Test with a simple, well-defined issue first:

1. Create a simple issue (e.g., linting or formatting)
2. Add `autofix-devin` label
3. Monitor the workflow
4. Review the resulting PR

### **Test with Dry-Run**

Test without making actual changes:

```bash
python .devin/scripts/devin_api_autofix.py \
  --issue-number 19 \
  --issue-url https://github.com/sreeramvasu/superset/issues/19 \
  --repo-url https://github.com/sreeramvasu/superset \
  --branch-name "feature/19" \
  --dry-run
```

## 📚 File Structure

```
.devin/
├── api_config.json              # Devin API configuration (local)
├── api_config.template.json     # Configuration template
├── config.json                  # Devin configuration
├── mcp_config.json              # MCP server configuration
├── logs/                        # Observability logs
│   ├── observability_dashboard.html
│   └── observability_stats.json
├── scripts/
│   ├── devin_api_autofix.py    # Main automation script
│   ├── devin_api_client.py     # Devin API client wrapper
│   ├── devin-autofix.ps1       # PowerShell wrapper
│   ├── devin-autofix.sh        # Bash wrapper
│   ├── observability_dashboard.py # Observability dashboard
│   ├── sync_github_logs.py      # GitHub logs sync (future)
│   └── terminate_session.py    # Session termination (future)
└── skills/
    └── superset-autofix/
        └── SKILL.md             # Superset-specific guidelines
```

## 🔐 Security Considerations

- **API keys stored in GitHub Secrets** - never commit them
- **Sensitive files excluded** via `.gitignore`
- **GITHUB_TOKEN** automatically provided by GitHub Actions
- **Workspace isolation** - each Devin session is isolated

## 🚀 Future Enhancements

- [ ] GitHub logs sync for observability dashboard
- [ ] Session termination capability
- [ ] Workspace persistence optimization
- [ ] Multi-issue batch processing
- [ ] Custom issue type selection

## 📖 Related Documentation

- [Superset AGENTS.md](../AGENTS.md) - Coding standards and guidelines
- [Superset SECURITY.md](../SECURITY.md) - Security model
- [Devin API Documentation](https://api.devin.ai/v3) - API reference

## 💡 Tips

1. **Start with simple issues** - Test with formatting or linting issues first
2. **Monitor first runs** - Watch the workflow closely to understand behavior
3. **Check the dashboard** - Use observability dashboard to track success rates
4. **Review PRs carefully** - Devin creates good first drafts but review is essential
5. **Provide feedback** - Update the skill file with lessons learned

## 🆘 Support

For issues or questions:
1. Check the GitHub Actions logs for detailed error messages
2. Review the observability dashboard for patterns
3. Check the Devin session directly at app.devin.ai
4. Review this guide for common troubleshooting steps