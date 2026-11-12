# Handover: ONLYOFFICE bot for Telegram

Daily commands and rules are in `CLAUDE.md`. Releases are covered by the `release` skill (`.claude/skills/release/SKILL.md`). This document explains what the project is, how it works and why it is built this way.

## 1. Integration type

**A standalone service, not a plugin.** One Python process (aiogram 3 + aiohttp) runs a single HTTP server that:

- receives Telegram Bot API updates through a **webhook** (`WEB_APP_URL + WEBHOOK_PATH`, registered at startup in `main.py:on_startup`);
- serves a **Telegram Mini App**, the page `/editor` (`static/editor.html`). It opens from links like `https://t.me/<BOT_NAME>/<WEB_APP_NAME>?startapp=<session key>` and embeds the ONLYOFFICE editor;
- acts as the **file storage** for Document Server (`/editor/getFile`) and receives its **save callbacks** (`/editor/sendFile`).

All state lives in **Redis**: aiogram FSM, editing sessions, user language and anti-flood counters. The service has no database and no file storage of its own. Source files stay in Telegram (`file_id`). The result file goes back to the chat from a Document Server URL.

The only ONLYOFFICE product used is **ONLYOFFICE Docs (Document Server)**:

| Interaction | Code |
|---|---|
| Docs API (`/web-apps/apps/api/documents/api.js`) inside the Mini App | `static/editor.html` |
| Editor config signed with JWT (HS256, `JWT_SECRET`) | `app/routes/get_config.py` |
| DS downloads the source file. The URL carries `security_token`; DS's own JWT arrives in header `JWT_HEADER` | `app/routes/get_file.py` |
| Save callback: on status 2/3 the file is sent to the chat | `app/routes/send_file.py` |
| Conversion API (`ConvertService.ashx`, async, polled up to 5 × 5 s) | `app/handlers/convert_router.py` |

Two upstream ONLYOFFICE repositories are git submodules:
- `static/assets/document-formats` holds `onlyoffice-docs-formats.json`, the matrix of what can be viewed, edited and converted to what. The bot reads it at runtime.
- `static/assets/document-templates` holds blank `new.docx/xlsx/pptx/pdf` per language, from branch `main/new-2letter-code`.

**Supported versions**
- Python ≥ 3.11 (the Docker image is `python:3.11-slim`).
- Document Server: at minimum the release that was current at bot 1.1.0 (June 2026). Newer releases are expected to work. The formats submodule follows upstream DS format support.
- Telegram: Bot API via aiogram 3.15; Mini App via `telegram-web-app.js`.

Production deployment, the BotFather account and production secrets are handled by DevOps.

## 2. Key user scenarios

Private chat:
1. `/start` opens the reply-keyboard menu **Create / Open / 🔄 Convert / ❌ Cancel**. FSM states are in `app/fsm/menu_state.py`.
2. **Create**: choose Document / Spreadsheet / Presentation, then type a title (sanitized by `DocumentNameFilter`, 1–60 chars). The bot replies with a Mini App link. The file starts from the blank template for the user's language, falling back to `default`.
3. **Open**: send a file, either through the menu or by forwarding it to the bot without any command. The bot replies with a link. The mode is `edit` if the format's `actions` contain `edit`, otherwise `view`. Limit: 20 MB.
4. **Reopen**: reply to a message that contains a file with any text to get a new link.
5. **Co-editing**: forward the link message to others. Everyone who opens it joins the session's `members` and receives the final file.
6. **File return**: when everyone closes the editor, DS calls back. The bot sends the file to all members, edits the owner's link message to "expired" and deletes the session from Redis.
7. **Convert**: send a file, pick a target format from the keyboard (taken from `convert` in the formats matrix) and get the converted file back. Private chats only.
8. `/lang` changes the language (de, en, es, fr, it, ja, pt, ru, zh). The choice is stored in Redis `<user_id>:lang` with no TTL. The default is the Telegram profile language.
9. `/help`, `/cancel`, **⬅️ Back**.

