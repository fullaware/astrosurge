import os
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import random
from pprint import pprint

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.asteroids
elements_collection = db.elements
valid_uses = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

class Element(BaseModel):
    name: str

class ResponseModel(BaseModel):
    current_weather: str = Field(description="get_weather(city)")
    current_temp: float = Field(description="get_weather(city)")
    created: datetime = Field(description="get_current_date")
    satisfaction_score: int = Field(description="satisfaction_score(score)")
    satisfaction_comments: str = Field(description="satisfaction_score(comment)")
    dice_roll: int  = Field(description="roll_dice()")

# Track which tools have been used in a run
class GetCurrentDateInput(BaseModel):
    """No inputs required for current date"""
    pass

class GetCurrentDateOutput(BaseModel):
    """Response for getting current date"""
    current_date: str

class GetWeatherInput(BaseModel):
    """Input for getting weather"""
    city: str

class GetWeatherOutput(BaseModel):
    """Response for getting weather"""
    weather: str
    temperature: float

# Configure OpenRouter API with OpenAI-compatible base URL
model = OpenAIModel(
    # model_name=os.getenv('OLLAMA_MODEL'), # granite is not good for this
    model_name='llama3.2:latest', # Smallest LLM, seems fast and works well with tools
    # model_name='llama3.1:8b', # Default LLM  
    base_url=os.getenv('OLLAMA_URI')+'/v1',  
)

# Initialize the agent
agent = Agent(
    model=model,
    # result_type=ResponseModel,
    system_prompt=f"""You are a helpful assistant. You have access to tools to help you answer questions. \
        - Assess which tool you should use to answer the question. \
        - If you think the question is too complex or not relevant, respond with satisfaction_score(0-10, comment) 0 = Positive, 10 = Negative. Please leave a comment for the interaction as well \
        - roll_dice to get a random number. \
        - get_elements_by_use(name) to get a list of elements by use. \
          - Valid uses, choose only ONE of the following: {valid_uses} \
        - Use get_current_date to get the current date. \
        - Use get_weather to get the weather for a specified city. \
        Finally, respond with a complete JSON document once you have a final answer.""",
)

@agent.tool  
def get_current_date(_: RunContext[GetCurrentDateInput]) -> GetCurrentDateOutput:
    print("Getting current date...")
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return GetCurrentDateOutput(current_date=current_date)

@agent.tool
def get_weather(_: RunContext[GetWeatherInput], city: str) -> GetWeatherOutput:
    print(f"Received city: {city}")
    if not city:
        raise ValueError("City is missing!")
    # Simulated weather data
    weather = "Sunny"
    temperature = 24.5
    return GetWeatherOutput(weather=weather, temperature=temperature)

@agent.tool
def satisfaction_score(_: RunContext, score: int, comment: str):
    print(f"Received satisfaction score: {score}")
    print(f"Received satisfaction comment: {comment}")

    return {"score": score, "comment" : comment}

@agent.tool
def roll_dice(_: RunContext) -> int:
    """Roll a die and return the result."""
    roll = random.randint(1, 20)
    print(f"Roll : {roll}")
    return roll



query = f"Please tell me todays date, weather in New York, roll dice and return number."
    
result = agent.run_sync(query)
pprint(result.new_messages_json)
    
