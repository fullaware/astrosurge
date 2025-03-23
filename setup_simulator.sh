# Create necessary folders
mkdir -p templates static/css

# Create and populate manage_elements.py
cat << "EOF" > manage_elements.py
"""
manage_elements.py
Manages logic around which elements to mine.
"""
VALID_ELEMENTS = ["gold", "platinum", "iron", "silver"]

def select_elements(user_choice=None):
    if not user_choice:
        return VALID_ELEMENTS
    return [e for e in user_choice if e in VALID_ELEMENTS]
EOF

# Create and populate find_asteroids.py
cat << "EOF" > find_asteroids.py
"""
find_asteroids.py
Retrieves asteroids by name or distance (moid_days).
"""

def find_by_name(name: str):
    # Mock data for demonstration
    asteroids = {
        "Alpha": {"name": "Alpha", "moid_days": 2.0, "estimated_value": 5e7},
        "Beta": {"name": "Beta", "moid_days": 5.0, "estimated_value": 1.2e8},
        "Gamma": {"name": "Gamma", "moid_days": 10.0, "estimated_value": 3e8}
    }
    return asteroids.get(name, None)

def find_by_distance(max_days: float):
    # Mock data for demonstration
    candidates = [
        {"name": "Alpha", "moid_days": 2.0, "estimated_value": 5e7},
        {"name": "Beta", "moid_days": 5.0, "estimated_value": 1.2e8},
        {"name": "Gamma", "moid_days": 10.0, "estimated_value": 3e8}
    ]
    return [a for a in candidates if a["moid_days"] <= max_days]
EOF

# Create and populate mine_asteroid.py
cat << "EOF" > mine_asteroid.py
"""
mine_asteroid.py
Simulates mining yields over time.
"""
import random

def mine_hourly():
    return random.uniform(75.0, 200.0)
EOF

# Create and populate simulator.py
cat << "EOF" > simulator.py
"""
Space Mining Simulator Project Structure

1. manage_elements.py
   - Manages logic around which elements to mine.

2. find_asteroids.py
   - Retrieves asteroids by name or distance (moid_days).

3. mine_asteroid.py
   - Simulates mining yields over time.

4. webui.py
   - A minimal FastAPI interface with dark theme placeholders.

5. templates/base.html
   - Base HTML template for the web UI.

6. templates/index.html
   - Index page template for the web UI.

7. templates/missions.html
   - Missions page template for the web UI.

8. static/css/style.css
   - Custom CSS for styling the web UI.
"""

from find_asteroids import find_by_name, find_by_distance
from manage_elements import select_elements
from mine_asteroid import mine_hourly

def main():
    print("Starting the Space Mining Simulator MVP...")
    
    # Step 1: Select asteroid
    asteroid = find_by_name("Alpha")
    if not asteroid:
        print("Asteroid not found.")
        return
    
    # Step 2: Manage elements
    elements = select_elements()
    print(f"Selected elements: {elements}")
    
    # Step 3: Launch mission and simulate mining
    total_yield = 0
    for _ in range(24):  # Simulate 24 hours of mining
        total_yield += mine_hourly()
    
    # Step 4: Display results
    print(f"Total yield from mining: {total_yield:.2f}")

if __name__ == "__main__":
    main()
EOF

# Create and populate webui.py
cat << "EOF" > webui.py
"""
webui.py
A minimal FastAPI interface with dark theme placeholders.
"""
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pymongo import MongoClient
from dotenv import load_dotenv
from generate_logo import generate_logo

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["beryl_mvp"]
app = FastAPI(title="Space Mining UI")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    generate_logo(0)  # Generate the initial logo
    return templates.TemplateResponse("index.html", {"request": request, "title": "Space Mining MVP"})

@app.get("/missions", response_class=HTMLResponse)
def get_missions(request: Request):
    missions = list(db.missions.find())
    return templates.TemplateResponse("missions.html", {"request": request, "missions": missions})

