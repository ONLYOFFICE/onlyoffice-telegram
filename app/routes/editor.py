import json

from aiohttp.web import Request, Response
from jinja2 import Environment, FileSystemLoader

from config import DESKTOP_MODE, DOCSERVER_URL, PROJECT_ROOT

env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "static"))
template = env.get_template("editor.html")


async def editor(request: Request) -> Response:
    html_content = template.render(
        DOCSERVER_URL=DOCSERVER_URL, DESKTOP_MODE=json.dumps(DESKTOP_MODE)
    )
    return Response(text=html_content, content_type="text/html")
