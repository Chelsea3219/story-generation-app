from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# We're mapping out exactly what we want a story to look like within this Python class structure to pass it into the LLM
class StoryOptionLLM(BaseModel):
    #Specifies all the fields that we want to be included in the data that comes back from the LLM
    # Then the LLM will know how to populate this
    text: str = Field(description="Text of the story option")
    nextNode: Dict[str, Any] = Field(description="Next node of the story and its options")

class StoryNodeLLM(BaseModel):
    content: str = Field(description="Main content of the story node")
    isEnding: bool = Field(description="Whether this node is an ending node")
    isWinningEnding: bool = Field(
        default=False,
        description="Whether this node is a winning ending"
    )
    options: List["StoryOptionLLM"] = Field(default_factory=list, description="The options for this node")

class StoryLLMResponse(BaseModel):
    title: str = Field(description="Title of the story")
    rootNode: StoryNodeLLM = Field(description="The root node of the story")
