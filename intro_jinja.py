from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Jinja2 Intro")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates directory
templates = Jinja2Templates(directory="templates")
async def hello(request: Request, name: str = “Student”):
    #“request” key is required by FastAPI/Starlette templates
    return templates.TemplateResponse(
        "hello.html",
        {“request”: request, “name”: name},
    )