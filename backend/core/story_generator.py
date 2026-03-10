# Call an AI model to generate story
from sqlalchemy.orm import Session
from core.config import settings

#Take a string response coming from our LLM and pipe it into a Python class
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from dotenv import load_dotenv

load_dotenv()

class StoryGenerator:

    # We are writing a class so that we can organize some of the functions
    @classmethod #not specific to this instance
    def _get_llm(cls): #private method --> should only be called internally from the class
        return ChatOpenAI(model="gpt-4o-mini",
                          temperature=0.9,
                          max_tokens=1500)

    @classmethod
    def generate_story(cls, db:Session, session_id: str, theme:str ="fantasy") -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                STORY_PROMPT
            ),
            (
                "human",
                f"Create the story with this theme: {theme}"
            )
        ]).partial(format_instructions=story_parser.get_format_instructions())
        #Invoke the LLM -> generates the full prompt by actually passing in the format instructions
        raw_response = llm.invoke(prompt.invoke({}))

        response_text = raw_response
        if hasattr(raw_response, "content"):
            response_text = raw_response.content

        # Confirms that it is in the proper format
        story_structure = story_parser.parse(response_text)

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        #If this a dictionary, we want to validate that it is in the correct format of our root node
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        return story_db

    """Go thru all the data from LLM and convert it into the correct Python data type
    The model will return JSON and we're essentially enforcing that JSON returned by the model is correct
    """
    @classmethod
    def _process_story_node(cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False) -> StoryNode:
        print("Processing node:", getattr(node_data, "content", None), "is_root:", is_root)
        node = StoryNode(
            story_id=story_id,
            content=node_data.content if hasattr(node_data, "content") else node_data["content"],
            is_root=is_root,
            is_ending=node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"],
            is_winning_ending=node_data.isWinningEnding if hasattr(node_data, "isWinningEnding") else node_data["isWinningEnding"],
            options=[]
        )
        db.add(node)
        db.flush()
        print("Node ID after flush:", node.id)

        db.commit()  # Ensure it is saved in the database
        print("Node committed:", node.id)

        """Process child nodes recursively. We are creating a mapping structure where for every single node. 
        root node -> populating the options of the root node -> each option ioncludes the text of the next option and 
        the node_id"""
        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(db, story_id, next_node, False)

                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            node.options = options_list

        db.flush()
        return node