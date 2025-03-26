# Beryl Project

## Overview

The **Beryl Project** is a simulation-based system designed to manage asteroid mining operations, resource extraction, and economic decision-making. The project allows users to plan missions, mine asteroids, manage ships, and trade valuable resources. It combines elements of resource management, logistics, and strategy to create a dynamic and engaging experience.

The name "Beryl" is inspired by the mineral beryllium aluminium silicate, which is often associated with precious gemstones like emeralds and aquamarines. Similarly, this project focuses on extracting valuable resources from asteroids.

## Purpose

The primary goal of the Beryl Project is to simulate the complexities of asteroid mining and resource management in a futuristic setting. It aims to:
- **Explore the potential of asteroid mining** as a sustainable source of rare and valuable materials.
- **Simulate economic and logistical challenges** involved in space exploration and resource extraction.
- **Provide a framework for decision-making** in resource allocation, mission planning, and ship management.
- **Encourage ethical AI use** by incorporating feedback mechanisms and promoting responsible decision-making.

## Key Features

1. **Asteroid Mining:**
   - Locate and assess the value of asteroids based on their composition and proximity to Earth.
   - Mine valuable elements like gold, platinum, and rare earth metals.
   - Manage mined resources and update asteroid data dynamically.

2. **Ship Management:**
   - Build and manage a fleet of mining ships with customizable attributes like capacity, mining power, and hull integrity.
   - Track ship locations, missions, and cargo.
   - Repair and maintain ships to ensure operational efficiency.

3. **Mission Planning:**
   - Plan and execute mining missions to maximize resource extraction and minimize costs.
   - Track mission progress, including projected and actual costs, durations, and outcomes.
   - Handle unexpected challenges like ship damage or resource depletion.

4. **Resource Trading and Distribution:**
   - Sell mined resources to generate revenue.
   - Distribute resources for industrial, medical, and other uses.
   - Update user accounts with the value of mined resources and manage economic growth.

5. **Ethical AI Integration:**
   - Promote responsible decision-making through feedback mechanisms.
   - Encourage sustainable practices in resource extraction and economic management.

## Workflow

1. **Locate Asteroids:**
   - Use `find_asteroids.py` to identify asteroids within a given range.
   - Assess their value using `find_value.py`.

2. **Choose a Ship:**
   - Select a ship from the fleet using `manage_ships.py`.

3. **Plan and Execute Missions:**
   - Travel to the asteroid, mine resources, and return to Earth.
   - Use `mine_asteroid.py` to extract resources and update asteroid data.

4. **Manage Resources:**
   - Update ship cargo with mined resources using `manage_ships.py`.
   - Sell or distribute resources using `manage_elements.py`.

5. **Ship Maintenance:**
   - Repair ships and empty cargo for future missions using `manage_ships.py`.

6. **Economic Growth:**
   - Update user accounts with the value of mined resources using `manage_users.py`.
   - Track economic progress and reinvest in ship upgrades or new missions.

## Data Model

The project revolves around four main objects:
1. **Asteroids:**
   - Store data about mined elements, mass, and value.
   - Update dynamically with each mining operation.

2. **Users:**
   - Manage user accounts, including bank balances and resource usage.

3. **Missions:**
   - Track mission details, including costs, durations, and outcomes.

4. **Ships:**
   - Manage ship attributes, cargo, and mission history.

## Ethical Considerations

The Beryl Project emphasizes ethical AI use by incorporating feedback mechanisms and promoting responsible decision-making. Users are encouraged to balance economic growth with sustainability and ethical practices.

## Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/beryl.git
   cd beryl
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the application:
   ```sh
   python main.py
   ```

## Future Goals

- **Expand asteroid data:** Incorporate real-world asteroid data for more realistic simulations.
- **Introduce challenges:** Add random events like ship malfunctions or asteroid collisions.
- **Enhance trading mechanics:** Include dynamic market prices for resources.
- **Multiplayer support:** Allow multiple users to collaborate or compete in mining operations.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to suggest improvements.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

# Beryl

