# Unified Webhook Handler

A powerful, platform-agnostic webhook handler that processes events from GitHub and GitLab using a unified filtering system. Write your notification rules once, and they'll work across all platforms automatically.

## 🎯 Key Features

- **🔄 Platform Unified**: Single filter configuration works for both GitHub and GitLab
- **🎨 Flexible Filtering**: Powerful condition matching with AND/OR logic
- **📁 File Content Inspection**: Fetch and scan file contents from repositories
- **🔔 Multiple Notification Channels**: Slack, Email (extensible to Discord, Teams, etc.)
- **🔒 Secure**: HMAC signature verification for GitHub, token auth for GitLab
- **📝 Event Logging**: All events saved to JSON for debugging and analysis
- **⚡ Easy Configuration**: YAML-based filter rules with environment variable secrets

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone git@github.com:Joeri-Abbo/git-webhook-scanner.git 
cd git-webhook-scanner

# Install dependencies
make install
# For development
make dev-install
```

### 2. Configuration

Create a `.env` file:

```bash
# Platform webhook secrets
GITHUB_WEBHOOK_SECRET=your_github_secret_here
GITLAB_WEBHOOK_TOKEN=your_gitlab_token_here

# API tokens for file content fetching (optional)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Notification channel
NOTIFICATION_CHANNEL=slack

# Slack configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Create `config.yaml` with your filters:

```yaml
filters:
  - name: "Critical Issues"
    platform: [github, gitlab]  # Works on both platforms!
    events: [issues, issue]
    conditions:
      labels:
        contains: "critical"
    notify: true
    message: "🚨 Critical issue #{issue_number}: {issue_title} in {repository}"
```

### 3. Run the Application

#### Option A: Local Development

```bash
# Development
python main.py

# Production (with Hypercorn)
make run
```

The application will start on `http://localhost:8000`.

#### Option B: Docker (Recommended for Production)

```bash
# Using Docker Compose (easiest)
docker-compose up -d

# Or using pre-built image from GitHub Container Registry
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:latest
docker run -d -p 8000:8000 --env-file .env -v $(pwd)/config.yaml:/app/config.yaml:ro ghcr.io/joeri-abbo/git-webhook-scanner:latest
```

📘 **See [DOCKER.md](DOCKER.md) for complete Docker deployment guide.**

### 4. Configure Webhooks

#### GitHub

1. Go to repository → Settings → Webhooks → Add webhook
2. **Payload URL**: `https://your-domain.com/github/webhook`
3. **Content type**: `application/json`
4. **Secret**: Your `GITHUB_WEBHOOK_SECRET` value
5. **Events**: Select the events you want to monitor

#### GitLab

1. Go to repository → Settings → Webhooks → Add webhook
2. **URL**: `https://your-domain.com/gitlab/webhook`
3. **Secret token**: Your `GITLAB_WEBHOOK_TOKEN` value
4. **Trigger**: Select the events you want to monitor

## 📖 How It Works

### The Normalization Concept

Different platforms send different webhook payloads. This system normalizes them into a common format:

**GitHub payload:**
```json
{
  "action": "opened",
  "issue": { "number": 42, "title": "Bug report" },
  "repository": { "full_name": "acme/api" }
}
```

**GitLab payload:**
```json
{
  "object_kind": "issue",
  "object_attributes": { "iid": 42, "title": "Bug report" },
  "project": { "path_with_namespace": "acme/api" }
}
```

**Both become:**
```json
{
  "platform": "github|gitlab",
  "event_type": "issues|issue",
  "repository": "acme/api",
  "issue_number": 42,
  "issue_title": "Bug report",
  ...
}
```

This means **one filter works everywhere**:

```yaml
- name: "Bug Reports"
  platform: [github, gitlab]
  events: [issues, issue]
  conditions:
    issue_title:
      contains: "bug"
  notify: true
```

### Processing Pipeline

```
Webhook Received
    ↓
Verify Signature/Token
    ↓
Extract Event Type
    ↓
Normalize Data ← Platform-specific logic
    ↓
Evaluate Filters ← Your rules here
    ↓
Send Notifications ← Slack/Email
```

## 🎛️ Filter Configuration

### Basic Filter Structure

```yaml
filters:
  - name: "Filter Name"           # Human-readable name
    platform: [github, gitlab]    # Which platforms to apply to
    events: [issues, push]        # Which event types to monitor
    conditions:                   # AND logic - all must match
      field_name:
        operator: value
    notify: true                  # Send notification?
    message: "Template message"   # Notification text with {variables}
```

### Condition Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `contains` | Substring match (case-insensitive) | `title contains "bug"` |
| `equals` | Exact match | `action equals "opened"` |
| `in` | Value in list | `label in ["urgent", "critical"]` |
| `regex` | Regular expression | `title regex "^JIRA-\d+"` |
| `greater_than` | Numeric comparison | `pr_changes greater_than 100` |
| `less_than` | Numeric comparison | `pr_changes less_than 10` |
| `starts_with` | Prefix match | `branch starts_with "feature/"` |
| `ends_with` | Suffix match | `filename ends_with ".py"` |

