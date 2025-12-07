# System Architecture

This document describes the technical architecture of the Unified Webhook Handler system that processes webhooks from multiple Git platforms (GitHub, GitLab) using a common filtering and notification framework.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified Webhook Handler System                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐                                      ┌──────────────┐
│   GitHub     │                                      │   GitLab     │
│   Events     │                                      │   Events     │
└──────┬───────┘                                      └──────┬───────┘
       │                                                     │
       │ POST /github/webhook                               │ POST /gitlab/webhook
       │ X-Github-Event: issues                             │ X-Gitlab-Event: Issue Hook
       │ X-Hub-Signature-256: HMAC                          │ X-Gitlab-Token: Secret
       │                                                     │
       ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            main.py                                   │
│                         Flask Application                            │
└──────┬───────────────────────────────────────────┬──────────────────┘
       │                                            │
       ▼                                            ▼
┌──────────────────────┐                  ┌────────────────────────┐
│  GitHubWebhookHandler│                  │  GitLabWebhookHandler  │
│                      │                  │                        │
│  1. Verify HMAC-256  │                  │  1. Verify token       │
│  2. Extract event    │                  │  2. Extract event      │
│  3. Normalize data   │                  │  3. Normalize data     │
│  4. Process event    │                  │  4. Process event      │
└──────────┬───────────┘                  └───────────┬────────────┘
           │                                          │
           └──────────────────┬───────────────────────┘
                              │
                              ▼
                     ┌────────────────┐
                     │ EventNormalizer│
                     │                │
                     │ Platform-      │
                     │ agnostic data  │
                     └────────┬───────┘
                              │
                              │ Normalized Event:
                              │ {
                              │   "platform": "github|gitlab",
                              │   "event_type": "issues",
                              │   "repository": "org/repo",
                              │   "issue_title": "...",
                              │   "sender": "...",
                              │   ...
                              │ }
                              │
                              ▼
                     ┌────────────────┐
                     │ WebhookHandler │
                     │   (Base)       │
                     │                │
                     │ process_event()│
                     └────────┬───────┘
                              │
                              ▼
                     ┌────────────────┐
                     │ FilterEngine   │
                     │                │
                     │ • Match events │
                     │ • Eval filters │
                     │ • Fetch files  │
                     └────────┬───────┘
                              │
                              │ Match found?
                              │
                              ▼
                     ┌────────────────────┐
                     │ NotificationFactory│
                     │                    │
                     │ Create channel     │
                     └─────────┬──────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
          ┌───────────────┐        ┌───────────────┐
          │SlackNotification│      │EmailNotification│
          │                │        │                │
          │ • Webhook POST │        │ • SMTP Send    │
          └───────────────┘        └───────────────┘
