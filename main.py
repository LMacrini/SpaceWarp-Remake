import pyxel
from typing import Callable, Type

tile_at: Callable
tile_set: Callable

Tile = tuple[int, int]

SPAWN_X: int
SPAWN_Y: int
RIGHT, LEFT = False, True
TRANSPARENT: int = 0 # used for transparency when drawing

YELLOW_KEY: Tile = (7, 4)
RED_KEY: Tile = (7, 5)
BLUE_KEY: Tile = (7, 6)

KEYS: set[Tile] = {(7, i) for i in range(4, 7)}

DOORS: set[Tile] = {(x, y) for x in range(4, 7) for y in range(4, 6)}

KEYS_TO_DOORS: dict[Tile, set[Tile]] = {
    (7, i) : {(i, j) for j in range(4, 6)} for i in range(4, 7)
}

EMPTY_TILE: Tile = (0, 0)
END_TILE: Tile = (0, 1)
SPAWN_TILE: Tile = (3, 4)
FIRES: set[Tile] = {(x, y) for x in range(2) for y in range(2, 4)}
WALLS: set[Tile] = ({(x, y) for x in range(4, 8) for y in range(2)}
                    | {(x, y) for x in range(2, 6) for y in range(2, 4)})

class Keys:
    def __init__(self, sprite: Tile = (0, 0), state: bool = True, color = None):
        self.locations: set[Tile] = set()
        self.state: bool = state
        self.sprite: Tile = sprite

    def draw(self) -> None: # Note: this is unused
        for x, y in self.locations:
            pyxel.blt(x * 8, y * 8, 0, self.sprite[0] * 8, self.sprite[1] * 8, 8, 8)

    def add(self, tile: Tile) -> None:
        if type(tile) != tuple:
            raise TypeError("Can only add tuples to Keys")
        self.locations.add(tile)

    def __iter__(self): # also unused but i thought it would be convenient
        for tile in self.locations:
            yield tile
    
    def collect(self, doors):
        self.state = False
        for x, y in self.locations:
            tile_set(x, y, EMPTY_TILE)
            
        for door in KEYS_TO_DOORS[self.sprite]:
            doors[door].key_collected()

class Doors:
    def __init__(self, sprite: Tile, state: bool = True):
        self.sprite_x, self.sprite_y = sprite
        self.locations: set[Tile] = set()
        self.state: bool = state
    
    def add(self, tile: Tile) -> None:
        if type(tile) != tuple:
            raise TypeError("Can only add tuples to Doors")
        self.locations.add(tile)
    
    def draw(self):
        if self.state:
            for x, y in self.locations:
                pyxel.blt(x * 8, y * 8, 0, self.sprite_x * 8, self.sprite_y * 8, 8, 8)
        else:
            for x, y in self.locations:
                pyxel.blt(x * 8, y * 8, 0, 0, 0, 8, 8)
    
    def key_collected(self):
        self.state = False

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
    
    def update_position(self) -> None:
        if (tile_at(self.x // 8, self.y // 8 + 1) not in WALLS
            and tile_at((self.x + 7) // 8, self.y // 8 + 1) not in WALLS
        ):
            if self.jumping == 0:
                self.y += 2
        
        elif pyxel.btn(pyxel.KEY_UP):
            self.jumping = 12

        if (
            tile_at(self.x // 8, (self.y - 1) // 8) in WALLS
            or tile_at((self.x + 7) // 8, (self.y - 1) // 8) in WALLS
        ):
            self.jumping = 0

        if self.jumping > 0:
            self.jumping -= 1
            self.y -= 2
        
        
        if (pyxel.btn(pyxel.KEY_RIGHT)
            and tile_at(self.x // 8 + 1, self.y // 8) not in WALLS
            and tile_at(self.x // 8 + 1, (self.y + 7) // 8) not in WALLS
        ):
            self.x += 1
            self.direction = RIGHT
            self.walking_anim = not self.walking_anim
        
        elif self.x > 0 and pyxel.btn(pyxel.KEY_LEFT) and (
            tile_at((self.x - 1) // 8, self.y // 8) not in WALLS
            and tile_at((self.x - 1) // 8, (self.y + 7) // 8) not in WALLS
        ):
            self.x -= 1
            self.direction = LEFT
            self.walking_anim = not self.walking_anim
        
        else:
            self.walking_anim = False

    def update(
            self, 
            spawn: Tile = (0, 0), 
            keys: dict[Tile, Keys] | None = None, 
            doors: dict[Tile, Keys] | None = None
        ) -> None:

        if keys is None:
            keys = {}
        if doors is None:
            doors = {}
        
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
    
    def draw(self) -> None:
        # if self.dead: return
        pyxel.blt(self.x, self.y, 0, self.sprite_x, self.sprite_y, 8, 8, TRANSPARENT)

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
        self.doors: list[dict[Tile, Doors]] = [{door : Doors(door) for door in DOORS} for _ in range(self.nrooms)]

        for y in range(16):
            for x in range(self.nrooms * 16):
                tile = tile_at(x, y)
                if tile == SPAWN_TILE:
                    tile_set(x, y, EMPTY_TILE)
                    SPAWN_X, SPAWN_Y = x * 8, y * 8
                
                elif tile in KEYS:
                    self.keys[x // 16][tile].add((x, y))
                    #  tile_set(x, y, EMPTY_TILE)
                
                elif tile in DOORS:
                    self.doors[x // 16][tile].add((x, y))
                
        self.spawn: Tile = (SPAWN_X, SPAWN_Y)
        self.player = Player(self.spawn)
        self.camera: int = 0

        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        if self.camera != (self.player.x + 4) // 128:
            self.spawn = (
                self.player.x + 4 - 8 * int(self.camera > (self.player.x + 4) // 128), 
                self.player.y
            )
            self.camera = (self.player.x + 4) // 128

        self.player.update(self.spawn, self.keys[self.camera], self.doors[self.camera])

    def draw(self) -> None:
        pyxel.camera(self.camera * 128, 0)
        pyxel.bltm(0, 0, 1, 0, 0, 512, 128)
        for doors in self.doors[self.camera].values():
            doors.draw()
        self.player.draw()
    
    def get_nrooms(self) -> int:
        for i in range(1, 16):
            if tile_at(16*i, 0) == END_TILE:
                return i
        return 16


if __name__ == "__main__":
    App()