# Beryl

[Beryl](https://en.wikipedia.org/wiki/Beryl) is a mineral composed of beryllium aluminium silicate known as morganite, emerald and aquamarine. Easily mistaken for kryptonite.

Ethical AI use provided via feedback score and comment. [3 Laws of Kindness](https://www.fullaware.com/posts/aigoldenrule/)


## Workflow

- **Locate asteroids** and assess their value to choose which to build a mission plan to intercept.
  - [find_asteroids.py](find_asteroids.py) - find all asteroids within a given range, return ran
  - [find_value.py](find_falue.py) assess_asteroid_value()
  - [find_elements.py](find_elements.py) find_elements_use() to update_leaderboard
- **Travel to asteroid** 
- **Mine asteroid**
  - [mine_asteroid.py](mine_asteroid.py) claim an asteroid, remove mass, return list of elements mined
- **Manage mined resources**
  - [manage_ship.py](manage_ship.py) Create ship, update it's cargo, location, days_in_service
  - [update_leaderboard.py](update_leaderboard.py) update leaderboard with find_elements_use