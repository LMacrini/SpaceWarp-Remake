import pyxel

tile_at: callable

RIGHT, LEFT = False, True
TRANSPARENT: int = 0 # used for transparency when drawing
FIRES: list[tuple[int, int]] = [(x, y) for x in range(2) for y in range(2, 4)]
WALLS: list[tuple[int, int]] = [(x, y) for x in range(4, 8) for y in range(2)] + [(x, y) for x in range(2, 6) for y in range(2, 4)]

class App:
    def __init__(self):
        global tile_at

        self.difficulty: int | None = None
        self.player = Player()

        pyxel.init(128, 128, title="SpaceWarp")
        pyxel.load("assets.pyxres")
        tile_at = pyxel.tilemaps[1].pget
        # for y in range(16):
        #     string = ""
        #     for x in range(16):
        #         string += str(int(tile_at(x, y) in WALLS))
        #     print(string)
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        self.player.update()

    def draw(self) -> None:
        pyxel.camera(self.player.x - (self.player.x + 4) % 128 + 4, 0)
        pyxel.bltm(0, 0, 1, 0, 0, 512, 128)
        self.player.draw()

        

class Player:
    def __init__(self, x: int = 0, y: int = 0, *, direction: bool = RIGHT):
        self.x = x
        self.y = y
        self.direction = direction
    
    def update(self) -> None:
        if pyxel.btn(pyxel.KEY_UP) and (
            tile_at(self.x // 8, (self.y - 1) // 8) not in WALLS
            and tile_at((self.x + 7) // 8, (self.y - 1) // 8) not in WALLS
        ):
            self.y -= 2
        elif (tile_at(self.x // 8, self.y // 8 + 1) not in WALLS
            and tile_at((self.x + 7) // 8, self.y // 8 + 1) not in WALLS):
            self.y += 2
        
        if (pyxel.btn(pyxel.KEY_RIGHT)
            and tile_at(self.x // 8 + 1, self.y // 8) not in WALLS
            and tile_at(self.x // 8 + 1, (self.y + 7) // 8) not in WALLS):
            self.x += 1
        elif self.x > 0 and pyxel.btn(pyxel.KEY_LEFT) and (
            tile_at((self.x - 1) // 8, self.y // 8) not in WALLS
            and tile_at((self.x - 1) // 8, (self.y + 7) // 8) not in WALLS
        ):
            self.x -= 1
        # print(tile_at(self.x // 8 + 1, self.y), tile_at(self.x // 8 + 1, self.y + 7))
    
    def draw(self) -> None:
        pyxel.blt(self.x, self.y, 0, 8, 0, 8, 8, TRANSPARENT)



if __name__ == "__main__":
    App()