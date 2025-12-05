# GitHub Repository Setup Guide

This document outlines the recommended GitHub repository settings and configurations that should be set up in the GitHub UI.

## 📋 Repository Settings (GitHub UI)

### 1. Repository Description

Go to **Settings → General → Repository details**

**Description:**
```
🤖 Automated research report generation powered by Large Language Models. Generates comprehensive, citation-backed research reports in 30-90 seconds using Flask and OpenRouter API.
```

**Website (if you have one):**
```
https://your-demo-url.com
```

**Topics/Tags** (for discoverability):
```
ai
research
llm
flask
python
openrouter
automation
research-tools
citation
academic
nlp
machine-learning
report-generation
```

### 2. Features

Go to **Settings → General → Features**

Enable:
- ✅ **Issues** - For bug reports and feature requests
- ✅ **Discussions** - For community discussions
- ✅ **Projects** - For project management (optional)
- ✅ **Wiki** - For additional documentation (optional)
- ✅ **Sponsorships** - If you want to accept sponsorships

### 3. Branch Protection

Go to **Settings → Branches → Branch protection rules**

Add rule for `main` branch:
- ✅ Require a pull request before merging
- ✅ Require approvals (1 reviewer)
- ✅ Require status checks to pass before merging
  - Select: `test` and `lint` (from CI workflow)
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

### 4. Actions Settings

Go to **Settings → Actions → General**

- ✅ Allow all actions and reusable workflows
- ✅ Allow GitHub Actions to create and approve pull requests
- ✅ Workflow permissions: Read and write permissions

### 5. Security

Go to **Settings → Security**

- Enable **Dependency graph**
- Enable **Dependabot alerts**
- Enable **Dependabot security updates**
- Enable **Code scanning** (optional, requires GitHub Advanced Security)

### 6. Pages (Optional)

Go to **Settings → Pages**

If you want to host documentation:
- Source: Deploy from a branch
- Branch: `main` or `gh-pages`
- Folder: `/docs` or `/root`

### 7. Social Preview

Go to **Settings → General → Social preview**

Upload a custom image (1200x630px) for social media previews.

## 🏷️ Labels

Go to **Issues → Labels** and create:

**Type Labels:**
- `bug` - Something isn't working (red)
- `enhancement` - New feature or request (green)
- `documentation` - Documentation improvements (blue)
- `question` - Further information is requested (purple)

**Priority Labels:**
- `priority: high` - High priority (red)
- `priority: medium` - Medium priority (orange)
- `priority: low` - Low priority (yellow)

**Status Labels:**
- `good first issue` - Good for newcomers (green)
- `help wanted` - Extra attention is needed (purple)
- `wontfix` - This will not be worked on (gray)

## 📊 Insights & Analytics

### Enable Insights

Go to **Insights** tab:
- View traffic statistics
- Monitor contributors
- Track repository activity

## 🔗 Badges (Already in README)

The README already includes badges. To make them dynamic:

1. **Build Status** (after CI is set up):
   ```markdown
   ![CI](https://github.com/sgogi1/research_agent/workflows/CI/badge.svg)
   ```

2. **Code Coverage** (if using Codecov):
   ```markdown
   ![codecov](https://codecov.io/gh/sgogi1/research_agent/branch/main/graph/badge.svg)
   ```

3. **Latest Release**:
   ```markdown
   ![GitHub release](https://img.shields.io/github/v/release/sgogi1/research_agent?style=for-the-badge)
   ```

4. **Stars**:
   ```markdown
   ![GitHub stars](https://img.shields.io/github/stars/sgogi1/research_agent?style=for-the-badge)
   ```

5. **Forks**:
   ```markdown
   ![GitHub forks](https://img.shields.io/github/forks/sgogi1/research_agent?style=for-the-badge)
   ```

## 📝 README Badge Updates

Update the README badges section with dynamic badges:

```markdown
![CI](https://github.com/sgogi1/research_agent/workflows/CI/badge.svg)
![codecov](https://codecov.io/gh/sgogi1/research_agent/branch/main/graph/badge.svg)
![GitHub release](https://img.shields.io/github/v/release/sgogi1/research_agent?style=for-the-badge)
![GitHub stars](https://img.shields.io/github/stars/sgogi1/research_agent?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/sgogi1/research_agent?style=for-the-badge)
```

## ✅ Checklist

- [ ] Set repository description
- [ ] Add topics/tags
- [ ] Enable Issues
- [ ] Enable Discussions
- [ ] Set up branch protection for `main`
- [ ] Configure Actions settings
- [ ] Enable security features
- [ ] Create labels
- [ ] Add social preview image
- [ ] Update README with dynamic badges (after first CI run)
- [ ] Create first release tag (v1.0.0)

## 🎯 Next Steps

1. **First Release**: Create a release tag `v1.0.0`
   - Go to **Releases → Create a new release**
   - Tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: Copy from CHANGELOG.md

2. **Enable Discussions**: Create categories for:
   - General
   - Q&A
   - Ideas
   - Show and tell

3. **Add Topics**: Make sure all relevant topics are added for discoverability

4. **Social Media**: Share the repository on:
   - Twitter/X
   - LinkedIn
   - Reddit (relevant subreddits)
   - Dev.to / Medium

## 📚 Additional Resources

- [GitHub Community Guidelines](https://docs.github.com/en/github/site-policy/github-community-guidelines)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

