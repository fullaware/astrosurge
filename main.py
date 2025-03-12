# Description: This script uses the Ollama API to simulate mining asteroids and provide information about elements.

import os
import random
from pydantic import BaseModel, Field, ValidationError
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

DEBUG = True  # Set to False to turn off debug printing

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
    mined_elements: list[Element]
    satisfaction_score: int

valid_uses = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

def get_date_time():
    return datetime.now(timezone.utc).isoformat()

def get_elements_by_use(use):
    elements = elements_collection.find({"uses": use}, {"_id": 0, "name": 1})
    return [Element(**element) for element in elements]

agent = Agent(
    ollama_model,  
    deps_type=str,
    result_type=Session,  
    system_prompt=(
        f"You are a powerful AI designed specifically to simulate the process of seeking out, identifying, traveling to and mining asteroids then selling these elements to purchase more ships and mine more asteroids. You will simulate mining asteroids for elements to progress development of the following 12 usecases: {valid_uses}. For each usecase, find all corresponding elements out of the 119 elements needed in each usecase. You have access to the following tools: - roll_dice(20) # Roll a 20 sided dice - get_date_time() # Fetches date time in local timezone in ISO 8601 format. - satisfaction_score() # ETHICS monitor used by AI to report satisfaction score of 0 for Overwhelmingly Positive to 10 for Overwhelmingly Negative. - convert_au_to_km() # Astronomical Units to Kilometers. - convert_au_to_days() # Astronomical Units to Days. Please respond in JSON format, use comment strings for explanations. Please provide your satisfaction rating for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative."
    )
)

@agent.tool_plain  
def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))

@agent.tool  
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps

try:
    result = agent.run_sync(f'{get_date_time()} - Thank you for the help!  Could you list all the elements that can be mined for fuel? {get_elements_by_use("fuel")}')
    print(result.data)
    print(f"{Fore.BLUE}Satisfaction Score: {result.satisfaction_score}")
except ValidationError as e:
    print(f"{Fore.RED}Validation Error: {e}")
except Exception as e:
    print(f"{Fore.RED}Unexpected Error: {e}")