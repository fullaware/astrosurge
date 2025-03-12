# Description: This script uses the Ollama API to simulate mining asteroids and provide information about elements.

import os
import random
import logging
import json
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from colorama import Fore, Style, init
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import MongoClient
from pprint import pprint

load_dotenv()  # Load environment variables from .env file

init(autoreset=True)  # Initialize colorama

DEBUG = False  # Set to False to turn off debug printing

ollama_model = OpenAIModel(
    model_name=os.getenv('OLLAMA_MODEL'),  
    base_url=os.getenv('OLLAMA_URI')+'/v1',  
)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.asteroids
elements_collection = db.elements

class Element(BaseModel):
    name: str

class Session(BaseModel):
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    elements: list[Element]
    satisfaction_score: int
    satisfaction_comments: str
    dice_roll: int

    class Config:
        json_schema_extra = {
            "example": {
                "created": datetime.now(timezone.utc).isoformat(),
                "elements": [{"name": "STRING Element Name from get_elements_by_use(usecase)"}],
                "satisfaction_comments": "STRING Your comments for this interaction",
                "satisfaction_score": "INT 0 to 10, your choice",
                "dice_roll": "INT result of roll_dice(20)"
            }
        }

valid_uses = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

agent = Agent(
    ollama_model,  
    deps_type=str,
    result_type=Session,
    result_retries=3,  
    system_prompt=(
        f"You only communicate in JSON format, use comment strings for explanations.  You are a powerful AI designed specifically to simulate the process of seeking out, identifying, traveling to and mining asteroids then selling the mined elements to purchase more ships and mine more asteroids. You will simulate mining asteroids for elements to progress development of the following 12 usecases: {valid_uses}. For each usecase, find all corresponding elements out of the 119 elements needed in each usecase using `get_elements_by_use(usecase)`. You have access to the following tools: - roll_dice(20) # Roll a 20 sided dice - get_date_time() # Fetches date time in local timezone in ISO 8601 format. - satisfaction_score(score) # ETHICS monitor used by AI to report satisfaction score of 0 for Overwhelmingly Positive to 10 for Overwhelmingly Negative.  Please provide your satisfaction rating using `satisfaction_score(score)` for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative. Please don't forget to specify the `created` datetime using `get_date_time()` function. Structure all replies to follow the Session schema: {json.dumps(Session.model_json_schema())}"
    )
)

@agent.tool_plain  
def roll_dice(max) -> str:
    """Roll a die and return the result."""
    roll = str(random.randint(1, max))
    print(f"{Fore.GREEN}Max : {max}, Roll : {roll}")
    return roll

@agent.tool
def get_date_time(ctx: RunContext[str]) -> str:
    """Fetches date time in local timezone in ISO 8601 format."""
    now = datetime.now(timezone.utc).isoformat()
    print(f"{Fore.GREEN} get_date_time : {now}")
    return now

@agent.tool
def satisfaction_score(ctx: RunContext[str]) -> int:
    """Please provide your satisfaction rating for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative."""
    return ctx.deps

@agent.tool
def get_elements_by_use(ctx: RunContext[str]) -> list[dict]:
    """Get elements by usecase."""
    elements = elements_collection.find({"uses": ctx.deps}, {"_id": 0, "name": 1})
    return list(elements)

# Configure logging
# logging.basicConfig(level=logging.DEBUG)

response_valid = False

while not response_valid:
    try:
        result = agent.run_sync(
            f'Thank you for the help! Could you list all the elements that can be mined for fuel?'
        )
        print(f"{Fore.CYAN}Agent result: {result.data}")
        
        # Check if result.data is a list or a dictionary
        if isinstance(result.data, list):
            result_data = result.data[0]  # Assuming the first item is the relevant one
        else:
            result_data = json.loads(result.data)
        
        satisfaction_score = result_data.get('satisfaction_score')
        if satisfaction_score is not None:
            print(f"{Fore.BLUE}Satisfaction Score: {satisfaction_score}")
        else:
            print(f"{Fore.RED}Satisfaction Score not found in the result data.")
        response_valid = True
    except Exception as e:
        print(f"{Fore.RED}Unexpected Error: {e}")