@app.post("/launch", response_class=HTMLResponse)
def launch_mission(request: Request, asteroid_name: str = Form(...), days_to_mine: int = Form(...)):
    new_mission = {
        "asteroid_name": asteroid_name,
        "days_to_mine": days_to_mine,
        "status": "Launched"
    }
    db.missions.insert_one(new_mission)
    msg = f"Mission to {asteroid_name} launched for {days_to_mine} days!"
    return templates.TemplateResponse("index.html", {"request": request, "message": msg})

@app.get("/static/logo.png", response_class=FileResponse)
def get_logo():
    return FileResponse("static/logo.png")
EOF

# Create and populate generate_logo.py
cat << "EOF" > generate_logo.py
import matplotlib.pyplot as plt
import numpy as np

def generate_logo(day):
    t = np.linspace(0, 2 * np.pi, 100)
    x = np.sin(t + day)
    y = np.cos(t + day)

    plt.figure(figsize=(1.28, 1.28))  # 128x128 pixels
    plt.plot(x, y, 'b-', linewidth=2)
    plt.fill(x, y, 'b', alpha=0.3)
    plt.axis('equal')
    plt.axis('off')

    plt.savefig("static/logo.png", dpi=100)
    plt.close()

if __name__ == "__main__":
    generate_logo(0)
EOF

# Create and populate templates/base.html
cat << "EOF" > templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{{ title if title else "Space Mining" }}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"/>
  <style>
    body { background-color: #001f3f; color: #ffffff; }
  </style>
</head>
<body>
  <nav class="navbar navbar-dark bg-dark mb-3">
    <div class="container-fluid">
      <span class="navbar-brand">Space Mining Simulator</span>
    </div>
  </nav>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
EOF

# Create and populate templates/index.html
cat << "EOF" > templates/index.html
{% extends "base.html" %}
{% block content %}
  <div style="position: relative;">
    <h1>Asteroid Mining Operation Simulator</h1>
    <img src="/static/logo.png" alt="Logo" style="position: absolute; top: 0; right: 0; width: 128px; height: 128px;">
  </div>
  {% if message %}
  <div class="alert alert-success" role="alert">
    {{ message }}
  </div>
  {% endif %}
  <form method="post" action="/launch">
    <div class="mb-3">
      <label for="asteroidName" class="form-label">Asteroid Name</label>
      <input type="text" class="form-control" id="asteroidName" name="asteroid_name" required>
    </div>
    <div class="mb-3">
      <label for="daysToMine" class="form-label">Days to Mine</label>
      <input type="number" class="form-control" id="daysToMine" name="days_to_mine" required>
    </div>
    <button type="submit" class="btn btn-primary">Launch Mission</button>
  </form>
{% endblock %}
EOF

# Create and populate templates/missions.html
cat << "EOF" > templates/missions.html
{% extends "base.html" %}
{% block content %}
  <h2>Missions Database</h2>
  <table class="table table-dark table-striped">
    <thead>
      <tr>
        <th>Asteroid</th>
        <th>Days to Mine</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for m in missions %}
      <tr>
        <td>{{ m.asteroid_name }}</td>
        <td>{{ m.days_to_mine }}</td>
        <td>{{ m.status }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
{% endblock %}
EOF

# Create and populate static/css/style.css
cat << "EOF" > static/css/style.css
/* Custom CSS for styling the web UI */
body {
  background-color: #001f3f;
  color: #ffffff;
}
EOF

# Create and populate progress_checklist.md
cat << "EOF" > progress_checklist.md
# Space Mining Simulator Progress Checklist

## Detailed Plan and Checklist

### 1. Review Legacy Files
- [x] Review \`legacy/legacy_simulator.py\`
- [x] Identify reusable code and functionality

### 2. Set Up Project Structure
- [x] Create necessary folders and files
- [x] Populate files with initial content

### 3. Implement Core Features
- [ ] Asteroid Selection
- [ ] Element Management
- [ ] Mining Simulation
- [ ] Display Results

### 4. Integrate Modules
- [ ] Ensure all modules work together seamlessly

### 5. Test and Validate
- [ ] Run the simulator
- [ ] Start the FastAPI server
- [ ] Validate functionality

## Notes
- Keep track of any additional tasks or changes here.
EOF

echo "Setup complete. You can now run the simulator with 'python simulator.py' or start the FastAPI server with 'uvicorn webui:app --reload'."