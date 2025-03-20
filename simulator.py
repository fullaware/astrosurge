"""
I want to build a simulation where you mine asteroids for money and the further development of space exploration. AIs are a powerful ally in our reach for the stars.  Dwarf Fortress + AI co-operation + Space Mining Operation Simulator.

AIs will pilot ships, mine asteroids, and manage resources.  
The user will be able to direct the AI on how to manage the resources, or not.  
The AI will provide feedback on how the user's strategy is working.  
The user will be able to see the market trends and adjust their strategy.

For example; Gold is trending in the market you may want to focus your mining efforts on a specific element.  

During this day you will have 24 hours to mine resources from the asteroid.  
`mine_asteroid.py` explains how we can simulate mining per hour.  That will be our finest measurement of time, 1 hour.  
The amount of material we mine is measured in kg.  
How much we can mine per hour is randomized, but I would like an LLM to assess each hour's output and "explain" why certain things may not have met expectations.  We want to provide graphs to the users to help them change their strategy for what elements to focus on.  
The user may choose to purge a bunch of "worthless" platinum when the market shifts and another element is on the rise.

Every user is the CEO of their own space mining company.  Companies will be ranked based on their total value AND their totals of each element mined.  Each element mined will have certain usecases that it is associated with which we have limited to 12.  "fuel", "lifesupport", "energystorage", "construction", "electronics", "coolants", "industrial", "medical", "propulsion", "shielding", "agriculture", "mining". The simulator can be expanded into those 12 usecases in later versions.

You have to build a mission plan for each asteroid you mine, each mission costs money so we are going to have to choose our asteroid wisely.  The longer we are in space, the longer we are exposed to things that could go wrong.  find_asteroids.py will allow the user to find real asteroids by name and distance from Earth in days. Once the user has selected the asteroid, we will use it's distance from Earth in `moid_days` to calculate the mission duration.  While travel to and from the asteroid is mostly static, the number of days you allocate to mining may need to be a variable.  If you only allow for 10 days of mining, but you aren't getting the yeild you want, you may want to extend the mission.  This will increase the risk of something going wrong, but it may also increase the reward.  The user will have to balance the risk and reward of each mission and so will the investors.

Once you have your mission plan, you have to fund it.  You will publish your mission plan to the AI who will evaluate it and then authorize your investment with an expected return on investment of 1.25x.  If you cannot make it back to Earth with the ship intact it's not "Game Over", it just means your next funding round is going up to 1.5x, and so on.  The longterm goal is to have enough money to fund your own missions without needing investors.

The user experience should be click, read what has happened, click, read what has happened.  They can click to modify which elements should be mined.  But without guidance, it will mine and collect all elements it can get because the leaderboard is based on total elements mined, not just company value.  The simulation should be automated as much as possible, it's to show how much we can rely on AI to drive business decisions.  The user should be able to see the AI's decision making process and be able to adjust it.  The AI should be able to explain why it made the decisions it did.  The user should be able to see the market trends and adjust their strategy.  The user should be able to see the leaderboard and see how they rank against other companies.

After being authenticated with an email and password, the User is greeted by LLM and asked for a Company Name.  The User is then asked to select an asteroid to mine.  The User is then asked to select the elements they wish to mine.  The User is then asked to select the duration of the mission.   The User is then asked to confirm the mission.  The User is then asked to start the mission.  The User is then shown the results of the mission.  The User is then shown the leaderboard.  The User is then asked if they would like to start another mission.  The User is then asked if they would like to see the market trends

Minimum Viable Product is Web based - Python, Ollama, OpenAI, MongoDB($VectorSearch), FastAPI, Pydantic-ai
.env file for MONGODB_URI OLLAMA_MODEL OLLAMA_URI
logging to stdout, colorful logging

"""