# Git Workflow Standard (2-Developer Repository)

---

## 1. Core Branches

- **main** → Always stable, production-ready code  
- **dev (optional)** → Integration branch if staging is needed  

**Recommended for small teams (2 devs):**  <br>
Use only `main` + feature branches to keep workflow simple.

---

## 2. Branch Naming Convention

**Format**<br>
\<type\>/\<short-description\>

### Allowed Types

| Type | Purpose |
|-----|--------|
| feature | New functionality |
| fix | Bug fixes |
| hotfix | Urgent production fixes |
| refactor | Internal improvements |
| docs | Documentation only |
| test | Tests only |
| chore | Maintenance / tooling |

**Rules**
- lowercase only
- hyphen separated
- short but descriptive

**Examples**<br>
```feature/user-auth```<br>
```feature/appointment-booking```<br>
```fix/login-redirect```<br>
```refactor/api-services```<br>
```chore/update-dependencies```<br>

---

## 3. Branch Creation Policy

Always branch from updated base:
```bash
git checkout main
git pull origin main
git checkout -b feature/<name>
```


Rules:
- One branch = one task
- No mixed changes (feature + refactor + deps)
- Keep branches short-lived (1–3 days ideal)

---

## 4. Commit Message Standard

Format:<br>
\<type\>: \<message\>

**Types**
- feat
- fix
- refactor
- docs
- test
- chore

**Examples**<br>
```feat: add user registration endpoint```<br>
```fix: prevent null error in dashboard```<br>
```refactor: extract auth service```<br>
```chore: upgrade django version```

---

## 5. Pull Request Rules

All changes must go through PR review.

**PR must include**
- Clear title
- Description
- Testing steps
- Screenshots (if UI)

**Requirements**
- Code runs successfully
- Tests pass
- At least 1 reviewer approval

**Ideal PR size**<br>
< 300 lines changed

---

## 6. Keeping Branch Updated

Before pushing or opening PR:
```bash
git fetch origin
git merge origin/main
```

Merge is safer than rebase for small teams.

---

## 7. Merge Strategy

Recommended: **Squash & Merge**

Benefits:
- clean history
- removes WIP commits
- easier debugging

Alternative: Merge Commit (only if team prefers full history).

---

## 8. Conflict Prevention Rules

To reduce merge conflicts:
- Avoid editing same files simultaneously
- Assign module ownership
- Coordinate before changing shared core files

Example ownership:<br>
Dev A → auth/<br>
Dev B → dashboard/

---

## 9. Branch Deletion Policy

After merge:<br>
Delete remote branch on GitHub <br>
(Optional) delete local branch:
```bash
git branch -d feature/<name>
```

---

## 10. Optional Workflow with `dev` Branch

Use only if project complexity increases.

Flow:<br>
feature → dev → main

Meaning:
- Branch from `dev`
- Merge PR into `dev`
- Periodically merge `dev → main` for releases

---

## 11. Golden Rule

> Branch names and commit messages should explain purpose without opening the code.

If someone can understand project progress just by reading branch list, your workflow is correct.

---

## Recommended Minimal Workflow for This Project
main → stable code<br>
feature branches → all development work<br>
PR → review → merge → delete branch

Simple. Clean. Industry-standard.