# Devin Auto-Fix Setup and Testing Guide

This guide walks you through setting up and testing the Devin auto-fix automation system.

## 📋 Prerequisites Checklist

- [ ] Devin CLI installed
- [ ] GitHub CLI installed  
- [ ] Git installed and configured
- [ ] Node.js installed (for MCP GitHub server)
- [ ] GitHub Personal Access Token created
- [ ] Apache Superset repository cloned

## 🔧 Step-by-Step Setup

### 1. Install Devin CLI

```bash
# Linux/Mac
curl -fsSL https://cli.devin.ai/install.sh | sh

# Windows (PowerShell)
irm https://cli.devin.ai/install.ps1 | iex

# Verify installation
devin --version
```

### 2. Install GitHub CLI

```bash
# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Mac
brew install gh

# Windows
winget install --id GitHub.cli

# Verify installation
gh --version
```

### 3. Authenticate with GitHub

```bash
gh auth login
# Follow the prompts to authenticate
```

### 4. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes:
   - `repo` (full repository access)
   - `issues` (issue management)
   - `pull-requests` (PR creation)
4. Generate and copy the token
5. Save it securely (you'll need it for configuration)

### 5. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/apache/superset.git
cd superset

# Navigate to the superset subdirectory if needed
cd superset
```

### 6. Configure Devin

```bash
# Create MCP configuration
mkdir -p .devin
cat > .devin/mcp_config.local.json << EOF
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
      }
    }
  }
}
EOF

# Replace YOUR_GITHUB_TOKEN_HERE with your actual token
# Use a text editor or sed:
sed -i 's/YOUR_GITHUB_TOKEN_HERE/ghp_your_actual_token/' .devin/mcp_config.local.json
```

### 7. Make Scripts Executable (Linux/Mac)

```bash
chmod +x .devin/scripts/*.sh
```

### 8. Test MCP Connection

```bash
# Test MCP configuration
devin mcp list

# You should see "github" in the list
```

## 🧪 Testing the Automation

### Test 1: Script Validation

```bash
# Test the help message
.devin/scripts/devin-autofix.sh

# Should show usage information
```

### Test 2: Manual Dry Run

Create a test issue first, then:

```bash
# Run the script with a test issue number
.devin/scripts/devin-autofix.sh 12345

# Monitor the output for each step
# Check .devin/logs/ for detailed logs
```

### Test 3: GitHub Action Test

1. Create a test issue in your fork
2. Add the `autofix-devin` label
3. Monitor the Actions tab
4. Check the workflow logs

## 🔍 Validation Checks

### Check File Structure

```bash
# Verify all files are in place
ls -la .devin/
ls -la .devin/skills/
ls -la .devin/scripts/
ls -la .github/workflows/
```

Expected structure:
```
.devin/
├── README.md
├── config.json
├── mcp_config.template.json
├── mcp_config.local.json  # Created by you
├── skills/
│   └── superset-autofix/
│       └── SKILL.md
├── scripts/
│   ├── devin-autofix.sh
│   ├── devin-autofix.ps1
│   └── logger.sh
└── logs/  # Created during execution
```

### Check Configuration

```bash
# Validate Devin config
cat .devin/config.json | jq

# Validate MCP config
cat .devin/mcp_config.local.json | jq

# Should show valid JSON
```

### Check Git Configuration

```bash
# Verify git is configured
git config --global user.name
git config --global user.email

# Set if not configured
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🐛 Common Issues and Solutions

### Issue: Devin CLI not found

**Solution:**
```bash
# Check if Devin is in PATH
which devin

# If not, add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Issue: GitHub authentication fails

**Solution:**
```bash
# Check authentication status
gh auth status

# Re-authenticate
gh auth logout
gh auth login

# Verify token has correct scopes
gh auth status
```

### Issue: MCP server fails to start

**Solution:**
```bash
# Test npx can run the GitHub MCP server
npx -y @modelcontextprotocol/server-github --help

# If this fails, ensure Node.js is installed
node --version
npm --version
```

### Issue: Permission denied on scripts

**Solution:**
```bash
# Make scripts executable
chmod +x .devin/scripts/*.sh

# Or run with bash directly
bash .devin/scripts/devin-autofix.sh 12345
```

### Issue: Branch already exists

**Solution:**
```bash
# Delete existing branch
git branch -D feature/12345

# Or force the script to use a different branch
# (edit the script to handle this case)
```

## 📊 Monitoring and Debugging

### Enable Debug Mode

```bash
export DEVIN_DEBUG=true
.devin/scripts/devin-autofix.sh 12345
```

### View Logs

```bash
# View latest logs
ls -lt .devin/logs/
cat .devin/logs/devin-autofix-*.log

# View JSON logs with pretty printing
cat .devin/logs/devin-autofix-*.json | jq
```

### Check Devin Session

```bash
# Devin exports session logs
cat devin-session.json | jq
```

## 🎯 Success Criteria

A successful test should:

- [ ] Script executes without errors
- [ ] Feature branch is created
- [ ] Devin analyzes the issue correctly
- [ ] Changes are made to appropriate files
- [ ] Tests pass (if applicable)
- [ ] Pre-commit hooks succeed
- [ ] Branch is pushed to remote
- [ ] Pull request is created
- [ ] Issue is updated with PR link
- [ ] `fixed-by-devin` label is added

## 🚀 Next Steps

After successful testing:

1. **Add to your fork**: Push the `.devin/` directory and workflow to your fork
2. **Create a test issue**: Make a simple issue to test the full workflow
3. **Add the label**: Add `autofix-devin` to trigger the automation
4. **Monitor**: Watch the GitHub Action execution
5. **Review**: Check the created PR and issue updates
6. **Iterate**: Refine the skill and configuration based on results

## 📝 Notes

- **First run**: May take longer as dependencies are installed
- **Network**: Requires internet access for MCP server and Devin
- **Tokens**: Keep GitHub tokens secure and rotate regularly
- **Branch cleanup**: Clean up test branches after testing
- **Logs**: Review logs regularly to monitor automation health

## 🔐 Security Reminders

- Never commit `.devin/mcp_config.local.json` to git
- Use environment variables for sensitive data when possible
- Regularly rotate GitHub tokens
- Review Devin permissions configuration
- Monitor GitHub Actions logs for suspicious activity

---

**Need help?** Check the main [.devin/README.md](.devin/README.md) for more details.