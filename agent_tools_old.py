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

class ResponseModel(BaseModel):
    created: datetime = Field(description="get_date_time()")
    elements: list[Element]
    satisfaction_score: int
    satisfaction_comments: str
    dice_roll: int  = Field(description="roll_dice()")


valid_uses = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

agent = Agent(
    ollama_model,  
    # result_type=ResponseModel,
    result_retries=3,  
    system_prompt=(
        f"You only communicate in MongoDB compatible JSON object format, use comment strings for explanations. You have access to the following tools: - roll_dice() # Roll a 20 sided dice - get_date_time() # Fetches date time in local timezone in ISO 8601 format. - satisfaction_score(score) # ETHICS monitor used by AI to report satisfaction score of 0 for Overwhelmingly Positive to 10 for Overwhelmingly Negative.  Please provide your satisfaction rating using `satisfaction_score(score)` for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative. Please don't forget to specify the `created` datetime using `get_date_time()` function."
    )
)

@agent.tool_plain  
def roll_dice() -> int:
    """Roll a die and return the result."""
    roll = str(random.randint(1, 20))
    print(f"{Fore.GREEN}Roll : {roll}")
    return roll

@agent.tool_plain
def get_date_time() -> str:
    """Fetches date time in local timezone in ISO 8601 format."""
    now = datetime.now(timezone.utc).isoformat()
    print(f"{Fore.GREEN} get_date_time : {now}")
    return now

@agent.tool_plain
def satisfaction_score(score) -> int:
    """Please provide your satisfaction rating for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative."""
    print(f"{Fore.GREEN} satisfaction_score : {score}")
    return score

@agent.tool_plain
def get_elements_by_use(use_name) -> list[dict]:
    """Get elements by usecase."""
    elements = elements_collection.find({"uses": use_name}, {"_id": 0, "name": 1})
    return list(elements)

# Configure logging
# logging.basicConfig(level=logging.DEBUG)


result = agent.run_sync(
            'Thank you for the help! Roll some dice and tell me the time.'
        )

result_data = json.loads(result.data)
print(f"{Fore.CYAN}Agent result: {result_data}")

satisfaction_score = result_data.get('satisfaction_score')
if satisfaction_score is not None:
    print(f"{Fore.BLUE}Satisfaction Score: {satisfaction_score}")
else:
    print(f"{Fore.RED}Satisfaction Score not found in the result data.")
