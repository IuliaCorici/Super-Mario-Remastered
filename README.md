
## Run the code

Navigate to the project directory, and run:
```bash
python env/game.py
```
to play the game. You control the player using the `left` and `right` arrow keys, and jump with `space`.


## Code structure


└───env
│   │   game.py (all the code for the game)
│   │   env.py (a wrapper to interact with the Reinforcement Learning agent)
│   │   level.csv (the level that will be loaded in the game)
│   │
│   └───img (a folder with the game assets)
│

### Make your level
You can easily make your own level by looking at `level.csv`, which shows a 2D grid representing the level structure:

- `0` stands for nothing (air)
- `1` stands for the ground
- `2` stands for the goal position, reaching it means you win the level
- `3` stands for a walker enemy (an enemy that walks to the left once it sees the player)
- '4' stands for the cloud similar to the ground,-
- '5' stands for the lava,
- '6' stands for the meatballs (fall out of the sky and kill the player),
- '7' stands for the goombas (similar to the enemy),
- '9' stands for the player

The player always starts at position `(2,8)`, so that spot needs to be free.

### Extend the game
The game has a very simple structure:
```
GameObject: Every element of the game (such as the Player or the Ground) is a GameObject
│
└───Ground: A singleton class representing all the ground tiles
│
└───Goal: A class with the goal position
│
└───Moveable: All elements that can move around. 
              It includes basic movement (`update_speed`),
              and collision detection with the ground (`handle_obstacle_collision`)
              - A Moveable has an `update` method, that handle the object's logic at each timestep
│   │
│   └───Player: The player class. Has logic to handle collision with enemies (kills when on top)and goal-position
│   │
│   └───Enemy: All enemies inherit from this class.
               It handles player collision (dies or kills the player),
               and other enemies collision (simply bump into each other)
│   │   │
│   │   └───Walker: The only implemented enemy of the game.
                    Moves to the right when it sees the player
```

Every `GameObject` has an associated `GameSprite`, with the image representing the object.

The main class is `Game`. The method that does most of the work is `update`: it updates every element of the game and shifts their position so that they stay visible on the screen.
This is then called in the `step` method, which draws the current frame on the screen, and checks if the game terminates.

