from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import  settings
from routers import job, story
from db.database import create_tables

create_tables()

# Define the app
app = FastAPI(
    title="Choose Your Own Adventure Game API",
    description="api to generate cool stories",
    version = "0.1.0",
    docs_url= "/docs",
    redoc_url= "/redoc",
)

# Add middleware to enable certain origin / certain URLS to interact with our backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True, # allows someone to send credentials to backend
    allow_methods=["*"], # enables them to use any API method
    allow_headers=["*"], # enables them to send additional information with the request
)
# Set up the API endpoints and connect them to server
app.include_router(story.router, prefix=settings.API_PREFIX)
app.include_router(job.router, prefix=settings.API_PREFIX)

# Only executes what's inside this if statement --> if you were to import something from this file, it will not work
if __name__ == "__main__":
    import uvicorn #It is a web server which allows us to serve the FastAPI application
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)