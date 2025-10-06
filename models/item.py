import pygame
from config import (
    KEY_IMAGE_PATH, ENDPOINT_IMAGE_PATH, POWERUP_IMAGE_PATH,
    COLOR_KEY, COLOR_ENDPOINT, COLOR_POWERUP,
    MAZE_CELL_SIZE, POWERUP_DURATION, ATTACK_RANGE_BOOST
)
from helper import load_image

class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if KEY_IMAGE_PATH:
            self.image = load_image(KEY_IMAGE_PATH, (20,30))
        else:
            self.image = pygame.Surface((20,20))
            self.image.fill(COLOR_KEY)
        self.rect = self.image.get_rect(center=(x, y))

class Endpoint(pygame.sprite.Sprite):
    def __init__(self, cell_pos):
        super().__init__()
        size = MAZE_CELL_SIZE - 20
        if ENDPOINT_IMAGE_PATH:
            self.image = load_image(ENDPOINT_IMAGE_PATH, (size-20, size-40))
        else:
            self.image = pygame.Surface((size, size))
            self.image.fill(COLOR_ENDPOINT)
        self.rect = self.image.get_rect()
        col, row = cell_pos
        self.rect.center = (col * MAZE_CELL_SIZE + MAZE_CELL_SIZE//2,
                            row * MAZE_CELL_SIZE + MAZE_CELL_SIZE//2)

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, size=20):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.rect = self.image.get_rect(center=pos)
    def apply(self, player):
        pass

class AttackRangePowerUp(Item):
    def __init__(self, pos):
        super().__init__(pos, size=20)
        if POWERUP_IMAGE_PATH:
            self.image = load_image(POWERUP_IMAGE_PATH, (30,30))
        else:
            self.image.fill(COLOR_POWERUP)
    def apply(self, player):
        # Set powerup timer
        player.powerup_timer = POWERUP_DURATION
        # If player already has a bow, enable rapid fire; otherwise, boost attack range
        if player.has_bow:
            player.rapid_fire = True
        else:
            player.attack_range_boost = ATTACK_RANGE_BOOST

# Bow powerup (appears only once)
class Bow(Item):
    def __init__(self, pos):
        super().__init__(pos, size=30)
        self.image = load_image("assets/bow.png", (30,30))
    def apply(self, player):
        player.has_bow = True

# TODO 7: 新增一個道具
'''
你可以參考 AttackRangePowerUp 和 Bow 來新增一個道具
道具的功能是什麼？你可以在 apply() 方法中實作
'''

class Crown(Item):
    def __init__(self, pos):
        super().__init__(pos, size=30)
        self.image = load_image("assets/crown.png", (30,30))
    
    def apply(self, player):
        # 拿到皇冠就直接獲勝
        player.has_key = True  # 確保玩家有鑰匙
        player.win = True

