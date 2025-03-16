# Beryl

[Beryl](https://en.wikipedia.org/wiki/Beryl) is a mineral composed of beryllium aluminium silicate known as morganite, emerald and aquamarine. Easily mistaken for kryptonite.

Ethical AI use provided via feedback score and comment. [3 Laws of Kindness](https://www.fullaware.com/posts/aigoldenrule/)


## Workflow

- **Locate asteroids** and assess their value to choose which to build a mission plan to intercept.
  - [find_asteroids.py](find_asteroids.py) - find all asteroids within a given range, return ran
  - [find_value.py](find_falue.py) assess_asteroid_value()
  - [find_elements.py](find_elements.py) find_elements_use() to update_leaderboard
- **Choose Ship**
  - [manage_ship.py](manage_ship.py) get_ship
- **Travel to asteroid** 
  - [manage_ship.py](manage_ship.py) location, integrity
- **Mine asteroid**
  - [mine_asteroid.py](mine_asteroid.py) claim an asteroid, remove mass, return list of elements mined
  - [manage_ship.py](manage_ship.py) update cargo
- **Travel to Earth with resources**
  - [manage_ship.py](manage_ship.py) location, integrity
- **Manage mined resources**
  - [update_leaderboard.py](update_leaderboard.py) update leaderboard with find_elements_use