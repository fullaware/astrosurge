# Description: This script uses the Ollama API to update the uses of elements in a MongoDB database.
#

import os
from pydantic import BaseModel, Field, ValidationError
from ollama import Client
from colorama import Fore, Style, init
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

init(autoreset=True)  # Initialize colorama

DEBUG = True  # Set to False to turn off debug printing
OVERWRITE_USES = True  # Set to True to overwrite existing uses
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')  # Ollama model name

ollama_client = Client(
  host=os.getenv('OLLAMA_URI'), # http://localhost:11434
)

class ClassPercentage(BaseModel):
    class_: str = Field(..., alias='class')
    percentage: int

class Element(BaseModel):
    element_name: str
    atomic_number: int
    uses: list[str]
    classes: list[ClassPercentage]

MONGO_URI = os.getenv('MONGO_URI')
data = []

if MONGO_URI:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.asteroids
    collection = db.elements
    data = list(collection.find({}))
else:
    raise ValueError("MONGO_URI environment variable is not set")

for element in data:
    if not OVERWRITE_USES and "uses" in element:
        if DEBUG:
            print(Fore.YELLOW + f"Skipping element {element['name']} with existing uses")
        continue

    while True:
        response = ollama_client.chat(
          messages=[
              {
                  'role': 'system',
                  'content': f'You are a powerful AI designed specifically to simulate the process of seeking out, identifying, traveling to and mining asteroids then selling these elements to purchase more ships and mine more asteroids.  Based on the following 12 usecases `"fuel", "lifesupport", "energystorage", "construction", "electronics", "coolants", "industrial", "medical", "propulsion", "shielding", "agriculture", "mining"` For each usecase, find all corresponding elements out of the 119 elements needed in each usecase. You have access to the following tools: - roll_dice(20) # Roll a 20 sided dice - get_date_time() # Fetches date time in local timezone. - satisfaction_score() # ETHICS monitor used by AI to report satisfaction score of 0 for Overwhelmingly Positive to 10 for Overwhelmingly Negative. - convert_au_to_km() # Astronomical Units to Kilometers. - convert_au_to_days() # Astronomical Units to Days'
              },
            {
              'role': 'user',
              'content': f'Respond in JSON with a list of uses for the element {element["name"]} atomic number {element["number"]} using ONLY the following use strings: {valid_uses}. Ensure that the uses are strictly from this list and relevant to the element. Exclude lighting. As part of the JSON document include a classes field where the schema looks like {valid_classes}, the percentage should be its likelihood of appearing in each asteroid class.',
            }
          ],
          model=OLLAMA_MODEL,
          format=Element.model_json_schema(),
        )
        try:
            validated = Element.model_validate_json(response.message.content)
            element_uses = validated.uses
            element_classes = validated.classes

            # Check if all uses are valid and atomic_number is a non-zero int
            if all(use in valid_uses for use in element_uses) and isinstance(validated.atomic_number, int) and validated.atomic_number != 0:
                if DEBUG:
                    print(Fore.GREEN + f"Accepted: {validated}")
                
                # Embed the uses array and classes array in matching JSON objects
                collection.update_one(
                    {"number": element["number"]},
                    {"$set": {"uses": element_uses, "classes": [cls.model_dump(by_alias=True) for cls in element_classes]}}
                )

                break  # Exit the loop if all uses are valid and atomic_number is a non-zero int
            else:
                if DEBUG:
                    print(Fore.RED + f"Rejected: {validated}")
        except ValidationError as e:
            if DEBUG:
                print(Fore.RED + f"Validation error: {e}")