```

## Component Details

### 1. Entry Point: `main.py`

The Flask application that:
- Loads configuration from `config.yaml` and `.env`
- Initializes notification channels (Slack/Email)
- Creates platform-specific webhook handlers
- Filters configurations per platform
- Sets up file content fetcher for advanced filtering

**Key responsibilities:**
- Application bootstrap
- Dependency injection
- Environment configuration
- Route registration

### 2. Handler Layer

#### `WebhookHandler` (Base Class)
**Location:** `helpers/handler/base.py`

Abstract base class providing:
- Flask endpoint registration
- Event processing pipeline
- Filter evaluation coordination
- Notification triggering
- Event logging to JSON files

**Abstract methods** (must be implemented by subclasses):
- `register_endpoint()` - Set up Flask route
- `verify_signature()` - Validate webhook authenticity
- `get_event_info()` - Extract event type and action
- `normalize_data()` - Convert to unified format

**Concrete methods:**
- `process_event()` - Main processing pipeline
- `check_and_notify()` - Filter evaluation and notification dispatch
- `log_to_file()` - Persist events for debugging

#### `GitHubWebhookHandler`
**Location:** `helpers/handler/github.py`

Implements GitHub-specific logic:
- **Signature verification:** HMAC-SHA256 with `X-Hub-Signature-256` header
- **Event extraction:** From `X-Github-Event` header
- **Normalization:** Delegates to `EventNormalizer.normalize_github()`

**Supported events:**
- `issues`, `pull_request`, `push`, `workflow_run`, `workflow_job`, `release`, `deployment`, etc.

#### `GitLabWebhookHandler`
**Location:** `helpers/handler/gitlab.py`

Implements GitLab-specific logic:
- **Token verification:** Compares `X-Gitlab-Token` header with secret
- **Event extraction:** From `X-Gitlab-Event` header (mapped to normalized names)
- **Normalization:** Delegates to `EventNormalizer.normalize_gitlab()`

**Supported events:**
- `Issue Hook` → `issue`, `Merge Request Hook` → `merge_request`, `Push Hook` → `push`, `Pipeline Hook` → `pipeline`, etc.

### 3. Normalization Layer

#### `EventNormalizer`
**Location:** `helpers/normalizer.py`

Converts platform-specific webhook payloads to a unified schema.

**Design principle:** Write filters once, work on all platforms.

**Common normalized fields:**
```python
{
    'platform': 'github' | 'gitlab',
    'event_type': str,  # Normalized event name
    'action': str,      # opened, closed, merged, etc.
    'repository': str,  # org/repo format
    'repository_url': str,
    'sender': str,      # Username
    
    # Issue fields
    'issue_number': int,
    'issue_title': str,
    'issue_body': str,
    'issue_url': str,
    
    # Pull/Merge Request fields
    'pr_number': int,
    'pr_title': str,
    'pr_body': str,
    'pr_url': str,
    'pr_changes': int,
    'target_branch': str,
    'source_branch': str,
    
    # Push fields
    'ref': str,
    'commits': int,
    'modified_files': List[str],
    'commit_messages': List[str],
    'compare_url': str,
    
    # Workflow fields
    'workflow_name': str,
    'workflow_status': str,
    'workflow_conclusion': str,
    
    # Labels
    'labels': List[str],
    
    # Raw data for advanced use
    'raw_data': dict
}
```

**Platform mappings:**

| GitHub | GitLab | Normalized |
|--------|--------|------------|
| `repository.full_name` | `project.path_with_namespace` | `repository` |
| `issue.number` | `object_attributes.iid` | `issue_number` |
| `pull_request.title` | `object_attributes.title` | `pr_title` |
| `pull_request.changed_files` | `changes_count` | `pr_changes` |
| `sender.login` | `user.username` | `sender` |

### 4. Filter Engine

#### `FilterEngine`
**Location:** `helpers/filter_engine.py`

Powerful, flexible filtering system supporting:

**Condition types:**
- `contains` - Substring match (case-insensitive)
- `equals` - Exact match
- `in` - Value in list
- `regex` - Regular expression
- `greater_than` / `less_than` - Numeric comparison
- `starts_with` / `ends_with` - String prefix/suffix

**Special features:**
- **List handling:** Automatically handles list fields (e.g., `modified_files`, `labels`)
- **File content inspection:** Can fetch file contents from GitHub/GitLab to match patterns
- **Dot notation:** Access nested fields with `field.subfield`
- **ANY/ALL logic:** Support both OR (`any_of`) and AND (`conditions`) operations

**Filter evaluation flow:**
```python
1. Check if event type matches filter.events
2. Check if platform matches filter.platform
3. Evaluate all conditions (AND logic)
   OR evaluate any_of conditions (OR logic)
4. If file_content_contains specified:
   - Fetch file from GitHub/GitLab API
   - Check if pattern exists in content
5. If all checks pass, format and send message
```

**Example filter:**
```yaml
- name: "Critical File Changed"
  platform: [github, gitlab]
  events: [push]
  conditions:
    modified_files:
      contains: "production.yaml"
  file_content_contains:
    contains: "database_password"
  notify: true
  message: "⚠️ Sensitive file modified in {repository}"
```

### 5. Notification System

#### `NotificationFactory`
**Location:** `helpers/notification/factory.py`

Factory pattern for creating notification channels:
```python
NotificationFactory.create('slack', config)
NotificationFactory.create('email', config)
```

#### `SlackNotification`
**Location:** `helpers/notification/slack.py`

Sends messages to Slack via webhook URL.

**Configuration:**
- `webhook_url` (required)
- `channel` (optional - webhook default)
- `username` (optional - webhook default)

**Message format:** Supports Slack markdown (`<url|text>`)

#### `EmailNotification`
**Location:** `helpers/notification/email.py`

Sends emails via SMTP.

**Configuration:**
- `smtp_host`, `smtp_port`
- `smtp_user`, `smtp_password`
- `from_address`
- `to_addresses` (list)

### 6. File Content Fetcher

#### `FileContentFetcher`
**Location:** `helpers/file_content_fetcher.py`

Fetches file contents from repositories for advanced filtering.

**Features:**
- GitHub API integration (supports per-org tokens)
- GitLab API integration
- Caching (optional)
- Error handling

**Usage in filters:**
```yaml
conditions:
  modified_files:
    contains: "config.yaml"
  file_content_contains:
    contains: "secret_key"
