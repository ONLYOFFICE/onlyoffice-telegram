# CLAUDE.md

ONLYOFFICE bot for Telegram: a standalone Python service (aiogram 3 + aiohttp + Redis) that lets users create, open, co-edit and convert office files from Telegram chats. Editing happens in a Telegram Mini App that embeds ONLYOFFICE Docs (Document Server). Project background and history: see `HANDOVER.md`.

## Commands

```bash
git submodule update --init          # required: formats matrix + blank templates live in submodules
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .[dev]                # runtime deps + pre-commit + pytest
pre-commit install

python -m pytest                     # smoke tests, no network/Redis/Telegram needed
pre-commit run -a                    # ruff, ruff-format, black, basic hooks

python main.py                       # run the bot (needs env + Redis, see below)
docker compose --env-file .env up --build   # bot + redis (template: .env.docker.example)
```

Translations (after changing any `_()`/`__()` string):

```bash
pybabel extract -k __ -o locales/messages.pot app
pybabel update -i locales/messages.pot -d locales -D messages
pybabel compile -d locales -D messages   # .mo files are committed
```

## Running locally

- `config.py` reads the environment **at import time**; `load_dotenv()` in `main.py` runs after that import by design. Put variables into the process environment (shell export, IDE env file, `docker compose --env-file`). Variable list: `.env_example`.
- Telegram delivers updates to the webhook `WEB_APP_URL + WEBHOOK_PATH`, and Document Server downloads files from and posts callbacks to `WEB_APP_URL/editor/*`. So `WEB_APP_URL` must be a public HTTPS URL that both can reach (use a tunnel for local work).
- Use your own test bot token. On startup the bot resets the webhook, commands and description of that token; on shutdown it deletes the commands.

## Layout

```
main.py                 wiring: Bot, Dispatcher (Redis FSM), aiohttp app, webhook
config.py               all settings (env + constants: limits, flood, convert retries)
app/handlers/           chat scenarios (aiogram routers); ORDER in __init__.py matters
app/filters/            custom filters (document type, file name, group chat, ...)
app/middlewares/        antiflood (runs first), i18n (language from Redis or Telegram profile)
app/routes/             HTTP for the Mini App and Document Server:
                        /editor, /editor/getConfig, /editor/getFile, /editor/sendFile, /editor/getLocales
app/utils/              formats/templates lookup, JWT, i18n
static/editor.html      the Mini App page (Jinja2 template, loads DS api.js)
static/assets/          git submodules: document-formats, document-templates (do not edit here)
locales/                gettext catalogs, domain "messages"
tests/                  pytest smoke tests with fakes (tests/fakes.py)
```

## Conventions

- Branches: `feature/*`, `fix/*` from `develop`, PR into `develop`. `master` only receives release merges.
- Commit messages: `feat: ...`, `fix: ...`, `ci: ...`, `chore: ...`. Release commits are just the version (`1.1.0`).
- Every source file starts with the Apache-2.0 header "(c) Copyright Ascensio System SIA <year>". Copy it from an existing file.
- Max line length is 120. Formatting comes from ruff + black via pre-commit.
- Dependencies are pinned in both `requirements.txt` and `pyproject.toml`; change both. A new dependency must pass the `Licenses` workflow (exceptions go in `.check-licenses.yml`).
- `CHANGELOG.md` is the version source of truth: CI reads the first `## X.Y.Z` heading.

## Do not

- Do not reorder routers in `app/handlers/__init__.py` or middlewares in `app/middlewares/__init__.py` without reading the comments there. `start_router` contains a catch-all and must stay last.
- Do not change button labels or their translations casually. Handlers match buttons by translated text (`F.text.lower() == __("create")`), so `_("Create").lower()` must equal `_("create")` in every locale. `tests/test_formats_and_templates.py` checks this.
- Do not change the Redis key layout (session hash `<uuid>`, `<user_id>:lang`, `<user_id>:throttle`) without migration thought. Live sessions survive deploys for `TTL` hours.
- Do not switch the `document-templates` submodule off branch `main/new-2letter-code`: its folders match Telegram's 2-letter `language_code`.
- Do not commit `.env` or any token or secret.
