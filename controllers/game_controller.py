import sys, math, random, pygame, os
from config import (
    FPS, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_SPEED,
    MONSTER_SPAWN_INTERVAL, POWERUP_SPAWN_INTERVAL,
    BACKGROUND_IMAGE_PATH, HEART_IMAGE_PATH,
    NO_KEY_IMAGE_PATH, KEY_IMAGE_PATH, POWERUP_ICON_IMAGE_PATH,
    COLOR_BG, WORLD_WIDTH, WORLD_HEIGHT, KNOCKBACK_DURATION,
    KNOCKBACK_SPEED, INVULN_TIME, NUM_MONSTERS_INIT, KEY_DROP_PROBABILITY,
    MAZE_CELL_SIZE, MAZE_COLS, MAZE_ROWS, PLAYER_SIZE, MONSTER_SPEED,
    VICTORY_MUSIC_PATH
)
from models.player import Player
from models.monster import Monster
from models.item import Key, Endpoint, AttackRangePowerUp, Bow, Crown
from models.weapon import Fist, Arrow
from models.maze import generate_maze, generate_maze_walls
from views.renderer import Renderer
from helper import load_image

# TODO 2: 讓迷宮活起來！
'''
迷宮地圖是由「一格一格」的方塊組成，每個方塊的大小為 MAZE_CELL_SIZE
迷宮地圖的大小（方塊數量）為 MAZE_COLS x MAZE_ROWS
終點設定在 (MAZE_COLS-1, MAZE_ROWS//2) 的那塊方塊
勇者的初始位置在 (0,0) 的那塊方塊
請實作以下的 function, 回傳一個 position tuple (x, y)，代表一個物品隨機生成的位置（道具、怪物等）
小提醒：有些位置不應該作為隨機生成的位置
'''
# ----------------- your code starts here -----------------
def spwan_random_pos():
    # 隨機選擇一個方格位置，但避開起點和終點
    while True:
        i = random.randint(0, MAZE_COLS - 1)
        j = random.randint(0, MAZE_ROWS - 1)
        
        # 避開起點和終點
        if (i == 0 and j == 0) or (i == MAZE_COLS-1 and j == MAZE_ROWS//2):
            continue
            
        # 計算實際的位置，將物品放在方格中央
        x = i * MAZE_CELL_SIZE + MAZE_CELL_SIZE // 2
        y = j * MAZE_CELL_SIZE + MAZE_CELL_SIZE // 2
        return (x, y)
# ----------------- your code ends here -----------------

class GameController:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.maze = generate_maze(MAZE_COLS, MAZE_ROWS)
        self.wall_group = generate_maze_walls(self.maze)
        self.background_image = load_image(BACKGROUND_IMAGE_PATH, (WORLD_WIDTH, WORLD_HEIGHT)) if BACKGROUND_IMAGE_PATH else None
        self.heart_image = load_image(HEART_IMAGE_PATH, (25,25)) if HEART_IMAGE_PATH else None
        self.no_key_icon = load_image(NO_KEY_IMAGE_PATH, (25,35)) if NO_KEY_IMAGE_PATH else None
        
        # 初始化音樂
        pygame.mixer.init()
        self.victory_sound = None
        if os.path.exists(VICTORY_MUSIC_PATH):
            self.victory_sound = pygame.mixer.Sound(VICTORY_MUSIC_PATH)
        self.key_icon = load_image(KEY_IMAGE_PATH, (25,35)) if KEY_IMAGE_PATH else None
        self.powerup_icon = load_image(POWERUP_ICON_IMAGE_PATH, (35,35)) if POWERUP_ICON_IMAGE_PATH else None

        self.all_sprites = pygame.sprite.Group()
        self.monster_group = pygame.sprite.Group()
        self.key_group = pygame.sprite.Group()
        self.endpoint_group = pygame.sprite.Group()
        self.fist_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()

        self.player = Player((MAZE_CELL_SIZE//2, MAZE_CELL_SIZE//2))
        self.all_sprites.add(self.player)

        for _ in range(NUM_MONSTERS_INIT):
            pos = spwan_random_pos()
            if pos == None:
                continue
            else:
                monster = Monster(pos)
                self.all_sprites.add(monster)
                self.monster_group.add(monster)

        # 生成弓箭
        bow_spawned = False
        while not bow_spawned:
            pos = spwan_random_pos()
            if pos == None:
                break
            else:
                if not any(w.rect.collidepoint(pos) for w in self.wall_group):
                    bow = Bow(pos)
                    self.all_sprites.add(bow)
                    self.powerup_group.add(bow)
                    bow_spawned = True

        endpoint = Endpoint((MAZE_COLS-1, MAZE_ROWS//2))
        self.all_sprites.add(endpoint)
        self.endpoint_group.add(endpoint)

        self.monster_spawn_timer = 0
        self.powerup_spawn_timer = 0
        self.game_over = False
        self.win = False
        self.endpoint_message = None
        self.camera_x = 0

        self.renderer = Renderer(self.screen, {
            'background': self.background_image,
            'heart': self.heart_image,
            'no_key': self.no_key_icon,
            'key': self.key_icon,
            'powerup': self.powerup_icon,
            'bg_color': COLOR_BG
        })

        self.font = pygame.font.Font("fonts/GrechenFuemen-Regular.ttf", 28)
        self.title_font = pygame.font.Font("fonts/GrechenFuemen-Regular.ttf", 48)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.renderer.render(self.all_sprites, self.wall_group, self.player, self.endpoint_group,
                                 self.camera_x, self.game_over, self.win, self.endpoint_message,
                                 self.font, self.title_font)
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (self.game_over or self.win):
                    self.__init__(self.screen)
                if event.key == pygame.K_SPACE and not (self.game_over or self.win):
                    if self.player.has_bow and not self.player.is_attacking:
                        self.player.start_arrow_attack()
                    elif not self.player.has_bow:
                        fist = Fist(self.player, self.wall_group)
                        self.all_sprites.add(fist)
                        self.fist_group.add(fist)

    def update(self):
        if not (self.game_over or self.win):
            # 如果玩家贏了，直接結束遊戲並播放音樂
            if self.player.win:
                self.win = True
                # 播放勝利音樂
                if self.victory_sound and not pygame.mixer.get_busy():
                    self.victory_sound.play()
                return
            self.player.update(self.wall_group)
            for monster in self.monster_group:
                monster.update(self.wall_group)
            for projectile in self.projectile_group:
                projectile.update()
                for wall in self.wall_group:
                    if projectile.rect.colliderect(wall.rect):
                        projectile.kill()
                        break
                for m in pygame.sprite.spritecollide(projectile, self.monster_group, False):
                    # TODO 6: 擊退怪物！
                    '''
                    計算怪物被擊中後的擊退速度（包括方向），並且呼叫 m.hit(velocity) 來指定怪物被擊中時的擊退方向
                    projectile.direction 可以取得射出物件（擊中怪物的物件）的方向
                    或許可以在 config.py 找找其他相關的變數或是自己設定
                    '''
                    # ---------------- modify code below ----------------
                    # 弓箭擊中：使用弓箭的飛行方向作為擊退方向
                    # 乘上2倍速度使擊退效果更強
                    knockback_velocity = projectile.direction * (MONSTER_SPEED * 2)
                    m.hit(knockback_velocity)
                    # ---------------- modify code above ----------------
                    projectile.kill()
                    if m.is_dying and not hasattr(m, 'key_dropped'):
                        m.key_dropped = True
                        if random.random() < KEY_DROP_PROBABILITY and not self.player.has_key:
                            key = Key(m.rect.centerx, m.rect.centery)
                            self.all_sprites.add(key)
                            self.key_group.add(key)
                    break
            for fist in self.fist_group:
                fist.update()
                collided = pygame.sprite.spritecollide(fist, self.monster_group, False)
                for m in collided:
                    # TODO 6: 擊退怪物！
                    '''
                    計算怪物被擊中後的擊退速度（包括方向），並且呼叫 m.hit(velocity) 來指定怪物被擊中時的擊退方向
                    self.player.direction 可以取得勇者的方向
                    或許可以在 config.py 找找其他相關的變數或是自己設定
                    '''
                    # ---------------- modify code below ----------------
                    # 拳頭擊中：使用玩家的方向作為擊退方向
                    # 因為拳頭是近戰攻擊，所以使用玩家的方向更合理
                    knockback_velocity = self.player.direction * (MONSTER_SPEED * 1.5)
                    m.hit(knockback_velocity)
                    # ---------------- modify code above ----------------
                    fist.kill()
                    if m.is_dying and not hasattr(m, 'key_dropped'):
                        m.key_dropped = True
                        if random.random() < KEY_DROP_PROBABILITY and not self.player.has_key:
                            key = Key(m.rect.centerx, m.rect.centery)
                            self.all_sprites.add(key)
                            self.key_group.add(key)
                    break

            collided_monsters = pygame.sprite.spritecollide(self.player, self.monster_group, False)
            for m in collided_monsters:
                if m.is_dying:
                    continue
                if self.player.invuln_timer > 0:
                    continue
                if self.player.is_attacking:
                    self.player.is_attacking = False
                    self.player.attack_anim_index = 0
                    self.player.arrow_spawned = False
                self.player.lives -= 1
                self.player.invuln_timer = INVULN_TIME
                # TODO 6: 擊退怪物！
                '''
                計算怪物被擊中後的擊退速度（包括方向），並且呼叫 m.hit(velocity) 來指定怪物被擊中時的擊退方向
                計算勇者被撞到後的擊退速度（包括方向），並且呼叫 self.player.start_knockback(velocity, KNOCKBACK_DURATION) 來指定勇者被撞到時的擊退方向
                Hint: 記得 Vector2
                '''
                # ---------------- modify code below ----------------
                # 計算玩家和怪物之間的方向向量（從怪物指向玩家的向量）
                knockback_direction = pygame.math.Vector2(
                    self.player.rect.centerx - m.rect.centerx,
                    self.player.rect.centery - m.rect.centery
                ).normalize()
                # 玩家向後擊退，怪物也向後擊退
                self.player.start_knockback(-knockback_direction * PLAYER_SPEED, KNOCKBACK_DURATION)
                m.hit(-knockback_direction * MONSTER_SPEED)  # 怪物往相反方向退
                # ---------------- modify code above ----------------
                if m.is_dying and not hasattr(m, 'key_dropped'):
                    m.key_dropped = True
                    if random.random() < KEY_DROP_PROBABILITY and not self.player.has_key:
                        key = Key(m.rect.centerx, m.rect.centery)
                        self.all_sprites.add(key)
                        self.key_group.add(key)
                if self.player.lives <= 0:
                    self.game_over = True

            if pygame.sprite.spritecollideany(self.player, self.endpoint_group):
                if self.player.has_key:
                    self.win = True
                    self.endpoint_message = None
                else:
                    self.endpoint_message = "Go Find The Key!"
            else:
                self.endpoint_message = None

            key_hit = pygame.sprite.spritecollideany(self.player, self.key_group)
            if key_hit:
                self.player.has_key = True
                key_hit.kill()

            powerup_hit = pygame.sprite.spritecollideany(self.player, self.powerup_group)
            if powerup_hit:
                powerup_hit.apply(self.player)
                powerup_hit.kill()

            if self.player.has_bow and self.player.is_attacking:
                if self.player.rapid_fire:
                    if self.player.attack_anim_index >= 7 and not self.player.arrow_spawned:
                        for offset in [-5, 0, 5]:
                            direction = self.player.direction.rotate(offset)
                            arrow = Arrow(self.player.rect.center, direction, self.wall_group)
                            self.all_sprites.add(arrow)
                            self.projectile_group.add(arrow)
                        self.player.arrow_spawned = True
                else:
                    if self.player.attack_anim_index >= 7 and not self.player.arrow_spawned:
                        arrow = Arrow(self.player.rect.center, self.player.direction, self.wall_group)
                        self.all_sprites.add(arrow)
                        self.projectile_group.add(arrow)
                        self.player.arrow_spawned = True

            self.camera_x = self.player.rect.centerx - SCREEN_WIDTH // 2
            self.camera_x = max(0, min(self.camera_x, WORLD_WIDTH - SCREEN_WIDTH))

            self.monster_spawn_timer += 1
            if self.monster_spawn_timer >= MONSTER_SPAWN_INTERVAL:
                self.monster_spawn_timer = 0
                pos = spwan_random_pos()
                if pos == None:
                    pass
                else:
                    new_monster = Monster(pos)
                    self.all_sprites.add(new_monster)
                    self.monster_group.add(new_monster)

            self.powerup_spawn_timer += 1
            if self.powerup_spawn_timer >= POWERUP_SPAWN_INTERVAL:
                self.powerup_spawn_timer = 0
                pos = spwan_random_pos()
                if pos == None:
                    pass
                else:
                    # TODO 7: 把你的道具放進來！
                    '''
                    把下方的程式改成：每次生成道具時，隨機生成其中一種道具
                    Hint: 你可以使用 random.choice() 來隨機選擇一個 list 中的元素
                    '''
                    # ---------------- modify code below ----------------
                    # 創建一個道具清單，並隨機選擇一個

                    # 增加皇冠出現的機率，增加多個 Crown 在清單中
                    powerup_types = [AttackRangePowerUp, Crown, Bow, Bow,AttackRangePowerUp,AttackRangePowerUp,AttackRangePowerUp,AttackRangePowerUp,Bow,Bow]  
                    selected_powerup = random.choice(powerup_types)
                    powerup = selected_powerup(pos)
                    self.all_sprites.add(powerup)
                    self.powerup_group.add(powerup)
                    
