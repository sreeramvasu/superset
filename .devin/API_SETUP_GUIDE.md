# Devin API Authentication Setup Guide

This guide walks you through setting up Devin API authentication for the auto-fix automation system.

## 🔑 Authentication Overview

The Devin API uses a **service user + API key** model for authentication. This is different from the CLI's OAuth-based authentication.

### Key Concepts

- **Service User**: Non-human account designed for API integrations
- **API Key**: Token that authenticates as the service user (starts with `cog_`)
- **Organization ID**: Unique identifier for your Devin organization
- **RBAC**: Role-based access control for permissions

## 📋 Prerequisites Checklist

- [ ] Access to Devin dashboard (https://app.devin.ai)
- [ ] Organization admin or service user creation permissions
- [ ] GitHub Personal Access Token (for GitHub operations)
- [ ] Python 3.8+ installed
- [ ] GitHub CLI installed

## 🚀 Step-by-Step Setup

### Step 1: Create a Service User

1. **Log in to Devin dashboard**
   - Go to [https://app.devin.ai](https://app.devin.ai)
   - Sign in with your organization account

2. **Navigate to Service Users**
   - Go to **Settings** → **Service users** (organization level)
   - Or **Enterprise settings** → **Service users** (enterprise level)

3. **Create a new service user**
   - Click "Create service user"
   - Give it a descriptive name (e.g., "superset-autofix-bot")
   - Select the appropriate scope:
     - **Organization**: For single-org automation (recommended)
     - **Enterprise**: For multi-org management

4. **Assign permissions**
   - Create or select a role with appropriate permissions
   - Required permissions for auto-fix:
     - `CreateOrgSessions` - Create sessions
     - `ReadOrgSessions` - Read session data
     - `WriteOrgSessions` - Send messages to sessions
     - `ReadOrgKnowledge` - Access knowledge base
     - `ReadOrgPlaybooks` - Access playbooks
   - Apply least privilege principle

5. **Generate API key**
   - After creating the service user, click "Generate API key"
   - **Important**: Copy the API key immediately (shown only once)
   - The key will start with `cog_` (e.g., `cog_abc123xyz`)

### Step 2: Get Your Organization ID

1. **Find your organization ID**
   - On the **Service users** page, your organization ID is displayed
   - It's typically in the format: `org_abc123xyz` or similar
   - Copy this ID for configuration

### Step 3: Create GitHub Personal Access Token

1. **Generate GitHub token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Select scopes:
     - ✅ `repo` (full repository access)
     - ✅ `issues` (issue management)
     - ✅ `pull-requests` (PR creation)
     - ✅ `workflow` (for GitHub Actions)
   - Generate and copy the token (starts with `ghp_`)

### Step 4: Configure Local Environment

#### Option A: Environment Variables (Recommended)

```bash
# Set Devin API credentials
export DEVIN_API_KEY="cog_your_api_key_here"
export DEVIN_ORG_ID="your_org_id_here"

# Set GitHub token
export GITHUB_TOKEN="ghp_your_github_token_here"

# Verify
echo $DEVIN_API_KEY
echo $DEVIN_ORG_ID
echo $GITHUB_TOKEN
```

#### Option B: Configuration File

```bash
# Navigate to project directory
cd superset

# Create API configuration from template
cp .devin/api_config.template.json .devin/api_config.json

# Edit the file
nano .devin/api_config.json
# Replace placeholders with actual values
```

Edit `.devin/api_config.json`:
```json
{
  "api_key": "cog_your_actual_api_key_here",
  "org_id": "your_actual_org_id_here",
  "base_url": "https://api.devin.ai/v3",
  "timeout": 600,
  "poll_interval": 10,
  "max_poll_attempts": 180
}
```

### Step 5: Configure GitHub Actions Secrets

1. **Navigate to repository settings**
   - Go to your repository → Settings → Secrets and variables → Actions

2. **Add repository secrets**
   - Click "New repository secret"
   - Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DEVIN_API_KEY` | `cog_your_api_key` | Devin service user API key |
| `DEVIN_ORG_ID` | `your_org_id` | Devin organization ID |

3. **GitHub token is automatic**
   - `GITHUB_TOKEN` is automatically provided by GitHub Actions
   - No need to add it manually

### Step 6: Test API Authentication

#### Test API Connection
```bash
# Test API credentials
curl -H "Authorization: Bearer $DEVIN_API_KEY" \
  https://api.devin.ai/v3/self

# Should return your user/service user information
```

#### Test Python API Client
```bash
# Install dependencies
pip install requests

# Test the API client
python .devin/scripts/devin_api_client.py "test prompt"

# Should create a test session and return session ID
```

#### Test GitHub Integration
```bash
# Test GitHub CLI
gh auth status

# Test MCP configuration
devin mcp list
# Should show "github" in the list
```

## 🔐 Security Best Practices

### API Key Security
- ✅ Store API keys in environment variables or secret managers
- ✅ Never commit API keys to git (`.devin/api_config.json` is gitignored)
- ✅ Rotate API keys regularly (every 90 days recommended)
- ✅ Use separate service users for different environments
- ✅ Apply least privilege permissions

### GitHub Token Security
- ✅ Use minimal required scopes
- ✅ Rotate tokens regularly
- ✅ Use different tokens for different repositories
- ✅ Monitor token usage in GitHub settings

### Monitoring
- ✅ Review audit logs in Devin dashboard
- ✅ Monitor API usage and costs
- ✅ Set up alerts for unusual activity
- ✅ Review GitHub Actions logs regularly

## 🐛 Troubleshooting

### Common Authentication Issues

#### 401 Unauthorized
**Problem**: API key is invalid or expired

**Solution**:
```bash
# Verify API key format
echo $DEVIN_API_KEY | grep "^cog_"

# Test API connection
curl -H "Authorization: Bearer $DEVIN_API_KEY" \
  https://api.devin.ai/v3/self

# If this fails, regenerate API key in Devin dashboard
```

#### 403 Forbidden
**Problem**: Service user lacks required permissions

**Solution**:
1. Check service user role in Devin dashboard
2. Ensure role has required permissions
3. Update role permissions if needed
4. Regenerate API key if role was changed

#### 404 Not Found
**Problem**: Organization ID is incorrect

**Solution**:
```bash
# Verify organization ID
echo $DEVIN_ORG_ID

# Test with correct org ID
curl -H "Authorization: Bearer $DEVIN_API_KEY" \
  https://api.devin.ai/v3/organizations/$DEVIN_ORG_ID/sessions
```

#### GitHub Authentication Fails
**Problem**: GitHub token is invalid or has wrong scopes

**Solution**:
```bash
# Test GitHub CLI
gh auth status

# Re-authenticate if needed
gh auth logout
gh auth login

# Verify token scopes
gh auth token
```

### Configuration Issues

#### Service User Not Found
**Problem**: Service user doesn't exist or was deleted

**Solution**:
1. Check service user exists in Devin dashboard
2. Verify service user is in correct organization
3. Recreate service user if needed

#### Role Permissions Insufficient
**Problem**: Service user role lacks required permissions

**Solution**:
1. Review current role permissions
2. Add missing permissions to role
3. Or create new role with correct permissions
4. Assign new role to service user

## 📊 API Usage Monitoring

### Monitor API Usage
```bash
# Check session creation
curl -H "Authorization: Bearer $DEVIN_API_KEY" \
  https://api.devin.ai/v3/organizations/$DEVIN_ORG_ID/sessions

# Check service user activity
# (Available in Devin dashboard under Audit logs)
```

### Cost Management
- Monitor API usage in Devin dashboard
- Set up usage alerts if available
- Review session costs regularly
- Optimize prompts to reduce token usage

## 🔄 API Key Rotation

### Regular Rotation Process
1. Generate new API key in Devin dashboard
2. Update environment variables or configuration files
3. Update GitHub Actions secrets
4. Test new API key
5. Revoke old API key after verification

### Emergency Rotation
If API key is compromised:
1. Immediately revoke in Devin dashboard
2. Generate new API key
3. Update all configurations
4. Monitor for unauthorized usage
5. Review audit logs for suspicious activity

## 🎯 Verification Checklist

After setup, verify:

- [ ] Service user created in Devin dashboard
- [ ] API key generated and stored securely
- [ ] Organization ID noted and configured
- [ ] GitHub token created with correct scopes
- [ ] Local environment variables set
- [ ] GitHub Actions secrets configured
- [ ] API connection test successful
- [ ] GitHub CLI authentication working
- [ ] MCP configuration test successful
- [ ] Test automation script runs successfully

## 📞 Support

For authentication issues:
- **Devin API Documentation**: [https://docs.devin.ai/api-reference/authentication](https://docs.devin.ai/api-reference/authentication)
- **Devin Dashboard**: [https://app.devin.ai](https://app.devin.ai)
- **GitHub Support**: [https://support.github.com](https://support.github.com)

---

**Security Reminder**: Never share API keys or commit them to version control. Always use environment variables or secret management systems.