Groups and supergroups:
10. `/document`, `/spreadsheet`, `/presentation` create a file named automatically, e.g. `New document 2026-01-02_03-04 PM UTC` (12-hour clock for some languages, 24-hour for the rest).
11. `/open` with a file, a reply to a file, or a mention of the bot with a file returns a link. The final file goes to the group, and in private to members who have left the group.
12. Without admin rights the bot sees only commands, mentions and replies addressed to it. See README "Using the bot in group chats".

Service behaviour:
13. A session lives `TTL` hours (default 24). Every opening of the link extends it (`get_config` calls `expire`).
14. Anti-flood: 5 messages less than 2 s apart get a warning and are ignored (`app/middlewares/antiflood.py`, constants in `config.py`).
15. Telegram Mini Apps analytics (tganalytics.xyz) are enabled only when `ANALYTICS_APP_NAME` and `ANALYTICS_TOKEN` are set.
16. At startup the bot sets its commands (private and group scopes) and its description in every locale (`app/commands`, `app/description`).

## 3. Build

- There is no compile step; this is plain Python. Install with `pip install -e .[dev]`. Dependencies are pinned twice, in `requirements.txt` (used by Docker and the license check) and `pyproject.toml`. Keep them identical.
- **Submodules are mandatory.** Without `document-formats` no file type is recognized; without `document-templates` creation fails. Run `git submodule update --init`. CI checks out with `submodules: recursive`. The tests stop with a clear message if submodules are missing.
- **Translations**: `messages.pot` is produced by `pybabel extract -k __ -o locales/messages.pot app`. The `-k __` matters because lazy strings use `__`; without it 5 msgids are lost. Then run `pybabel update` and `pybabel compile`. The compiled `.mo` files are committed. Exact commands are in `CLAUDE.md`.
- **Docker**: `Dockerfile` (`python:3.11-slim`, `python3 main.py`) and `docker-compose.yml` (bot + `redis`, network `onlyoffice`, port 8000). The env template is `.env.docker.example`.
- **Tooling**: pre-commit (ruff 0.9.1, ruff-format, black 24.10.0, standard hooks), `.pylintrc` for editors, pytest smoke tests in `tests/`.
- There are no private repositories or private dependencies. Everything comes from PyPI and public ONLYOFFICE GitHub repos.
- **CI** (GitHub Actions, `.github/workflows`):
  - `build.yaml`: on push to `develop` (or a manual run) it builds `onlyoffice/telegram:<version>-rc.<run>` for linux/amd64 and pushes it to Docker Hub. `<version>` comes from `ONLYOFFICE/ga-common/.github/scripts/get_connector_version.py`, which takes the first `## X.Y.Z` in `CHANGELOG.md` and **adds 1 to the patch number**. So after `## 1.1.0` the RC images are `1.1.1-rc.N`. A manual run with input `tag` uses that tag as is. The `update` job then sends an HMAC-signed POST to `secrets.TELEGRAM_WEBHOOK_URL`, the Flux hook (commit "Build: enable flux hook").
  - `create-tag.yml`: on push to `master` it creates tag `v<first version in CHANGELOG.md>`. Pushes that touch only `.github/**`, `AUTHORS.md`, `LICENSE` or `README.md` are ignored.
  - `release.yml`: on a `v*` tag it creates a GitHub Release whose body is the top CHANGELOG section.
  - `licenses.yml`: on push or PR to `master`/`develop` it runs `ONLYOFFICE/check-licenses` over `requirements.txt`. Approved exceptions are in `.check-licenses.yml`.
  - CI secrets referenced: `DOCKER_HUB_USERNAME`, `DOCKER_HUB_ACCESS_TOKEN`, `TELEGRAM_WEBHOOK_TOKEN`, `TELEGRAM_WEBHOOK_URL`. They live in GitHub Actions secrets (repository or organization level).
- `hooks/build|push|post_checkout` are Docker Hub Automated Builds hooks. They use `$DOCKER_TAG` and `docker-compose`.

## 4. Publishing

- **Docker Hub, `onlyoffice/telegram`**:
  - `X.Y.Z-rc.N` images come from `build.yaml` on every push to `develop`.
  - Release images are tagged `stable-X.Y.Z` (for example `stable-1.1.0`, pushed right after the 1.1.0 merge to `master`). No workflow in this repository produces this tag, so check that it appears after a release.
