import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
DEAD = False

jump = pygame.mixer.Sound("assets/sound/jump.wav")
bump = pygame.mixer.Sound("assets/sound/bump.wav")
music = pygame.mixer.music.load("assets/sound/title.mp3")
pygame.mixer.music.play(-1)

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health_count  = 3

    def game_over(self, run):
        if self.rect.centerx > 800:
            run = False

    def death(self):
        if self.health_count == 0:
            DEAD = True

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
    
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0
        self.health_count -= 1

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1
        bump.play()

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count +=1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        self.box_hit = False
        self.box_hit_count = 0

class Box1(Object):
    ANIMATION_DELAY = 3
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "box1")
        self.box1 = load_sprite_sheets("Items", "Boxes/Box1", width, height)
        self.image = self.box1["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Idle"
        self.box_hit = False
        self.box_hit_count = 0

    def idle_box(self):
        self.animation_name = "Idle"

    def hit_box(self):
        self.animation_name = "Hit (28x24)"
    
    def break_box(self):
        self.animation_name = "Break"

    def box_break(self):
        self.box_hit = True


    def loop(self):
        sprites = self.box1[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count +=1
        
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count +=1
        
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_backgroud(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i*width, j*height)
            tiles.append(pos)
    
    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 3)
    collide_right = collide(player, objects, PLAYER_VEL * 3)

    player.x_vel = 0
    if keys[pygame.K_a] and not collide_left and not DEAD:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right and not DEAD:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_backgroud("Blue.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    # box1 = Box1(block_size * 8, HEIGHT - block_size * 3, 28, 32)
    # box1.idle_box()
    fires = [  
                Fire((block_size * 5) + 32, HEIGHT - block_size - 64, 16, 32),
                Fire((block_size * 14) + 32, HEIGHT - block_size - 64, 16, 32)
                ]
    floor1 = [Block(i*block_size, HEIGHT - block_size, block_size) 
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    floor2 = [Block(i*block_size, HEIGHT - block_size, block_size) 
             for i in range((WIDTH * 3) // block_size, (WIDTH * 5) // block_size)]
    wall1 = [Block(block_size * -11, HEIGHT - block_size * i, block_size) 
             for i in range(-HEIGHT // block_size, (HEIGHT * 2) // block_size)]
    wall2 = [Block(block_size * 52, HEIGHT - block_size * i, block_size) 
             for i in range(-HEIGHT // block_size, (HEIGHT * 2) // block_size)]
    blocks = [
               Block(block_size * 3, HEIGHT - block_size * 3, block_size),
               Block(block_size * 6, HEIGHT - block_size * 5, block_size),
               Block(block_size * 7, HEIGHT - block_size * 5, block_size),
               Block(block_size * 8, HEIGHT - block_size * 5, block_size),
               Block(block_size * 10, HEIGHT - block_size * 2, block_size),
               Block(block_size * 10, HEIGHT - block_size * 3, block_size),
               Block(block_size * 15, HEIGHT - block_size * 2, block_size),
               Block(block_size * 15, HEIGHT - block_size * 3, block_size),
               Block(block_size * 15, HEIGHT - block_size * 4, block_size),
               Block(block_size * 11, HEIGHT - block_size * 7, block_size),
               Block(block_size * 21, HEIGHT - block_size * 3, block_size),
               Block(block_size * 23, HEIGHT - block_size * 5, block_size),
               Block(block_size * 25, HEIGHT - block_size * 3, block_size),
               Block(block_size * 27, HEIGHT - block_size * 5, block_size),
               ]

    objects = [*floor1,
               *floor2,
               *wall1,
               *wall2,
               *blocks,
               *fires]

    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        player.game_over(run)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                    jump.play()

        player.loop(FPS)
        for fire in fires:
            fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        if DEAD:
            font = pygame.font.SysFont(None, 40)
            died = "You Died!"
            text = font.render(died, False, 'red')
            text_rect = text.get_rect()
    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)