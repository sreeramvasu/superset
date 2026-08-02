# Devin API Auto-Fix Automation for Apache Superset

This repository contains an event-driven automation system that uses **Devin API v3** to automatically remediate GitHub issues in the Apache Superset project.

## 🎯 Overview

The automation system:
- **Triggers** when an issue is labeled with `autofix-devin`
- **Reads** the issue details using GitHub MCP integration
- **Creates** a feature branch `feature/ISSUE_NUMBER`
- **Remediates** the issue following AGENTS.md guidelines
- **Tests** the changes automatically
- **Creates** a pull request with the fix
- **Updates** the issue with PR link and `fixed-by-devin` label

## 📁 Structure

```
.devin/
├── README.md                          # This file
├── api_config.template.json          # Devin API configuration template
├── config.json                        # Devin configuration
├── mcp_config.template.json          # MCP configuration template
├── skills/
│   └── superset-autofix/
│       └── SKILL.md                   # Custom remediation skill
├── scripts/
│   ├── devin_api_client.py           # Devin API client wrapper
│   ├── devin_api_autofix.py          # API-based automation script
│   ├── devin-autofix.sh              # Bash automation script
│   ├── devin-autofix.ps1             # PowerShell automation script
│   └── logger.sh                     # Structured logging utility
└── logs/                             # Generated logs (gitignored)

.github/workflows/
└── devin-autofix.yml                 # GitHub Action workflow (API-based)
```

## 🚀 Quick Start

### 1. Prerequisites

