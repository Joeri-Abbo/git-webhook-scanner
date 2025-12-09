# Dependabot Auto-Merge Workflows

## Current Setup

### `dependabot-auto-approve.yml` (Active)
✅ **Enables auto-merge** for Dependabot PRs (patch & minor updates)  
❌ **Cannot approve PRs** (GitHub Actions limitation)

**What it does:**
- Detects Dependabot PRs
- Enables auto-merge for patch/minor updates
- Adds helpful comments
- Waits for all checks to pass, then merges automatically

**Important**: This workflow does NOT approve PRs because GitHub Actions cannot approve PRs using `GITHUB_TOKEN`. This is a security restriction.

### Solutions if You Need Approvals

#### Option 1: No Approval Required (Recommended)
Don't require approvals in your branch protection rules. Auto-merge will work when checks pass.

#### Option 2: Manual Approval
Manually approve Dependabot PRs. Once you approve + checks pass, auto-merge triggers.

#### Option 3: Use Personal Access Token (Advanced)
1. Create a PAT at https://github.com/settings/tokens/new
   - Select: `repo` (full control of private repositories)
2. Add as repository secret:
   - Go to: Settings → Secrets and variables → Actions
   - Name: `DEPENDABOT_APPROVE_TOKEN`
   - Value: Your PAT
3. Rename: `dependabot-auto-approve-with-pat.yml.example` → `dependabot-auto-approve-with-pat.yml`
4. Disable the original workflow

⚠️ **Security Note**: Using a PAT gives the workflow more permissions. Only do this if necessary.

## How Auto-Merge Works

```
1. Dependabot creates PR
   ↓
2. Workflow enables auto-merge (patch/minor only)
   ↓
3. CI runs: tests, linting, docker build
   ↓
4. All checks pass? → Merges automatically
   Any check fails? → PR stays open
```

## What Gets Auto-Merged?

| Update Type | Example | Auto-Merge? |
|-------------|---------|-------------|
| Patch | `flask 3.0.3 → 3.0.4` | ✅ Yes |
| Minor | `flask 3.0.0 → 3.1.0` | ✅ Yes |
| Major | `flask 3.0.0 → 4.0.0` | ❌ No (manual) |

## Disabling Auto-Merge

**For one PR:**
```bash
gh pr merge --disable-auto <PR-number>
```

**Disable workflow:**
Delete or rename the workflow file.
