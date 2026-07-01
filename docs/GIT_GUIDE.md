# Git & Versioning — Simple Guide (Hinglish)

Ye guide aapke liye hai. Git me bilkul naye ho to bas itna hi kaafi hai shuru me.

## Concepts (2 min)

- **Commit** = kaam ka "save point". Chhote-chhote commits achhe.
- **Branch** = alag line jaha experiment karo bina `main` toade.
- **Tag / Release** = ek version ka naam, jaise `v0.1.0`. **Yahi "version" hai.**
- **Remote (GitHub)** = online copy, backup + sharing.

## Versioning scheme — Semantic Versioning

`vMAJOR.MINOR.PATCH`  → jaise `v0.2.1`
- **MAJOR** = bada breaking change (abhi 0, kyunki development chal rahi hai)
- **MINOR** = naya feature (`v0.1.0` → `v0.2.0`)
- **PATCH** = chhota fix (`v0.2.0` → `v0.2.1`)

## Roz ke commands

```bash
git status                 # kya kya badla dekho
git add .                  # saare changes stage karo
git commit -m "message"    # save point banao
git log --oneline          # history dekho
```

## Naya version (release) banana

```bash
# 1. kaam commit karo
git add .
git commit -m "feat: agent core + chat"

# 2. version tag lagao
git tag -a v0.2.0 -m "v0.2.0 — agent core"

# 3. GitHub pe bhejo (code + tags dono)
git push
git push --tags
```

## Version SWITCH karna (aapka sawaal)

```bash
# purane version pe jao (sirf dekhne/test ke liye)
git checkout v0.1.0

# wapas latest pe aao
git checkout main
```

> Note: `git checkout v0.1.0` "detached HEAD" me le jaata hai — sirf dekhne ke liye
> theek hai. Agar us purane version se kaam aage badhana ho to nayi branch banao:
> `git checkout -b fix-from-v0.1.0 v0.1.0`

## Branch se feature banana (safe tareeka)

```bash
git checkout -b feature/leave-agent   # nayi branch
# ...kaam + commits...
git checkout main
git merge feature/leave-agent         # main me le aao
```

## GitHub se pehli baar connect (ek baar)

```bash
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
git push --tags
```

## Version history (is project ki)

| Version | Kya aaya |
|---|---|
| v0.1.0 | Foundation — repo, backend skeleton, frontend + amber theme, Groq key pool, keep-alive |
