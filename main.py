import pyxel
from typing import Callable

tile_at: Callable
tile_set: Callable

type Tile = tuple[int, int]

SPAWN_X: int
SPAWN_Y: int
RIGHT, LEFT = False, True
TRANSPARENT: int = 0 # used for transparency when drawing

EMPTY_TILE: Tile = (0, 0)
FIRES: list[Tile] = [(x, y) for x in range(2) for y in range(2, 4)]
WALLS: list[Tile] = ([(x, y) for x in range(4, 8) for y in range(2)]
                    + [(x, y) for x in range(2, 6) for y in range(2, 4)])

class App:
    def __init__(self):
        global tile_at, tile_set
        global SPAWN_X, SPAWN_Y

        self.difficulty: int = 1

        pyxel.init(128, 128, title="SpaceWarp")
        pyxel.load("assets.pyxres")

        tile_at = pyxel.tilemaps[self.difficulty].pget
        tile_set = pyxel.tilemaps[self.difficulty].pset

        for y in range(16):
            for x in range(64):
                if tile_at(x, y) == (3, 4):
                    tile_set(x, y, (0, 0))
                    SPAWN_X, SPAWN_Y = x * 8, y * 8
                    break
            else:
                continue
            break

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

        self.player.update(self.spawn)

    def draw(self) -> None:
        pyxel.camera(self.camera * 128, 0)
        pyxel.bltm(0, 0, 1, 0, 0, 512, 128)
        self.player.draw()
        

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
    
    def update(self, spawn: Tile = (0, 0)) -> None:
        # if self.dead: return
        
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
        
        # just look at the assets file man, this is stupid. should I just have changed it? probably
        self.sprite_x = 8*(self.direction^self.walking_anim) + 8 if self.jumping == 0 else 24
        self.sprite_y = 8*self.direction

        if any((tile in FIRES for tile in self.corners())):
            self.dead = True
            self.x, self.y = spawn
            self.jumping = 0
            self.direction = RIGHT
    
    def draw(self) -> None:
        # if self.dead: return
        pyxel.blt(self.x, self.y, 0, self.sprite_x, self.sprite_y, 8, 8, TRANSPARENT)



if __name__ == "__main__":
    App()