```

When this filter is evaluated:
1. System detects `file_content_contains` condition
2. Extracts filename from `modified_files`
3. Uses FileContentFetcher to get file content
4. Checks if pattern exists in content

## Data Flow Example

### Scenario: GitHub Issue Opened with Keyword

```
1. GitHub Event Received
   POST /github/webhook
   {
     "action": "opened",
     "issue": {
       "number": 42,
       "title": "Fix shalut configuration",
       "body": "The shalut service is failing..."
     },
     "repository": { "full_name": "acme/api" },
     "sender": { "login": "alice" }
   }

2. GitHubWebhookHandler
   - Verify HMAC signature ✓
   - Extract event: "issues"
   - Call normalize_data()

3. EventNormalizer.normalize_github()
   Returns:
   {
     "platform": "github",
     "event_type": "issues",
     "action": "opened",
     "repository": "acme/api",
     "issue_number": 42,
     "issue_title": "Fix shalut configuration",
     "issue_body": "The shalut service is failing...",
     "sender": "alice",
     ...
   }

4. WebhookHandler.process_event()
   - Log to events/issues.json
   - Call check_and_notify()

5. FilterEngine.evaluate()
   Filter: "Shalut Mention"
   - events: [issues] ✓
   - platform: [github] ✓
   - any_of:
     - issue_title contains "shalut" ✓ MATCH!
   
6. NotificationFactory
   - Format message: "🔔 'shalut' mentioned in acme/api by alice"
   - Get Slack channel
   - Send notification

7. SlackNotification.send()
   POST https://hooks.slack.com/...
   {
     "text": "🔔 'shalut' mentioned in acme/api by alice",
     "icon_emoji": ":bell:"
   }
```

### Scenario: GitLab Push with File Content Check

```
1. GitLab Event Received
   POST /gitlab/webhook
   {
     "object_kind": "push",
     "project": { "path_with_namespace": "acme/frontend" },
     "commits": [
       { "added": ["config/production.yaml"], "message": "Update config" }
     ],
     "user_username": "bob"
   }

2. GitLabWebhookHandler
   - Verify token ✓
   - Extract event: "Push Hook" → "push"
   - Call normalize_data()

3. EventNormalizer.normalize_gitlab()
   Returns:
   {
     "platform": "gitlab",
     "event_type": "push",
     "repository": "acme/frontend",
     "modified_files": ["config/production.yaml"],
     "sender": "bob",
     ...
   }

4. FilterEngine.evaluate()
   Filter: "Production Config Changed"
   - events: [push] ✓
   - platform: [gitlab] ✓
   - conditions:
     - modified_files contains "production.yaml" ✓
     - file_content_contains: "api_key"
       
5. FileContentFetcher.fetch_file_content()
   - API call to GitLab
   - GET /api/v4/projects/.../repository/files/config%2Fproduction.yaml
   - Returns file content
   - Check if "api_key" in content ✓ MATCH!

6. Send notification
   "📝 Production config with api_key modified in acme/frontend by bob"
```

## Configuration System

### Environment Variables (`.env`)

```bash
# Platform secrets
GITHUB_WEBHOOK_SECRET=sha256_secret_here
GITLAB_WEBHOOK_TOKEN=token_here

# API tokens for file fetching
GITHUB_TOKEN=ghp_xxxxx
GITLAB_TOKEN=glpat-xxxxx

# Per-organization GitHub tokens (optional)
GITHUB_ORG_TOKEN_acme=ghp_yyyyy
GITHUB_ORG_TOKEN_widgets=ghp_zzzzz

# Notification channel
NOTIFICATION_CHANNEL=slack  # or 'email'

# Slack config
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ

# Email config
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=notifications@example.com
EMAIL_SMTP_PASSWORD=app_password
EMAIL_FROM_ADDRESS=notifications@example.com
EMAIL_TO_ADDRESSES=team@example.com,alerts@example.com
```

### Filter Configuration (`config.yaml`)

```yaml
filters:
  # Simple keyword filter - works on both platforms
  - name: "Mention Detection"
    platform: [github, gitlab]  # Apply to both
    events: [issues, issue, pull_request, merge_request]
    any_of:  # OR logic - match ANY condition
      - issue_title:
          contains: "urgent"
      - pr_title:
          contains: "urgent"
    notify: true
    message: "🚨 Urgent item in {repository}: {issue_title}{pr_title}"
  
  # Push event with file content check
  - name: "Secrets in Code"
    platform: [github]
    events: [push]
    conditions:  # AND logic - match ALL conditions
      modified_files:
        contains: ".py"
    file_content_contains:
      contains: ["password", "secret_key", "api_key"]
    notify: true
    message: "⚠️ Potential secret in {repository} by {sender}"
  
  # Workflow monitoring
  - name: "Build Failures"
    platform: [github]
    events: [workflow_run]
    conditions:
      workflow_conclusion:
        equals: "failure"
    notify: true
    message: "❌ Build failed: {workflow_name} in {repository}"
  
  # Label-based routing
  - name: "Security Issues"
    platform: [github, gitlab]
    events: [issues, issue]
    conditions:
      labels:
        contains: "security"
    notify: true
    message: "🔒 Security issue #{issue_number} in {repository}"
