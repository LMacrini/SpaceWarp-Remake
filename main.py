#region imports
from __future__ import annotations
import pyxel
from typing import Callable, Any

tile_at: Callable
tile_set: Callable

Tile = tuple[int, int]

# region Constants

SPAWN_X: int
SPAWN_Y: int
RIGHT, LEFT = False, True
TRANSPARENT: int = 0 # used for transparency when drawing

YELLOW_KEY: Tile = (7, 4)
RED_KEY: Tile = (7, 5)
BLUE_KEY: Tile = (7, 6)

KEYS: set[Tile] = {(7, y) for y in range(4, 7)}

BUTTONS: set[Tile] = {(x, 6) for x in range(4, 7)}

TOP_DOORS: set[Tile] = {(x, 4) for x in range(4, 7)}
BOTTOM_DOORS: set[Tile] = {(x, 5) for x in range(4, 7)}
DOORS: set[Tile] = TOP_DOORS | BOTTOM_DOORS

EMPTY_TILE: Tile = (0, 0)
END_TILE: Tile = (0, 1)
SPAWN_TILE: Tile = (3, 4)
FIRES: set[Tile] = {(x, y) for x in range(2) for y in range(2, 4)}
WALLS: set[Tile] = ({(x, y) for x in range(4, 8) for y in range(2)}
                    | {(x, y) for x in range(2, 6) for y in range(2, 4)})

COLLIDERS = WALLS | DOORS

def is_tile(foo: Any):
    try:
        return (
            isinstance(foo, tuple) 
            and len(foo) == 2 and 
            isinstance(foo[0], int) and 
            isinstance(foo[1], int)
        )
    except:
        return False

class DoorError(Exception):
    """Misplaced door"""


# region Keys
class Keys:
    def __init__(self, sprite: Tile = (0, 0), state: bool = True, color = None):
        self.locations: set[Tile] = set()
        self.state: bool = state
        self.sprite: Tile = sprite

    def draw(self) -> None: # Note: this is unused
        for x, y in self.locations:
            pyxel.blt(x * 8, y * 8, 0, self.sprite[0] * 8, self.sprite[1] * 8, 8, 8)

    def add(self, tile: Tile) -> None:
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Keys")
        self.locations.add(tile)

    def __iter__(self): # also unused but i thought it would be convenient
        for tile in self.locations:
            yield tile
    
    def collect(self, doors: set[Doors]):
        self.state = False
        for x, y in self.locations:
            tile_set(x, y, EMPTY_TILE)

        for door in doors:
            door.open_door(self.sprite)

# region Buttons
class Buttons:
    def __init__(self, sprite: Tile, state: int = 0):
        self.sprite: Tile = sprite
        self.locations: set[Tile] = set()
        self.state = state
    
    def add(self, tile: Tile) -> None:
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Keys")
        self.locations.add(tile)
    
    def update(self):
        if self.state > 0:
            self.state -= 1

    def press(self, x: int, y: int, doors: set[Doors]) -> None:
        for button in self.locations:
            if button[0] * 8 - 4 <= x <= button[0] * 8 + 4 and button[1] * 8 == y:
                self.state = 150
            elif (
                button[0] * 8 - 5 <= x <= button[0] * 8 + 5 
                and button[1] * 8 - 1 <= y <= button[1] * 8 and self.state <= 2
            ):
                self.state = 2
            elif (
                button[0] * 8 - 6 <= x <= button[0] * 8 + 6
                and button[1] * 8 - 2 < y <= button[1] * 8 and self.state <= 1
            ):
                self.state = 1
        
        for door in doors:
            door.button_open(self.sprite, self.state)

    def draw(self):
        sprite_x, sprite_y = self.sprite
        sprite_x *= 8
        sprite_y *= 8

        for x, y in self.locations:
            pyxel.blt(x * 8, y * 8, 0, 0, 0, 8, 8)
            if self.state == 0:
                pyxel.blt(x * 8, y * 8, 0, sprite_x, sprite_y, 8, 8)
            elif self.state == 1:
                pyxel.blt(x * 8, y * 8 + 1, 0, sprite_x, sprite_y, 8, 7)
            elif self.state == 2:
                pyxel.blt(x * 8, y * 8 + 2, 0, sprite_x, sprite_y, 8, 6)