[Beryl](https://en.wikipedia.org/wiki/Beryl) is a mineral composed of beryllium aluminium silicate known as morganite, emerald and aquamarine. Easily mistaken for kryptonite.

Ethical AI use provided via feedback score and comment. [3 Laws of Kindness](https://www.fullaware.com/posts/aigoldenrule/)


## Mission Planning
There are 4 objects that need to be manipulated for a successful mission.
- asteroids.mined_asteroids
  - asteroid = {
  "full_name": STR,
  "mined_elements_kg": $numberLong, # updated with every mine_asteroid()
  "abs_magnitude": DOUBLE,
  "class": STR, # C, S or M
  "elements": [  # mass_kg reduced with every mine_asteroid()
    {
      "name": "Hydrogen",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 1
    },
    {
      "name": "Helium",
      "mass_kg": {
        "$numberLong": "7192097937629254"
      },
      "number": 2
    },
    {
      "name": "Lithium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 3
    },
    {
      "name": "Beryllium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 4
    },
    {
      "name": "Boron",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 5
    },
    {
      "name": "Carbon",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 6
    },
    {
      "name": "Nitrogen",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 7
    },
    {
      "name": "Oxygen",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 8
    },
    {
      "name": "Fluorine",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 9
    },
    {
      "name": "Neon",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 10
    },
    {
      "name": "Sodium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 11
    },
    {
      "name": "Magnesium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 12
    },
    {
      "name": "Aluminium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 13
    },
    {
      "name": "Silicon",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 14
    },
    {
      "name": "Phosphorus",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 15
    },
    {
      "name": "Sulfur",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 16
    },
    {
      "name": "Chlorine",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 17
    },
    {
      "name": "Argon",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 18
    },
    {
      "name": "Potassium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 19
    },
    {
      "name": "Calcium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 20
    },
    {
      "name": "Scandium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 21
    },
    {
      "name": "Titanium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 22
    },
    {
      "name": "Vanadium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 23
    },
    {
      "name": "Chromium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 24
    },
    {
      "name": "Manganese",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 25
    },
    {
      "name": "Iron",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 26
    },
    {
      "name": "Cobalt",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 27
    },
    {
      "name": "Nickel",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 28
    },
    {
      "name": "Copper",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 29
    },
    {
      "name": "Zinc",
      "mass_kg": {
        "$numberLong": "61132832469848663"
      },
      "number": 30
    },
    {
      "name": "Gallium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 31
    },
    {
      "name": "Germanium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 32
    },
    {
      "name": "Arsenic",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 33
    },
    {
      "name": "Selenium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 34
    },
    {
      "name": "Bromine",
      "mass_kg": {
        "$numberLong": "28768391750517016"
      },
      "number": 35
    },
    {
      "name": "Krypton",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 36
    },
    {
      "name": "Rubidium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 37
    },
    {
      "name": "Strontium",
      "mass_kg": {
        "$numberLong": "64728881438663286"
      },
      "number": 38
    },
    {
      "name": "Yttrium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 39
    },
    {
      "name": "Zirconium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 40
    },
    {
      "name": "Niobium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 41
    },
    {
      "name": "Molybdenum",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 42
    },
    {
      "name": "Technetium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 43
    },
    {
      "name": "Ruthenium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 44
    },
    {
      "name": "Rhodium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 45
    },
    {
      "name": "Palladium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 46
    },
    {
      "name": "Silver",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 47
    },
    {
      "name": "Cadmium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 48
    },
    {
      "name": "Indium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 49
    },
    {
      "name": "Tin",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 50
    },
    {
      "name": "Antimony",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 51
    },
    {
      "name": "Tellurium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 52
    },
    {
      "name": "Iodine",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 53
    },
    {
      "name": "Xenon",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 54
    },
    {
      "name": "Cesium",
      "mass_kg": {
        "$numberLong": "7192097937629254"
      },
      "number": 55
    },
    {
      "name": "Barium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 56
    },
    {
      "name": "Lanthanum",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 57
    },
    {
      "name": "Cerium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 58
    },
    {
      "name": "Praseodymium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 59
    },
    {
      "name": "Neodymium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 60
    },
    {
      "name": "Promethium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 61
    },
    {
      "name": "Samarium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 62
    },
    {
      "name": "Europium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 63
    },
    {
      "name": "Gadolinium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 64
    },
    {
      "name": "Terbium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 65
    },
    {
      "name": "Dysprosium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 66
    },
    {
      "name": "Holmium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 67
    },
    {
      "name": "Erbium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 68
    },
    {
      "name": "Thulium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 69
    },
    {
      "name": "Ytterbium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 70
    },
    {
      "name": "Lutetium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 71
    },
    {
      "name": "Hafnium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 72
    },
    {
      "name": "Tantalum",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 73
    },
    {
      "name": "Tungsten",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 74
    },
    {
      "name": "Rhenium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 75
    },
    {
      "name": "Osmium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 76
    },
    {
      "name": "Iridium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 77
    },
    {
      "name": "Platinum",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 78
    },
    {
      "name": "Gold",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 79
    },
    {
      "name": "Mercury",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 80
    },
    {
      "name": "Thallium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 81
    },
    {
      "name": "Lead",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 82
    },
    {
      "name": "Bismuth",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 83
    },
    {
      "name": "Polonium",
      "mass_kg": {
        "$numberLong": "64728881438663286"
      },
      "number": 84
    },
    {
      "name": "Astatine",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 85
    },
    {
      "name": "Radon",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 86
    },
    {
      "name": "Francium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 87
    },
    {
      "name": "Radium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 88
    },
    {
      "name": "Actinium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 89
    },
    {
      "name": "Thorium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 90
    },
    {
      "name": "Protactinium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 91
    },
    {
      "name": "Uranium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 92
    },
    {
      "name": "Neptunium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 93
    },
    {
      "name": "Plutonium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 94
    },
    {
      "name": "Americium",
      "mass_kg": {
        "$numberLong": "50344685563404785"
      },
      "number": 95
    },
    {
      "name": "Curium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 96
    },
    {
      "name": "Berkelium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 97
    },
    {
      "name": "Californium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 98
    },
    {
      "name": "Einsteinium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 99
    },
    {
      "name": "Fermium",
      "mass_kg": {
        "$numberLong": "53940734532219408"
      },
      "number": 100
    },
    {
      "name": "Mendelevium",
      "mass_kg": {
        "$numberLong": "17980244844073136"
      },
      "number": 101
    },
    {
      "name": "Nobelium",
      "mass_kg": {
        "$numberLong": "35960489688146271"
      },
      "number": 102
    },
    {
      "name": "Lawrencium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 103
    },
    {
      "name": "Rutherfordium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 104
    },
    {
      "name": "Dubnium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 105
    },
    {
      "name": "Seaborgium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 106
    },
    {
      "name": "Bohrium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 107
    },
    {
      "name": "Hassium",
      "mass_kg": {
        "$numberLong": "14384195875258508"
      },
      "number": 108
    },
    {
      "name": "Meitnerium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 109
    },
    {
      "name": "Darmstadtium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 110
    },
    {
      "name": "Roentgenium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 111
    },
    {
      "name": "Copernicium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 112
    },
    {
      "name": "Nihonium",
      "mass_kg": {
        "$numberLong": "43152587625775530"
      },
      "number": 113
    },
    {
      "name": "Flerovium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 114
    },
    {
      "name": "Moscovium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 115
    },
    {
      "name": "Livermorium",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 116
    },
    {
      "name": "Tennessine",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 117
    },
    {
      "name": "Oganesson",
      "mass_kg": {
        "$numberLong": "21576293812887765"
      },
      "number": 118
    },
    {
      "name": "Ununennium",
      "mass_kg": {
        "$numberLong": "57536783501034031"
      },
      "number": 119
    }
  ],
  "mass": {
    "$numberLong": "9223372036854775178" # reduced after each mine_asteroid()
  },
  "moid_days": INT, # Days from Earth
  "neo": BOOL, # Near Earth Object
  "hazard" : BOOL, # Potential to impact Earth
  "orbit_id": STR,
  "pdes": STR,
  "spkid": INT,
  "synthetic": true, # If moid or diameter generated 
  "uid": user.uid,
  "value": {
    "$numberLong": "9223372036854775807"
  }
  }
- asteroids.users
  - user = {
  "uid": str(uuid.uuid4()),
  "name": STR,
  "bank": $numberLong,
  "password": "scrypt:32768:8:1$vBb77wctLPqDBAFA$dc271294c9d410be79384e62307d6366508e8a81c3a38e7587fe1ad02e6c47601f46a36ed2bd65f31f6ceb19a6fd17a5a6647102f1bf4db6f8cfa858687080c3",
"uses" : {
    "fuel" : $numberLong, # mass in kg incremented after each successful mission
    "lifesupport" : $numberLong,
    "energystorage" : $numberLong,
    "industrial" : $numberLong,
    "medical" : $numberLong,
    "construction" : $numberLong, 
    "electronics" : $numberLong, 
    "coolants" : $numberLong, 
    "propulsion" : $numberLong, 
    "shielding" : $numberLong, 
    "agriculture" : $numberLong,
    "mining" : $numberLong
  }
- asteroids.missions
  - mission = {
    "oid": str(uuid.uuid4()), # Multiple missions to the same asteroid are possible
    "uid": uid,
    "asteroid_name": asteroid["full_name"],
    "days_projected" : INT, # Days projected for mission to take travel to, mining, travel from
    "days_actual" : INT, # Days spent, incremented with each day cycle
    "value_projected" : $numberLong, # Estimated value of mission success = value of ship['cargo'] if full with mix of commodities
    "value_actual" : $numberLong, # updated at end of mission with value of list_elements_mined
    "cost_projected" : $numberLong, # Estimated costs based on ship cost + mission duration
    "cost_actual" : $numberLong, # updated at end of mission with costs, includes the value of the ship if status = 4 
    "status" : 0, # 0 = Planning, 1 = Executing, 2 = Success, 4 = Failure
    "mined_elements" : [{"name": STR, "mass_kg", $numberLong}] # Total mined elements from mission.
  }
- asteroids.ships
  - ship = {
        'oid': str(uuid.uuid4()),
        'name': str,
        'uid': uid, 
        'shield': INT 100 Default,
        'mining_power': 1000, # measured in kilojoules kJ
        'capacity': 10000,  # mass in kg
        'created': datetime.now(timezone.utc),
        'days_in_service': INT,
        'location': 0, # 0 = Earth, updated with each [manage_ships.py]().travel_ship(oid, uid, destination)
        'mission': INT, # Number of missions completed
        'hull': INT 100 Default, # Repaired on return to Earth
        'cargo': {} # {element_name: $numberLong} incremented with each mine_asteroid.update_mined_asteroid()
    }
- **Locate asteroids** and assess their value to choose which to build a mission plan to intercept.
  - [find_asteroids.py](find_asteroids.py) - find all asteroids within a given range, return list of asteroid names.
  - [find_value.py](find_falue.py) assess_asteroid_value()
- **Choose Ship**
  - [manage_ship.py](manage_ship.py) get_ship
- **Travel to asteroid** 
  - [manage_ship.py](manage_ship.py) location, integrity
- **Mine asteroid**
  - [mine_asteroid.py](mine_asteroid.py) mine_asteroid, and update_mined_asteroid
  - [manage_ship.py](manage_ship.py) update cargo
- **Travel to Earth with resources**
  - [manage_ship.py](manage_ship.py) location, integrity
- **Sell/Distribute mined resources**
  - [manage_elements.py](manage_elements.py) find_elements_use() to update_users()
  - [manage_elements.py](manage_elements.py) sell % of valuable elements, 
  - [manage_users.py](manage_users.py) update_users with find_elements_use, value of mined elements to add to `bank` and `mined_value`
- **Ship Maintenance**
  - [manage_ship.py](manage_ship.py) empty_cargo, repair `hull` and `shields` for $ determined difference between current status and 100.