```

## Design Principles

### 1. Platform Abstraction
The `EventNormalizer` creates a unified data model, allowing filters to be written once and work on all platforms. This dramatically reduces configuration complexity.

### 2. Composable Filters
Filters use simple condition operators (`contains`, `equals`, etc.) that can be combined with AND/OR logic. This makes complex rules readable and maintainable.

### 3. Security by Design
- Webhook signatures verified using cryptographic methods
- Secrets stored in environment variables
- API tokens support per-organization scoping

### 4. Extensibility
- Add new platforms by implementing `WebhookHandler` subclass
- Add new notification channels by implementing `NotificationChannel`
- Add new filter conditions in `FilterEngine`

### 5. Observability
- All events logged to JSON files
- Detailed console logging
- Notification delivery tracking

## Extension Points

### Adding a New Platform (e.g., Bitbucket)

1. Create `helpers/handler/bitbucket.py`:
```python
class BitbucketWebhookHandler(WebhookHandler):
    def verify_signature(self, payload, signature):
        # Bitbucket-specific verification
        pass
    
    def normalize_data(self, data, event_type):
        return EventNormalizer.normalize_bitbucket(data, event_type)
```

2. Add normalization in `helpers/normalizer.py`:
```python
@staticmethod
def normalize_bitbucket(data, event_type):
    # Map Bitbucket fields to unified schema
    return { ... }
```

3. Register in `main.py`:
```python
bitbucket_handler = BitbucketWebhookHandler(...)
```

### Adding a New Notification Channel (e.g., Discord)

1. Create `helpers/notification/discord.py`:
```python
class DiscordNotification(NotificationChannel):
    def send(self, message, event_data=None):
        # Send to Discord webhook
        pass
```

2. Register in `helpers/notification/factory.py`:
```python
if channel_type == 'discord':
    return DiscordNotification(config)
```

## Performance Considerations

- **Webhook processing:** Synchronous (blocks until filters evaluated)
- **File fetching:** May add latency for `file_content_contains` filters
- **Notification sending:** Synchronous (consider async for production)
- **Event logging:** I/O operation per event (consider batching)

## Security Considerations

- **Always verify signatures** before processing webhooks
- **Use environment variables** for secrets
- **Validate input data** before normalization
- **Rate limit** webhook endpoints in production
- **Rotate tokens** periodically
- **Use HTTPS** for all webhook endpoints

## Testing Strategy

1. **Unit tests:** Test normalizers, filter engine, handlers independently
2. **Integration tests:** Use sample event JSONs from `events/` directory
3. **Manual testing:** Use webhook testing tools (e.g., ngrok + curl)
4. **Validation:** Check `events/*.json` logs for debugging

## Deployment Architecture

```
┌─────────────┐
│   GitHub    │──┐
│   GitLab    │  │
└─────────────┘  │
                 │ HTTPS
                 │
                 ▼
          ┌─────────────┐
          │   Reverse   │
          │   Proxy     │ (nginx/Caddy)
          │   (HTTPS)   │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │   Flask     │
          │   App       │ (Hypercorn/Gunicorn)
          │   (ASGI)    │
          └──────┬──────┘
                 │
                 ├─> Slack Webhook
                 └─> SMTP Server
```

**Recommended stack:**
- Web server: Caddy (auto HTTPS) or nginx
- ASGI server: Hypercorn (async) or Gunicorn + uvicorn
- Process manager: systemd or Docker
- Monitoring: Prometheus + Grafana

## Future Enhancements

- [ ] Async webhook processing (celery, Redis)
- [ ] Database storage for events (PostgreSQL)
- [ ] Web UI for filter management
- [ ] Metric collection (Prometheus)
- [ ] Rate limiting and throttling
- [ ] Webhook retry logic
- [ ] Multi-tenancy support
- [ ] Filter testing UI
- [ ] Notification templating engine
- [ ] Conditional notification routing
