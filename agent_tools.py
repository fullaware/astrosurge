import os
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
import random
from pprint import pprint
import json

load_dotenv()

class ResponseModel(BaseModel):
    weather: str 
    temperature: float
    current_date: str
    roll: int

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
    # model_name='llama3.2:latest', # Small LLM 
    # model_name='llama3.1:8b-instruct-q8_0', # Recommended LLM for tools
    model_name='qwen2.5:14b', # Recommended LLM for tools
    # model_name='llama3.1:8b', # Default LLM  
    base_url=os.getenv('OLLAMA_URI')+'/v1',  
)

# Initialize the agent
agent = Agent(
    model=model,
    result_type=ResponseModel,
    result_retries=5,
    system_prompt=f"""You are a helpful assistant. You have access to tools to help you answer questions. \
        - Assess which tool you should use to answer the question. \
        - get_current_date() to get the current date as YYYY-MM-DD. \
        - get_weather(city) to get the current weather in a city. \
        Finally, respond with a complete JSON document once you have a final answer.
        """,
)

@agent.tool  
def get_current_date(_: RunContext[GetCurrentDateInput]) -> GetCurrentDateOutput:
    
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"Getting current date : {current_date}")
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
def roll_dice(_: RunContext) -> int:
    roll = random.randint(1, 20)
    print(f"Rolled a 20-sided dice: {roll}")
    return roll

if __name__ == "__main__":

    query = "Please provide the current date and weather in New York and roll a 20 sided dice."
    max_retries = 5
    valid_response = None

    for attempt in range(max_retries):
        result = agent.run_sync(query)
        # If result.data is not None (i.e. valid ResponseModel), keep it
        if result.data:
            valid_response = result.data
            break

    if not valid_response:
        print("Failed to produce a valid ResponseModel after 5 attempts.")
    else:
        # Print final result as JSON
        pprint(json.loads(valid_response.model_dump_json()))

