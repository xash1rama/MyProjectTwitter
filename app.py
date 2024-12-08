from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path
from fastapi import FastAPI
from routers.rout_users import router as user_router
from routers.rout_tweets import router as tweet_router
from routers.rout_medias import router as media_router
from config.setup import lifespan



app = FastAPI(lifespan=lifespan)


app.include_router(user_router)
app.include_router(tweet_router)
app.include_router(media_router)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/images", StaticFiles(directory="static/images"), name="image")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    file_path = Path("static/index.html")
    return HTMLResponse(content=file_path.read_text(), status_code=200)