### AND vs OR Logic

**AND Logic (all conditions must match):**
```yaml
conditions:
  issue_title:
    contains: "bug"
  labels:
    contains: "production"
```

**OR Logic (any condition can match):**
```yaml
any_of:
  - issue_title:
      contains: "urgent"
  - labels:
      contains: "critical"
```

### Available Fields

After normalization, these fields are available:

**Common fields:**
- `platform` - "github" or "gitlab"
- `event_type` - Event name (normalized)
- `repository` - Full repo name ("org/repo")
- `sender` - Username who triggered event
- `action` - Action type ("opened", "closed", etc.)

**Issue fields:**
- `issue_number` - Issue number
- `issue_title` - Issue title
- `issue_body` - Issue description
- `issue_url` - URL to issue

**Pull/Merge Request fields:**
- `pr_number` - PR/MR number
- `pr_title` - PR/MR title
- `pr_body` - PR/MR description
- `pr_url` - URL to PR/MR
- `pr_changes` - Number of files changed
- `target_branch` - Target branch name
- `source_branch` - Source branch name

**Push fields:**
- `ref` - Git ref (e.g., "refs/heads/main")
- `commits` - Number of commits
- `modified_files` - List of changed files
- `commit_messages` - List of commit messages
- `compare_url` - URL to view diff

**Workflow fields:**
- `workflow_name` - Workflow/pipeline name
- `workflow_status` - Status (running, completed, etc.)
- `workflow_conclusion` - Conclusion (success, failure, etc.)

**Label fields:**
- `labels` - List of labels applied

## 🔍 Advanced Features

### File Content Inspection

Check the **contents** of files in addition to their names:

```yaml
- name: "Secrets in Config"
  platform: [github, gitlab]
  events: [push]
  conditions:
    modified_files:
      contains: "config.yaml"
    file_content_contains:
      contains: ["password", "api_key", "secret"]
  notify: true
  message: "⚠️ Potential secrets in config file: {repository}"
```

**How it works:**
1. Filter matches `config.yaml` in modified files
2. System fetches file content via GitHub/GitLab API
3. Checks if any of the patterns appear in content
4. Sends notification if match found

**Requirements:**
- Set `GITHUB_TOKEN` and/or `GITLAB_TOKEN` in `.env`
- Token must have `repo` (GitHub) or `read_api` (GitLab) scope

### Per-Organization Tokens

For GitHub, you can use different tokens per organization:

```bash
# .env
GITHUB_TOKEN=ghp_default_token
GITHUB_ORG_TOKEN_acme=ghp_acme_token
GITHUB_ORG_TOKEN_widgets=ghp_widgets_token
```

This is useful for:
- Different access levels per org
- Rate limit management
- Security isolation

### Message Templates

Use `{field_name}` placeholders in messages:

```yaml
message: |
  🚨 {repository} Alert
  Issue #{issue_number}: {issue_title}
  Reporter: {sender}
  URL: {issue_url}
  
  Action required!
```

**Available in messages:**
- All normalized fields
- Special: `{compare_url}`, `{commit_url}` for push events

### Platform-Specific Filters

Apply filters to only one platform:

```yaml
- name: "GitHub Actions Failed"
  platform: [github]  # GitHub only
  events: [workflow_run]
  conditions:
    workflow_conclusion:
      equals: "failure"
  notify: true
```

## 📋 Example Use Cases

### 1. Security Monitoring

```yaml
- name: "Security Issues"
  platform: [github, gitlab]
  events: [issues, issue]
  conditions:
    labels:
      contains: "security"
  notify: true
  message: "🔒 Security issue #{issue_number} in {repository}: {issue_title}"
```

### 2. Production Deployment Tracking

```yaml
- name: "Production Deployments"
  platform: [github]
  events: [push]
  conditions:
    ref:
      equals: "refs/heads/production"
  notify: true
  message: "🚀 Deployment to production: {repository} by {sender}"
```

### 3. Large PR Warning

```yaml
- name: "Large Pull Requests"
  platform: [github, gitlab]
  events: [pull_request, merge_request]
  conditions:
    pr_changes:
      greater_than: 500
  notify: true
  message: "⚠️ Large PR ({pr_changes} files) in {repository}: {pr_title}"
```

### 4. Keyword Mention Tracking

```yaml
- name: "Technical Debt Mentions"
  platform: [github, gitlab]
  events: [issues, pull_request, push, issue, merge_request]
  any_of:
    - issue_title:
        contains: "tech debt"
    - pr_title:
        contains: "tech debt"
    - commit_messages:
        contains: "tech debt"
  notify: true
  message: "📝 Tech debt mentioned in {repository}"
```

### 5. Configuration File Changes

```yaml
- name: "Config Changed with Secrets"
  platform: [github, gitlab]
  events: [push]
  conditions:
    modified_files:
      contains: ".env.example"
    file_content_contains:
      contains: ["DATABASE", "PASSWORD", "SECRET"]
  notify: true
  message: "⚠️ Environment config changed in {repository}: {compare_url}"
```

