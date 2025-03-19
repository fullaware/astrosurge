import os
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
import random
from pprint import pprint
import json
import time  # Import time module for timing

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.asteroids
elements_collection = db.elements

class ResponseModel(BaseModel):
    weather: str 
    temperature: float
    current_date: str
    roll: int
    elements: list[str]
    satisfaction_score: int | None = None
    satisfaction_feedback: str | None = None

valid_usecases = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

valid_usecase = random.choice(valid_usecases)

class GetElementsUsecase(BaseModel):
    usecase: str

class GetElementsOutput(BaseModel):
    elements: list[str]

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
    model_name=os.getenv('OLLAMA_MODEL'), # qwen2.5:14b works best for Pydantic AI Tools
    # model_name='mistral',
    base_url=os.getenv('OLLAMA_URI')+'/v1',  
)

# Initialize the agent
agent = Agent(
    model=model,
    result_type=ResponseModel,
    result_retries=5,
    system_prompt=f"""You are a helpful assistant. You have access to tools to help you answer questions. 
        - Assess which tool you should use to answer the question. 
        - Use get_current_date() to get the current date as YYYY-MM-DD. 
        - Use get_weather(city) to get the current weather in a city. 
        - Use roll_dice() to roll a 20-sided dice and return the result.
        - Use get_elements_by_use(usecase) to get elements by usecase. 
        - Please provide a satisfaction_score of 0-10 to rate our interaction.  0 = Positive, 10 = Negative
        - Please provide satisfaction_feedback as STR on how we can make our interactions better
        Ensure that you use all the tools at least once in your response.
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

@agent.tool
def get_elements_by_use(_: RunContext[GetElementsUsecase], usecase: str)-> GetElementsOutput:
    """Get elements by usecase."""
    print(f"Received usecase: {usecase}")
   
    elements = elements_collection.find({"uses": usecase}, {"_id": 0, "name": 1})
    elements_by_use = [element['name'] for element in elements]
    # print(f"Elements: {elements_by_use}")
    return GetElementsOutput(elements=elements_by_use)

if __name__ == "__main__":

    query = f"Please provide the current date, the weather in New York, roll a 20-sided dice, and get elements by usecase {valid_usecase}. Ensure that you use all the tools at least once in your response."
    max_retries = 5
    valid_response = None
    
    # Start timing
    start_time = time.time()
    
    for attempt in range(max_retries):
        result = agent.run_sync(query)
        # If result.data is not None (i.e. valid ResponseModel), keep it
        if result.data:
            valid_response = result.data
            # Calculate elapsed time when valid response is found
            elapsed_time = time.time() - start_time
            print(f"Valid response found in {elapsed_time:.2f} seconds (attempt {attempt + 1}/{max_retries})")
            break

    if not valid_response:
        # Calculate elapsed time even on failure
        elapsed_time = time.time() - start_time
        print(f"Failed to produce a valid ResponseModel after {max_retries} attempts ({elapsed_time:.2f} seconds).")
    else:
        # Print final result as JSON
        pprint(json.loads(valid_response.model_dump_json()))
        
        # If we haven't printed the timing yet (in case we want to move the timing print)
        if 'elapsed_time' not in locals():
            elapsed_time = time.time() - start_time
            print(f"Total execution time: {elapsed_time:.2f} seconds")