- **Devin API Key**: Service user API key from Devin dashboard
- **Devin Organization ID**: Organization ID from Devin settings
- **GitHub CLI**: Install from [https://cli.github.com](https://cli.github.com)
- **Git**: Standard git installation
- **Python 3**: For API client scripts
- **Node.js**: For MCP GitHub server (npx)

### 2. Setup

#### Clone and Configure
```bash
# Clone the repository
git clone https://github.com/apache/superset.git
cd superset

# Setup Devin API configuration
cp .devin/api_config.template.json .devin/api_config.json

# Edit the file and add your Devin credentials
# Replace your_api_key_here and your_org_id_here
```

#### Devin API Key Setup
1. Go to Devin dashboard → Settings → Service users
2. Create a service user with appropriate permissions
3. Generate an API key (starts with `cog_`)
4. Note your organization ID from the Service users page

#### GitHub Token Setup
Create a GitHub Personal Access Token with:
- `repo` scope (for full repository access)
- `issues` scope (for issue management)
- `pull-requests` scope (for PR creation)

### 3. Usage

#### Manual Testing
```bash
# Set environment variables
export DEVIN_API_KEY="cog_your_api_key_here"
export DEVIN_ORG_ID="your_org_id_here"
export GITHUB_TOKEN="ghp_your_github_token_here"

# Run automation for a specific issue
.devin/scripts/devin-autofix.sh 12345

# Or with PowerShell (Windows)
$env:DEVIN_API_KEY="cog_your_api_key_here"
$env:DEVIN_ORG_ID="your_org_id_here"
$env:GITHUB_TOKEN="ghp_your_github_token_here"
.\.devin\scripts\devin-autofix.ps1 -IssueNumber 12345
```

#### GitHub Actions (Automated)
1. Add repository secrets:
   - `DEVIN_API_KEY`: Your Devin service user API key
   - `DEVIN_ORG_ID`: Your Devin organization ID
2. Add the `autofix-devin` label to any issue
3. The GitHub Action will automatically trigger
4. Monitor progress in the Actions tab
5. Find the PR link in the issue comments

## 🔧 Configuration

### Devin API Config (.devin/api_config.json)
```json
{
  "api_key": "cog_your_service_user_api_key_here",
  "org_id": "your_organization_id_here",
  "base_url": "https://api.devin.ai/v3",
  "timeout": 600,
  "poll_interval": 10,
  "max_poll_attempts": 180
}
```

### MCP Config (.devin/mcp_config.local.json)
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## 📋 Workflow Process

1. **Trigger**: Issue labeled with `autofix-devin`
2. **Setup**: Configure environment and git
3. **Analysis**: Read and understand the issue
4. **Branch**: Create `feature/ISSUE_NUMBER` branch
5. **Remediation**: Apply fix using Devin API with custom skill
6. **Testing**: Run tests and pre-commit hooks
7. **PR Creation**: Create pull request with changes
8. **Cleanup**: Add labels and comments to issue

## 🎨 Custom Skill

The `superset-autofix` skill in `.devin/skills/superset-autofix/SKILL.md` contains:

- **Step-by-step remediation process**
- **AGENTS.md guidelines compliance**
- **Code quality standards**
- **Testing requirements**
- **Observable output guidelines**

## 📊 Observable Outputs

The system provides comprehensive logging:

### Console Output
- Real-time progress updates
- Step-by-step execution status
- Error messages with context
- Success/failure indicators

### Structured Logs (.devin/logs/)
- JSON-formatted logs for analysis
- File operation tracking
- Test results with duration
- Command execution logs
- Error context and stack traces

### GitHub Issue Updates
- PR links and status
- Error messages if failed
- Summary of changes made
- Next steps for manual review

## 🔐 Security

- **Sensitive data**: API keys in `.devin/api_config.json` (gitignored)
- **Permissions**: Controlled via Devin service user roles
- **Code review**: All changes require manual PR review
- **Rollback**: Feature branches allow easy rollback

## 🐛 Troubleshooting

### Common Issues

**Issue**: Python not found
```bash
# Solution: Install Python 3
# On Ubuntu: sudo apt install python3
# On Mac: brew install python3
# On Windows: Download from python.org
```

**Issue**: API authentication fails
```bash
# Solution: Verify API key and org ID
curl -H "Authorization: Bearer cog_your_key" https://api.devin.ai/v3/self
```

**Issue**: GitHub authentication fails
```bash
# Solution: Check token has correct scopes
gh auth status
gh auth refresh -h github.com
```

**Issue**: Pre-commit hooks fail
```bash
# Solution: Run pre-commit manually to see specific errors
pre-commit run --all-files
```

**Issue**: Branch already exists
```bash
# Solution: Delete existing branch or use different issue
git branch -D feature/ISSUE_NUMBER
```

### Debug Mode

Enable verbose logging by setting environment variable:
```bash
export DEVIN_DEBUG=true
.devin/scripts/devin-autofix.sh 12345
```

## 📈 Monitoring

### GitHub Actions
- Monitor workflow runs in Actions tab
- Check logs for each step
- Review uploaded artifacts (API session logs)

### Local Logs
```bash
# View latest logs
ls -lt .devin/logs/
cat .devin/logs/devin-api-result-*.json | jq
```

### Issue Tracking
- Check issue comments for PR links
- Look for `fixed-by-devin` label
- Review failed automation runs

## 🤝 Contributing

To improve the automation:

1. **Enhance the skill**: Edit `.devin/skills/superset-autofix/SKILL.md`
2. **Add logging**: Extend `.devin/scripts/logger.sh`
3. **Improve API client**: Modify `.devin/scripts/devin_api_client.py`
4. **Improve workflow**: Modify `.github/workflows/devin-autofix.yml`
5. **Update docs**: Edit this README

## 📝 Notes

- **First setup**: Requires manual Devin API key and org ID configuration
- **Branch naming**: Uses `feature/ISSUE_NUMBER` pattern
- **Commit format**: Follows conventional commits
- **Testing**: Runs project-specific test suite
- **Review**: All changes require manual approval
- **API usage**: Billed via Devin API usage metrics

## 🎯 Success Criteria

A successful automation run:
- ✅ Issue is fully understood
- ✅ Fix follows AGENTS.md guidelines
- ✅ All tests pass
- ✅ Pre-commit hooks succeed
- ✅ PR is created with proper description
- ✅ Issue is updated with PR link
- ✅ `fixed-by-devin` label is added

## 📞 Support

For issues with:
- **Devin API**: Check [Devin API Documentation](https://docs.devin.ai/api-reference/overview)
- **GitHub Actions**: Check [GitHub Actions Docs](https://docs.github.com/actions)
- **Apache Superset**: Check [Superset Documentation](https://superset.apache.org/docs)

---

**Automated with ❤️ by Devin API v3**