- **GitHub Release `vX.Y.Z`**: created automatically from `CHANGELOG.md` after the merge to `master`.
- **Telegram / BotFather**:
  - Commands (private and group), the long description and the short description in all bot languages are set **by the bot itself at startup**. There is nothing to do in BotFather for them. Edit the strings in code and translations.
  - The Mini App is registered once in BotFather (`/newapp`, managed under `/myapps`). Its short name must equal `WEB_APP_NAME` and its URL must be `WEB_APP_URL/editor`. Change it only if the domain or name changes.
  - BotFather changes apply immediately. There is no review step.

Step by step: `.claude/skills/release/SKILL.md`.

## 5. Implicit knowledge

**Why it is built this way**
- **Links are capability tokens.** Anyone with the Mini App link can open the document. Telegram signs the Mini App `initData` with the bot token, and `/editor/getConfig` accepts the request only if that signature is valid (`check_webapp_signature`). That is the only authentication.
- **Two different JWTs, one secret.**
  - `security_token` in the `getFile` and `sendFile` URLs is the bot's own JWT `{key, exp = TTL}`. It identifies the session.
  - The JWT in header `JWT_HEADER` is Document Server's request signature.
  - Both use `JWT_SECRET`, which must match DS's secret.
- **One DS document key per session.** `session["key"]` is created on the first opening and shared by everyone, which is what makes co-editing work. After the callback with status 2/3 the session is deleted, so the old link stops working by design. Reopening (reply to the file) creates a new session.
- **20 MB limit**: this is the Bot API `getFile` download limit. The bot cannot fetch larger files without a local Bot API server.
- `permissions.download/print/protect = false` in the editor config: the final file is delivered to the chat instead of being downloaded.
- `config.py` reads env at import and `load_dotenv()` runs after it. This is by design: configuration is expected from the process environment (Docker/compose).
- The Redis client is synchronous inside async handlers. This is by design (simple single-instance service).
- `toolbarNoTabs` was removed (`0608a10`) because it took up space. In Telegram's web app the compact style (`compactHeader`) matters more.

**Hacks and workarounds**
- `"​."` in file names (`edit_router.py`): a zero-width space before the extension stops Telegram from turning `name.docx` into a link.
- `check_message_exists` (`send_file.py`) checks whether the owner's link message still exists by calling `set_message_reaction(None)`, because the Bot API has no "get message" method. It branches on exact Telegram error strings, as does `check_user_exists_in_group`.
- `fixSize()` in `editor.html` corrects the iframe height in mobile WebViews.
- `DESKTOP_MODE`: the editor opens with `type: "desktop"` only on Telegram Desktop and macOS (`Telegram.WebApp.platform` is `tdesktop` or `macos`). Every other platform, including Telegram Web, gets `mobile`.
- For newly created files `customization.mobile.forceView/standardView = false`, so a new file opens directly for editing on phones.
- The anti-flood middleware ignores messages from the same album (`media_group_id`). Otherwise sending several files at once would trip the limit.
- In groups the anti-flood middleware also acts as a gate. It drops non-text/non-document messages and anything that does not mention `BOT_NAME`, unless the user is in the middle of a dialog. That is why it runs before i18n.

**Do not touch without a reason**
- The router order in `app/handlers/__init__.py`: back, cancel and lang must come before the scenario routers, and `start_router` with its catch-all reply must be last.
- The middleware order: anti-flood, then i18n.
- **Menu buttons are matched by translated text.** `_("Create")` renders the button and `F.text.lower() == __("create")` matches it, so both msgids must be translated consistently in every language. The Create menu also maps translated "Document/Spreadsheet/Presentation" back to extensions. `tests/test_formats_and_templates.py` checks both. Review any translation update against these tests.
- `BOT_NAME` must be the exact bot username. Group commands are matched as `/cmd@BOT_NAME` (`NotCommandFilter`) and the group gate looks for `BOT_NAME` in the text.
- The Redis layout:
  - session hash `<uuid>` with fields `document_type, file_id?, file_name, file_type, lang, members` (space-separated user ids), `message_id, owner, group?, link_message_id, key`;
  - `<user_id>:lang`;
  - `<user_id>:throttle`;
  - aiogram FSM keys (`DefaultKeyBuilder(with_destiny=True)`).

  Sessions survive deploys for up to `TTL` hours, so any change must stay compatible with existing keys.
