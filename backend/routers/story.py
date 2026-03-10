import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from models.story import Story, StoryNode
from models.job import StoryJob
from schemas.story import (CompleteStoryResponse,
                                   CompleteStoryNodeResponse, CreateStoryRequest)
from schemas.job import StoryJobResponse
from core.story_generator import StoryGenerator

router = APIRouter(
    prefix="/stories",
    tags=["stories"]
)

# A session will identify in your browser when you're interacting with a website
# Look for your session_if and creates a new one if you don't have one
def get_session_id(session_id: Optional[str] = Cookie(None)):
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# Create an API Route to create the story
@router.post("/create", response_model=StoryJobResponse)
# Injects the dependencies or these values into these parameters.
def create_story(
        request: CreateStoryRequest,
        background_tasks: BackgroundTasks,
        response: Response,
        session_id: str= Depends(get_session_id),
        db: Session = Depends(get_db) # grabs the db and throw that in this database value
):
    # stores the session id (unsecured)
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    # Generate a new job_id as soon as the user creates a story
    # create a story -> creates a job => trigger a background story -> go to OpenAI to call an alarm to make the story
    job_id = str(uuid.uuid4())

    job = StoryJob(
        job_id = job_id,
        session_id = session_id,
        theme = request.theme,
        status = "pending"
    )
    # Add to database
    db.add(job)
    db.commit() # Saves to the database

    # Add background tasks, generate story
    background_tasks.add_task(
        generate_story_task,
        job_id=job_id,
        theme=request.theme,
        session_id=session_id
    )
    return job


# Background Task
def generate_story_task(job_id: str, theme:str, session_id: str):
    # Creates a new instance of our database so that we have two active databases at the same time
    # One session will be doing something and the other is waiting on something else to occur
    db = SessionLocal()

    try:
        # look for the job
        job = db.query(StoryJob).filter(StoryJob.job_id == job_id).first()

        if not job:
            return
        try:
            job.status = "processing"
            db.commit() # Save changes in the database

            story = StoryGenerator.generate_story(db, session_id, theme)

            job.story_id = story.id
            job.status = "completed"
            job.completed_at = datetime.now()
            db.commit()
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error = str(e)
            db.commit()
    finally:
        db.close()


# Create an API endpoint to retrieve the story
@router.get("/{story_id}/complete", response_model=CompleteStoryResponse)
def get_complete_story(story_id:int, db: Session = Depends(get_db)):
    # Checks to see if the story_id exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # todo: parse story
    complete_story = build_complete_story_tree(db, story)
    return complete_story

# Generate the story
def build_complete_story_tree(db: Session, story:Story) -> CompleteStoryResponse:
    print("Story ID:", story.id)
    nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).all()
    print("Nodes:", len(nodes))

    node_dict = {}
    for node in nodes:
        node_response = CompleteStoryNodeResponse(
            id=node.id,
            content = node.content,
            is_ending= node.is_ending,
            is_winning_ending= node.is_winning_ending,
            options=node.options or []
        )
        node_dict[node.id] = node_response

    root_node = next((node for node in nodes if node.is_root ), None)
    if not root_node:
        raise HTTPException(status_code=500, detail="Node not found")

    return CompleteStoryResponse(
        id = story.id,
        title = story.title,
        session_id = story.session_id,
        created_at = story.created_at,
        root_node = node_dict[root_node.id],
        all_nodes=node_dict
    )