## 🔔 Notification Channels

### Slack

```bash
# .env
NOTIFICATION_CHANNEL=slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

**Create a webhook URL:**
1. Go to https://api.slack.com/apps
2. Create new app → Incoming Webhooks
3. Activate and create webhook for your channel
4. Copy the webhook URL

### Email

```bash
# .env
NOTIFICATION_CHANNEL=email
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=notifications@example.com
EMAIL_SMTP_PASSWORD=your_app_password
EMAIL_FROM_ADDRESS=notifications@example.com
EMAIL_TO_ADDRESSES=team@example.com,alerts@example.com
```

**Gmail setup:**
1. Enable 2FA on your account
2. Generate an App Password
3. Use that password in `EMAIL_SMTP_PASSWORD`

## 🛠️ Development

### Project Structure

```
github-webhook/
├── main.py                 # Flask app entry point
├── config.yaml            # Filter configuration
├── .env                   # Secrets (gitignored)
├── pyproject.toml         # Project config, dependencies, and tool settings
├── requirements.txt       # Pinned production dependencies
├── dev-requirements.txt   # Pinned dev dependencies
├── helpers/
│   ├── normalizer.py      # Data normalization
│   ├── filter_engine.py   # Filter evaluation
│   ├── file_content_fetcher.py  # API file fetching
│   ├── handler/
│   │   ├── base.py        # Abstract webhook handler
│   │   ├── github.py      # GitHub implementation
│   │   └── gitlab.py      # GitLab implementation
│   └── notification/
│       ├── base.py        # Abstract notification
│       ├── factory.py     # Channel factory
│       ├── slack.py       # Slack implementation
│       └── email.py       # Email implementation
└── events/                # Logged webhook events (gitignored)
```

📘 **See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup guide.**

### Running Tests

```bash
# Install dev dependencies
make dev-install

# Run all tests
make test

# Run with coverage
make test-cov

# Lint and format code
make lint-fix
make format
```

### Debugging

**Event logs:**
All webhook events are saved to `events/*.json` files. Use these to:
- Debug filter rules
- Understand payload structure
- Test normalization

**Enable verbose logging:**
```python
# main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test filters locally:**
```python
from helpers.filter_engine import FilterEngine
from helpers.normalizer import EventNormalizer

# Load a sample event
with open('events/issues.json') as f:
    data = json.load(f)

# Normalize
normalized = EventNormalizer.normalize_github(data, 'issues')

# Test filter
engine = FilterEngine()
result = engine.evaluate_filter(normalized, your_filter_config)
print(f"Match: {result}")
```

## 🚀 Deployment

### Using Docker

```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:5000"]
```

```bash
docker build -t webhook-handler .
docker run -p 5000:5000 --env-file .env webhook-handler
```

### Using systemd

Create `/etc/systemd/system/webhook-handler.service`:

```ini
[Unit]
Description=Webhook Handler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/webhook-handler
EnvironmentFile=/opt/webhook-handler/.env
ExecStart=/usr/local/bin/hypercorn main:app --bind 0.0.0.0:5000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable webhook-handler
systemctl start webhook-handler
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name webhooks.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Using Caddy (Auto HTTPS)

```
webhooks.example.com {
    reverse_proxy localhost:5000
}
```

## 🔐 Security Best Practices

1. **Always use HTTPS** for webhook endpoints
2. **Verify signatures** - never disable verification
3. **Rotate secrets** periodically
4. **Limit token scopes** - only grant necessary permissions
5. **Use environment variables** - never commit secrets
6. **Rate limit** - implement rate limiting in production
7. **Monitor logs** - watch for suspicious activity
8. **Validate input** - all webhook data is untrusted

## 🤝 Contributing

Contributions welcome! To add features:

### Adding a New Platform

1. Create `helpers/handler/yourplatform.py`:
```python
class YourPlatformHandler(WebhookHandler):
    def verify_signature(self, payload, signature):
        # Implement verification
        pass
    
    def normalize_data(self, data, event_type):
        return EventNormalizer.normalize_yourplatform(data, event_type)
```

2. Add normalization in `helpers/normalizer.py`

3. Register in `main.py`

### Adding a Notification Channel

1. Create `helpers/notification/yourchannel.py`:
```python
class YourChannelNotification(NotificationChannel):
    def send(self, message, event_data=None):
        # Implement sending
        pass
```

2. Register in `helpers/notification/factory.py`

## 📚 Additional Resources

- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [GitLab Webhooks Documentation](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [Architecture Documentation](ARCHITECTURE.md) - Deep dive into system design

## 📝 License

[Your License Here]

## 💬 Support

- Issues: [GitHub Issues](your-repo-issues-url)
- Discussions: [GitHub Discussions](your-repo-discussions-url)

## 🎉 Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [PyYAML](https://pyyaml.org/) - Configuration parsing
- [Requests](https://requests.readthedocs.io/) - HTTP client
