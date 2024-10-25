from aiohttp.web_app import Application

from .editor import editor
from .get_config import get_config
from .get_file import get_file
from .send_file import send_file


def setup_routers(app: Application) -> None:
    app.router.add_static(prefix="/static", path="static")
    app.router.add_get("/editor", editor)
    app.router.add_get("/editor/getConfig", get_config)
    app.router.add_get("/editor/getFile", get_file)
    app.router.add_post("/editor/sendFile", send_file)
