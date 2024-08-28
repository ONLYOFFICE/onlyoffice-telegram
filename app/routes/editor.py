from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from config import DOCSERVER_URL, PROJECT_ROOT, WEB_APP_URL

# async def editor(request: Request) -> FileResponse:
#    file_path = PROJECT_ROOT / "static" / "editor.html"

#    if not file_path.exists():
#        return FileResponse(status=404)

#    return FileResponse(file_path)

env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "static"))
template = env.get_template("editor.html")


async def editor(request: web.Request) -> web.Response:
    html_content = template.render(DOCSERVER_URL=DOCSERVER_URL, WEB_APP_URL=WEB_APP_URL)
    return web.Response(text=html_content, content_type="text/html")
