from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from config import DOCSERVER_URL, PROJECT_ROOT, WEB_APP_URL

env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "static"))
template = env.get_template("editor.html")


async def editor(request: web.Request) -> web.Response:
    html_content = template.render(DOCSERVER_URL=DOCSERVER_URL, WEB_APP_URL=WEB_APP_URL)
    return web.Response(text=html_content, content_type="text/html")
