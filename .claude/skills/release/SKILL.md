---
name: release
description: Release a new version of the ONLYOFFICE Telegram bot. Covers the version bump in CHANGELOG.md, translations, submodules, checks, the Release PR from develop to master, the tag and GitHub Release, Docker Hub images and BotFather. Use when asked to release, cut a version, bump the version or publish the bot.
---

# Release the ONLYOFFICE Telegram bot

The version source of truth is the **first `## X.Y.Z` heading in `CHANGELOG.md`**. CI derives everything from it: RC image tags, the git tag and the GitHub Release.

Ask the maintainer before every outward step: pushing, opening or merging a PR, tagging. Never push or merge on your own initiative.

## 0. Pick the version

- Ask the maintainer for the version, or propose one with SemVer: patch for fixes and format/template updates, minor for features.
- Collect the changes since the last tag: `git log --oneline v<previous>..develop`.

## 1. Sync branches

```bash
git fetch origin
git switch develop && git pull
git merge origin/master        # master may carry commits develop lacks (e.g. issue templates)
git submodule update --init
```

## 2. Update upstream data (when the release should pick up new formats or templates)

```bash
git submodule update --remote static/assets/document-formats      # upstream master
git submodule update --remote static/assets/document-templates    # branch main/new-2letter-code (.gitmodules)
git diff --submodule=log
```

- If `onlyoffice-docs-formats.json` changed, update the format lists in `README.md` (Editable / View-only / Conversion) and mention it in the changelog.
- New template language folders work automatically. Bot UI languages are separate (`locales/`).

## 3. Translations (only if user-facing strings changed)

```bash
pybabel extract -k __ -o locales/messages.pot app
pybabel update -i locales/messages.pot -d locales -D messages
# get the new/changed msgids translated in every locales/*/LC_MESSAGES/messages.po
pybabel compile -d locales -D messages
```

- `-k __` is required. Without it the lazy button strings drop out of the catalog.
- Button pairs (`Create`/`create`, `Open`/`open`, `🔄 Convert`/`🔄 convert`, `⬅️ Back`/`⬅️ back`, `❌ Cancel`/`❌ cancel`) must translate consistently. The tests check this.
- Commit the updated `.po` and `.mo` files.

## 4. Bump the version

1. Add a section at the **top** of `CHANGELOG.md` in the existing style:
   ```markdown
   # Change Log

   ## X.Y.Z
   ## Added
   - ...
   ## Changed
   - ...
   ```
   `release.yml` uses the lines between the first and second `## <digit>` headings as the GitHub Release body.
2. Set `version = "X.Y.Z"` in `pyproject.toml` to keep it in sync.
3. Commit with the message `X.Y.Z`, as previous release commits do.

## 5. Check

```bash
python -m pytest
pre-commit run -a
docker build -t telegram-local .
```

All three must pass. `xfail` entries in the tests are known issues. An `XPASS(strict)` failure means one was fixed, so remove its marker.

## 6. Release candidate on the test deployment

1. **Ask the maintainer**, then push `develop`.
2. GitHub Actions `Build onlyoffice-telegram` pushes `onlyoffice/telegram:<X.Y.(Z+1)>-rc.<run>`. The script adds 1 to the patch of the CHANGELOG version, so for `## 1.2.0` the RC is `1.2.1-rc.N`; this is expected. Its `update` job calls the Flux webhook.
3. For a custom tag, run the workflow manually with input `tag`.
4. Run the **Manual verification checklist** from `HANDOVER.md` on the test bot. Do not continue until it passes.

## 7. Release PR and merge (manual)

1. Open a PR on `origin` named `Release/X.Y.Z` from `develop` into `master`.
2. Wait for approval and the `Licenses` check. Merge it **only on the maintainer's explicit OK**.

## 8. Automatic after the merge (verify each)

- `Create Tag` pushes tag `vX.Y.Z`. It is skipped if the push only touched `.github/**`, `README.md`, `AUTHORS.md` or `LICENSE`.
- `Release` creates the GitHub Release `vX.Y.Z` with the changelog section. Read it.
- Docker Hub gets `onlyoffice/telegram:stable-X.Y.Z`. No workflow in this repository produces this tag, so if it does not appear, raise it with DevOps.
- The production rollout is done by DevOps.

## 9. BotFather (manual, only when needed)

- Commands and descriptions in all languages are pushed by the bot at startup. No BotFather action is needed for them.
- Only if the public domain or Mini App name changed: in BotFather `/myapps`, select the bot's app and set the URL to `<WEB_APP_URL>/editor`; the short name must equal `WEB_APP_NAME`. Changes apply immediately, with no review.

## 10. Finish

```bash
git switch develop && git merge origin/master && git push   # ask first
```

Smoke-check the production bot: `/start`, create a document, edit it, close it and get the file back.
