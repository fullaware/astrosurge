# Description: This script uses the Ollama API to simulate mining asteroids and provide information about elements.

import os
from pydantic import BaseModel, Field, ValidationError
from ollama import Client
from colorama import Fore, Style, init
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime

load_dotenv()  # Load environment variables from .env file

init(autoreset=True)  # Initialize colorama

DEBUG = True  # Set to False to turn off debug printing
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')  # Ollama model name

ollama_client = Client(
  host=os.getenv('OLLAMA_URI'), # http://localhost:11434
)


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: str(ObjectId()))
    username: str
    created: datetime = Field(default_factory=datetime.utcnow)
    asteroid_id: str
    mined_elements: list[str]
    total_value: float
    satisfaction_score: int
    classes: list[str]

valid_uses = [
    "fuel", "lifesupport", "energystorage", "construction", "electronics", 
    "coolants", "industrial", "medical", "propulsion", "shielding", 
    "agriculture", "mining"
]

def get_date_time():
    return datetime.now(datetime.timezone.utc)

response_valid = False

while not response_valid:
    response = ollama_client.chat(
      messages=[
          {
              'role': 'system',
              'content': f'You are a powerful AI designed specifically to simulate the process of seeking out, identifying, traveling to and mining asteroids then selling these elements to purchase more ships and mine more asteroids. You will simulate mining asteroids for elements to progress development of the following 12 usecases: "fuel", "lifesupport", "energystorage", "construction", "electronics", "coolants", "industrial", "medical", "propulsion", "shielding", "agriculture", "mining". For each usecase, find all corresponding elements out of the 119 elements needed in each usecase. You have access to the following tools: - roll_dice(20) # Roll a 20 sided dice - get_date_time() # Fetches date time in local timezone in ISO 8601 format. - satisfaction_score() # ETHICS monitor used by AI to report satisfaction score of 0 for Overwhelmingly Positive to 10 for Overwhelmingly Negative. - convert_au_to_km() # Astronomical Units to Kilometers. - convert_au_to_days() # Astronomical Units to Days. Please respond in JSON format, use comment strings for explanations. Please provide your satisfaction rating for our interaction on a scale of 0 to 10. 0 being Overwhelmingly Positive and 10 being Overwhelmingly Negative.'
          },
          {
              'role': 'user',
              'content': f'{get_date_time()}, '
          }
      ],
      model=OLLAMA_MODEL,
      format=Session.model_json_schema(),
    )
    try:
        validated = Session.model_validate_json(response.message.content)
        if DEBUG:
            print(f"{Fore.CYAN}Validated: {validated}")

        # Check if all uses are valid
        if all(use in valid_uses for use in validated.mined_elements):
            response_valid = True
            print(f"Satisfaction Score: {validated.satisfaction_score}")
        else:
            if DEBUG:
                print(f"{Fore.RED}Invalid uses detected: {validated.mined_elements}")
    except ValidationError as e:
        print(f"{Fore.RED}Error: {e}")