# region Doors
class Doors:
    def __init__(self, sprite: Tile, state: bool = True, timer: int = 0):
        self.sprite: Tile = sprite
        self.locations: set[Tile] = set()
        self.state: bool = state
        self.timer: int = 0
    
    def add(self, tile: Tile) -> None:
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Doors")
        self.locations.add(tile)
    
    def update(self) -> None:
        if self.timer > 0:
            self.timer -= 1
    
    def draw(self) -> None:
        if self.state and not self.timer:
            for x, y in self.locations:
                tile_set(x, y, self.sprite)
                tile_set(x, y + 1, (self.sprite[0], self.sprite[1] + 1))
        else:
            for x, y in self.locations:
                tile_set(x, y, EMPTY_TILE)
                tile_set(x, y + 1, EMPTY_TILE)
    
    def open_door(self, key: Tile) -> None:
        if key == (7, self.sprite[0]):
            self.state = False
    
    def button_open(self, button: Tile, frames: int) -> None:
        if button[0] == self.sprite[0] and frames > self.timer:
            self.timer = frames


# region Player
class Player:
    def __init__(self, spawn: Tile = (0, 0), *, direction: bool = RIGHT):
        self.x: int = spawn[0]
        self.y: int = spawn[1]
        self.jumping: int = 0
        self.dead: bool = False

        self.direction: bool = direction
        self.sprite_x: int = 8
        self.sprite_y: int = 0
        self.walking_anim: bool = False
    
    def corners(self) -> tuple[Tile, Tile, Tile, Tile]:
        return (
            tile_at(self.x // 8, self.y // 8),
            tile_at(self.x // 8, (self.y + 7) // 8),
            tile_at((self.x + 7) // 8, self.y // 8),
            tile_at((self.x + 7) // 8, (self.y + 7) // 8)
        )
    
    # region Player.update_position()
    def update_position(self) -> None:
        if (tile_at(self.x // 8, self.y // 8 + 1) not in COLLIDERS
            and tile_at((self.x + 7) // 8, self.y // 8 + 1) not in COLLIDERS
        ):
            if self.jumping == 0:
                self.y += 2
        
        elif pyxel.btn(pyxel.KEY_UP):
            self.jumping = 12

        if (
            tile_at(self.x // 8, (self.y - 1) // 8) in COLLIDERS
            or tile_at((self.x + 7) // 8, (self.y - 1) // 8) in COLLIDERS
        ):
            self.jumping = 0

        if self.jumping > 0:
            self.jumping -= 1
            self.y -= 2
        
        
        if (pyxel.btn(pyxel.KEY_RIGHT)
            and tile_at(self.x // 8 + 1, self.y // 8) not in COLLIDERS
            and tile_at(self.x // 8 + 1, (self.y + 7) // 8) not in COLLIDERS
        ):
            self.x += 1
            self.direction = RIGHT
            self.walking_anim = not self.walking_anim
        
        elif self.x > 0 and pyxel.btn(pyxel.KEY_LEFT) and (
            tile_at((self.x - 1) // 8, self.y // 8) not in COLLIDERS
            and tile_at((self.x - 1) // 8, (self.y + 7) // 8) not in COLLIDERS
        ):
            self.x -= 1
            self.direction = LEFT
            self.walking_anim = not self.walking_anim
        
        else:
            self.walking_anim = False

    # region Player.update()
    def update(
            self, 
            spawn: Tile = (0, 0), 
            keys: dict[Tile, Keys] | None = None,
            buttons: dict[Tile, Buttons] | None = None,
            doors: set[Doors] | None = None
        ) -> None:

        if keys is None:
            keys = {}
        if buttons is None:
            buttons = {}
        if doors is None:
            doors = set()
        
        self.update_position()

        corners = self.corners()
        # print(corners)
        
        # just look at the assets file man, this is stupid. should I just have changed it? probably
        self.sprite_x = 8*(self.direction^self.walking_anim) + 8 if self.jumping == 0 else 24
        self.sprite_y = 8*self.direction

        if any((tile in FIRES for tile in corners)):
            self.dead = True
            self.x, self.y = spawn
            self.jumping = 0
            self.direction = RIGHT
        
        for corner in corners:
            if corner in KEYS:
                keys[corner].collect(doors)
            elif corner in BUTTONS:
                buttons[corner].press(self.x, self.y, doors)
    
    def draw(self) -> None:
        # if self.dead: return
        pyxel.blt(self.x, self.y, 0, self.sprite_x, self.sprite_y, 8, 8, TRANSPARENT)

# region App
class App:
    def __init__(self):
        global tile_at, tile_set
        global SPAWN_X, SPAWN_Y

        self.difficulty: int = 1

        pyxel.init(128, 128, title="SpaceWarp")
        pyxel.load("assets.pyxres")

        tile_at = pyxel.tilemaps[self.difficulty].pget
        tile_set = pyxel.tilemaps[self.difficulty].pset

        self.nrooms: int = self.get_nrooms()

        self.keys: list[dict[Tile, Keys]] = [{key : Keys(key) for key in KEYS} for _ in range(self.nrooms)]
        self.buttons: list[dict[Tile, Buttons]] = [
            {button : Buttons(button) for button in BUTTONS} for _ in range(self.nrooms)
        ]
        self.doors: list[dict[Tile, Doors]] = [
            {door : Doors(door) for door in TOP_DOORS} for _ in range(self.nrooms)
        ]

        for y in range(16):
            for x in range(self.nrooms * 16):
                tile = tile_at(x, y)
                if tile == SPAWN_TILE:
                    tile_set(x, y, EMPTY_TILE)
                    SPAWN_X, SPAWN_Y = x * 8, y * 8
                
                elif tile in KEYS:
                    self.keys[x // 16][tile].add((x, y))
                    #  tile_set(x, y, EMPTY_TILE)
                
                elif tile in BUTTONS:
                    self.buttons[x // 16][tile].add((x, y))
                
                elif tile in TOP_DOORS:
                    if y == 16:
                        raise DoorError("Top door cannot be at the bottom of the screen")
                    elif tile_at(x, y + 1) in BOTTOM_DOORS:
                        self.doors[x // 16][tile].add((x, y))
                    else:
                        raise DoorError(f"Missing bottom door at {(x, y + 1)}")
                
                elif tile in BOTTOM_DOORS:
                    if y == 0:
                        raise DoorError("Bottom door cannot be at the top of the screen")
                    elif tile_at(x, y - 1) not in TOP_DOORS:
                        raise DoorError(f"Missing top door at {(x, y - 1)}")
    
        self.spawn: Tile = (SPAWN_X, SPAWN_Y)
        self.player = Player(self.spawn)
        self.camera: int = 0

        pyxel.run(self.update, self.draw)

    # region App.update()
    def update(self) -> None:
        if self.camera != (self.player.x + 4) // 128:
            self.spawn = (
                self.player.x + 4 - 8 * int(self.camera > (self.player.x + 4) // 128), 
                self.player.y
            )
            self.camera = (self.player.x + 4) // 128
        for doors in self.doors[self.camera].values():
            doors.update()

        for buttons in self.buttons[self.camera].values():
            buttons.update()

        self.player.update(
            self.spawn, 
            self.keys[self.camera], 
            self.buttons[self.camera], 
            set(self.doors[self.camera].values())
        )

    def draw(self) -> None:
        pyxel.camera(self.camera * 128, 0)
        pyxel.bltm(0, 0, 1, 0, 0, 512, 128)
        for doors in self.doors[self.camera].values():
            doors.draw()
        for buttons in self.buttons[self.camera].values():
            buttons.draw()
        self.player.draw()
    
    def get_nrooms(self) -> int:
        for i in range(1, 16):
            if tile_at(16*i, 0) == END_TILE:
                return i
        return 16


if __name__ == "__main__":
    App()