- The `document-templates` submodule branch `main/new-2letter-code`. Its folder names are matched against Telegram's `language_code`.
- One bot token per running instance. Startup resets the webhook (`drop_pending_updates=True`, so updates sent during a restart are lost), commands and descriptions. Shutdown deletes the commands.

## 6. Known issues, tech debt, branches

**Branches.** Only `master` and `develop` exist on `origin`.
- `feature/env-ttl`, `feature/env-update`, `feature/lifetime`, `fix/no-tabs` and `ci/git-actions` are fully merged into `develop`. Delete them locally.
- `feature/telegram-build` (2 commits, Oct 2025) is an early version of `build.yaml` that hard-coded the RC version. It is superseded by the current workflow, deleted on `origin`, and can be dropped.
- `develop` and `master` have diverged a little:
  - `master` has GitHub issue templates (`60147ec`) that `develop` lacks. Merge `master` into `develop`.
  - `develop` has 2 post-release commits (dynamic RC version, submodule update).

**Tech debt**
- The tests are smoke-level only. They cover scenarios with fakes; there are no tests against a real Document Server or the Telegram API (see the manual checklist below).
- The synchronous `redis` client blocks the event loop on every call.
- `get_format_by_extension` re-reads the formats JSON from disk on every call.
- `MAX_FILE_SIZE_BYTES` is checked in handlers; the `TODO` in `config.py` is to move it into a middleware.
- `pyproject.toml` `version` is a placeholder; the real version is in `CHANGELOG.md`.
- `licenses.yml` installs Python 3.9 while the project requires ≥ 3.11.
- `datetime.utcnow()` is deprecated in `app/utils/jwt_utils.py`.
- Some aiohttp app keys are plain strings (`NotAppKeyWarning`).
- README format lists and `CHANGELOG.md` are maintained by hand and can drift from the formats submodule.

## 7. Plans and commitments

There are no open plans or commitments to customers or partners.

## Manual verification checklist

Automated smoke tests (`python -m pytest`) cover chat flows, editor config, the DS endpoints and translations with fakes. Before a release, also run this end to end against a real test bot and Document Server. Use two Telegram accounts (A, B), Telegram Desktop and a phone.

Private chat (account A):
- [ ] `/start` shows Create / Open / 🔄 Convert / ❌ Cancel. **⬅️ Back** and **❌ Cancel** work at each step.
- [ ] Create a Document, a Spreadsheet and a Presentation. Each link opens the editor. Telegram Desktop shows the desktop UI; the phone shows the mobile UI and opens the new file for editing.
- [ ] Edit, close the editor, and get the file back with the caption. The link message now says "expired" and the old link shows the localized "link has expired" page.
- [ ] Reply to the returned file with any text to get a new working link.
- [ ] Forward the link to account B. Both edit at the same time, and both receive the final file after closing.
- [ ] Send a `.docx` without a command: it opens for editing. Send a `.doc` or `.txt`: it opens view-only with the "available for 24 hours" text. Send a `.pdf`: it can be edited or filled.
- [ ] Send an unsupported file (`.zip`) or a photo to get "File not supported". Send a file over 20 MB to get "too large".
- [ ] Convert `.docx` to PDF and `.xlsx` to CSV and get the converted files. An invalid format gives "Invalid format".
- [ ] `/lang` → Русский: the menu, messages and editor UI are in Russian. Repeat for one more language.
- [ ] Send messages quickly to get the "Too many requests" warning.
- [ ] `/help` and `/cancel` work.

Group (A and B in a supergroup):
- [ ] Without admin rights, `/document@<bot>` creates a file with an auto-generated name, and the link works for B.
- [ ] Without admin rights, reply to a file with `/open@<bot>` to get a link. A plain file without a mention is ignored.
- [ ] With admin rights, send a file with a mention of the bot to get a link.
- [ ] After editing, the final file is posted in the group.
- [ ] `/help@<bot>` shows the group help.

After deploy:
- [ ] The bot's command menu and description are shown in the Telegram client language (check en and one other).
- [ ] The Docker Hub image tag matches the release (`stable-X.Y.Z` for production, `X.Y.Z-rc.N` for test).
