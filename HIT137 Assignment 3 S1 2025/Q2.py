"""
Name: Group 9
Date Started: 21/05
GitHub URL: https://github.com/MarukiIroha/HIT137-Assignment-3-Group-9
"""
import asyncio
import platform
import pygame
import os

# Initialize Pygame
pygame.init()

# Get the directory of the current script
script_dir = os.path.dirname(__file__)

# Set up the display
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Side-Scrolling Adventure")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
FALLBACK_BG_COLOR = (100, 100)  # Gray, used if background images fail

# Level-specific player Y positions
PLAYER_Y_POSITIONS = {
    1: 250,  # Level 1: higher on screen
    2: 480,  # Level 2: ground level
    3: 480   # Level 3: ground level
}

# Load images with paths relative to the script's directory
try:
    walkRight = [
        pygame.image.load(os.path.join(script_dir, 'images', f'R{i}.png')) for i in range(1, 10)
    ]
    walkLeft = [
        pygame.image.load(os.path.join(script_dir, 'images', f'L{i}.png')) for i in range(1, 10)
    ]
    char = pygame.image.load(os.path.join(script_dir, 'images', 'standing.png'))
    # Load multiple background images for each level
    backgrounds = [
        pygame.image.load(os.path.join(script_dir, 'images', f'bg{i}.png')) for i in range(1, 4)
    ]
    if len(backgrounds) != 3:
        raise pygame.error("Not all background images were loaded successfully")
except pygame.error as e:
    print(f"Error loading image: {e}")
    backgrounds = []  # Fallback to solid color if images fail
    pygame.quit()
    exit()

# Clock for frame rate
clock = pygame.time.Clock()
FPS = 60

# Audio for the game
bulletSound = pygame.mixer.Sound(os.path.join(script_dir, 'audio','maou_se_battle_gun01.mp3'))
hitSound = pygame.mixer.Sound(os.path.join(script_dir, 'audio','maou_se_battle18.mp3'))

music = pygame.mixer.music.load(os.path.join(script_dir, 'audio','maou_game_medley02.mp3'))
pygame.mixer.music.play(-1)

# Game variables
score = 0
level = 1
max_levels = 3
lives = 3
font = pygame.font.SysFont('comicsans', 30, True)
game_over = False

class Player:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vel = 5
        self.is_jump = False
        self.jump_count = 10
        self.left = False
        self.right = True
        self.walkCount = 0
        self.standing = True
        self.health = 100
        self.max_health = 100
        self.hitbox = (self.x + 17, self.y + 11, 29, 52)
        self.on_platform = False  # Track if player is on a platform

    def draw(self, win):
        if self.walkCount + 1 >= 27:
            self.walkCount = 0
        if not(self.standing):
            if self.left:
                win.blit(walkLeft[self.walkCount//3], (self.x, self.y))
                self.walkCount += 1
            elif self.right:
                win.blit(walkRight[self.walkCount//3], (self.x, self.y))
                self.walkCount +=1
        else:
            if self.right:
                win.blit(walkRight[0], (self.x, self.y))
            else:
                win.blit(walkLeft[0], (self.x, self.y))
        self.hitbox = (self.x + 17, self.y + 11, 29, 52)
        # Health bar
        pygame.draw.rect(win, RED, (self.x, self.y - 20, 50, 10))
        pygame.draw.rect(win, GREEN, (self.x, self.y - 20, 50 * (self.health / self.max_health), 10))

    def hit(self, damage):
        self.health -= damage
        if self.health <= 0:
            global lives
            lives -= 1
            self.health = self.max_health
            self.x = 200
            self.y = PLAYER_Y_POSITIONS.get(level, 240)  # Reset to level's default Y
            self.on_platform = False  # Reset platform status
            if lives <= 0:
                global game_over
                game_over = True

class Projectile:
    def __init__(self, x, y, radius, color, facing, damage=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.facing = facing
        self.vel = 8 * facing
        self.damage = damage

    def draw(self, win):
        pygame.draw.circle(win, self.color, (self.x, self.y), self.radius)

class Enemy:
    walkRight = [pygame.image.load(os.path.join(script_dir, 'images', f'R{i}E.png')) for i in range(1, 12)]
    walkLeft = [pygame.image.load(os.path.join(script_dir, 'images', f'L{i}E.png')) for i in range(1, 12)]

    def __init__(self, x, y, width, height, end, health=10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.end = end
        self.path = [self.x, self.end]
        self.walkCount = 0
        self.vel = 3
        self.health = health
        self.max_health = health
        self.visible = True
        self.hitbox = (self.x, self.y + 2, 31, 57)

    def draw(self, win):
        self.move()
        if self.visible:
            if self.walkCount + 1 >= 33:
                self.walkCount = 0
            if self.walkRight and self.walkLeft:
                frame_index = (self.walkCount // 3) % 11
                if self.vel > 0:
                    win.blit(self.walkRight[frame_index], (self.x, self.y))
                    self.walkCount += 1
                else:
                    win.blit(self.walkLeft[frame_index], (self.x, self.y))
                    self.walkCount += 1
            else:
                pygame.draw.rect(win, (255, 0, 0), (self.x, self.y, self.width, self.height))
                self.walkCount += 1
            pygame.draw.rect(win, (255, 0, 0), (self.hitbox[0], self.hitbox[1] - 20, 50, 10))
            pygame.draw.rect(win, (0, 128, 0), (self.hitbox[0], self.hitbox[1] - 20, 50 * (self.health / self.max_health), 10))
            self.hitbox = (self.x + 17, self.y + 2, 31, 57)

    def move(self):
        if self.vel > 0:
            if self.x + self.vel < self.path[1]:
                self.x += self.vel
            else:
                self.vel = self.vel * -1
                self.walkCount = 0
        else:
            if self.x - self.vel > self.path[0]:
                self.x += self.vel
            else:
                self.vel = self.vel * -1
                self.walkCount = 0

    def hit(self, damage):
        if self.health > 0:
            self.health -= damage
            if self.health <= 0:
                self.visible = False
                global score
                score += 10

class Boss(Enemy):
    walkRight = []
    walkLeft = []
    try:
        walkLeft = [pygame.image.load(os.path.join(script_dir, 'images', f'{x}.png')) for x in range(0, 8)]
        walkRight = [pygame.image.load(os.path.join(script_dir, 'images', f'{x}.png')) for x in range(8, 16)]
        if len(walkRight) != 8 or len(walkLeft) != 8:
            raise pygame.error("Not all boss images were loaded successfully")
    except pygame.error as e:
        print(f"Error loading boss images: {e}")
        print(f"Loaded {len(walkRight)} right images and {len(walkLeft)} left images")
        walkRight = None
        walkLeft = None

    def __init__(self, x, y, width, height, end):
        super().__init__(x, y, width, height, end, health=50)
        self.vel = 2
        self.damage = 20
        self.shoot_timer = 0
        self.shoot_interval = 60  # Shoot every ~1 second at 60 FPS
        self.walkCount = 0

    def draw(self, win):
        self.move()
        if self.visible:
            if self.walkCount + 1 >= 24:  # 8 frames * 3 ticks per frame = 24
                self.walkCount = 0
            if self.walkRight and self.walkLeft:
                frame_index = (self.walkCount // 3) % 8  # Cycle through 8 frames
                if self.vel > 0:
                    win.blit(self.walkRight[frame_index], (self.x, self.y))
                else:
                    win.blit(self.walkLeft[frame_index], (self.x, self.y))
            else:
                pygame.draw.rect(win, (128, 0, 128), (self.x, self.y, self.width, self.height))
            pygame.draw.rect(win, (255, 0, 0), (self.hitbox[0], self.hitbox[1] - 20, 50, 10))
            pygame.draw.rect(win, (0, 128, 0), (self.hitbox[0], self.hitbox[1] - 20, 50 * (self.health / self.max_health), 10))
            self.hitbox = (self.x + 17, self.y + 2, 31, 57)
            self.walkCount += 1
            # Shooting logic
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                self.shoot()
                self.shoot_timer = 0

    def shoot(self):
        global boss_bullets
        player_center_x = man.x + man.width // 2
        boss_center_x = self.x + self.width // 2
        facing = -1 if player_center_x < boss_center_x else 1
        if len(boss_bullets) < 3:  # Limit to 3 projectiles
            boss_bullets.append(Projectile(
                round(self.x + self.width // 2),
                round(self.y + self.height // 2),
                6, (128, 0, 128), facing, damage=15
            ))
            print(f"Boss shot projectile: x={self.x + self.width // 2}, facing={facing}")

    def hit(self, damage):
        if self.health > 0:
            self.health -= damage
            if self.health <= 0:
                self.visible = False
                global score
                score += 50

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hitbox = (self.x, self.y, self.width, self.height)

    def draw(self, win):
        pass
    
class Collectible:
    # Load animation frames for each collectible type
    sprites = {
        'coin': [],
        'heart': [],
        'potion': []
    }
    try:
        # Load coin images (11 frames: coin (1).png to coin (11).png)
        sprites['coin'] = [
            pygame.image.load(os.path.join(script_dir, 'images', f'coin ({i}).png')) for i in range(1, 12)
        ]
        # Load heart images (12 frames: heart (1).png to heart (12).png)
        sprites['heart'] = [
            pygame.image.load(os.path.join(script_dir, 'images', f'heart ({i}).png')) for i in range(1, 13)
        ]
        # Load potion images (8 frames: heal (1).png to heal (8).png)
        sprites['potion'] = [
            pygame.image.load(os.path.join(script_dir, 'images', f'heal ({i}).png')) for i in range(1, 9)
        ]
        # Verify all images loaded correctly
        if len(sprites['coin']) != 11 or len(sprites['heart']) != 12 or len(sprites['potion']) != 8:
            raise pygame.error("Not all collectible images were loaded successfully")
    except pygame.error as e:
        print(f"Error loading collectible images: {e}")
        print(f"Loaded {len(sprites['coin'])} coin images, {len(sprites['heart'])} heart images, {len(sprites['potion'])} potion images")
        sprites = {}  # Fallback to rectangles if any image fails

    def __init__(self, x, y, width, height, type_):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = type_  # 'coin', 'heart', 'potion'
        self.visible = True
        self.frame_count = 0
        self.frame_speed = 9  # Number of game ticks per frame (controls animation speed)
        self.frame_index = 0
        # Set max frames based on type
        self.max_frames = 11 if self.type == 'coin' else 12 if self.type == 'heart' else 8
        self.hitbox = (self.x, self.y, self.width, self.height)

    def draw(self, win):
        if self.visible:
            if self.sprites and self.type in self.sprites and self.sprites[self.type]:
                # Update animation frame
                self.frame_count += 1
                if self.frame_count >= self.frame_speed:
                    self.frame_index = (self.frame_index + 1) % self.max_frames
                    self.frame_count = 0
                # Draw current frame
                win.blit(self.sprites[self.type][self.frame_index], (self.x, self.y))
            else:
                # Fallback to colored rectangles
                color = (255, 255, 0) if self.type == 'coin' else (255, 0, 0) if self.type == 'heart' else (0, 128, 0)
                pygame.draw.rect(win, color, (self.x, self.y, self.width, self.height))

    def collect(self):
        global score, lives
        if self.type == 'potion':
            man.health = min(man.health + 20, man.max_health)
        elif self.type == 'heart':
            lives += 1
        elif self.type == 'coin':
            score += 50
        self.visible = False

class Goal:
    sprites = []
    try:
        sprites = [
            pygame.image.load(os.path.join(script_dir, 'images', f'goal ({i}).png')) for i in range(1, 6)
        ]
        if len(sprites) != 5:
            raise pygame.error("Not all goal images were loaded successfully")
    except pygame.error as e:
        print(f"Error loading goal images: {e}")
        print(f"Loaded {len(sprites)} goal images")
        sprites = []  # Fallback to rectangle if images fail

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.frame_count = 0
        self.frame_speed = 3  # Number of game ticks per frame (same as Collectible)
        self.frame_index = 0
        self.max_frames = 5  # 5 frames for goal animation
        self.hitbox = (self.x, self.y, self.width, self.height)

    def draw(self, win):
        if self.visible:
            if self.sprites:
                self.frame_count += 1
                if self.frame_count >= self.frame_speed:
                    self.frame_index = (self.frame_index + 1) % self.max_frames
                    self.frame_count = 0
                win.blit(self.sprites[self.frame_index], (self.x, self.y))
            else:
                pygame.draw.rect(win, BLUE, (self.x, self.y, self.width, self.height))

def setup_level(level):
    enemies = []
    collectibles = []
    boss = None
    goal = None
    platforms = []
    if level == 1:
        enemies = [
            Enemy(300, 250, 64, 64, 450),
            Enemy(500, 250, 64, 64, 600)
        ]
        collectibles = [
            Collectible(400, 120, 20, 20, 'heart'),
            Collectible(600, 120, 20, 20, 'coin')
        ]
        goal = Goal(700, 250, 50, 50)
        platforms = [
            Platform(372, 170, 65, 20),  # Smaller platform
            Platform(560, 170, 95, 20)   # Larger platform
        ]
    elif level == 2:
        enemies = [
            Enemy(200, 480, 64, 64, 400),
            Enemy(400, 480, 64, 64, 550),
            Enemy(600, 480, 64, 64, 700)
        ]
        collectibles = [
            Collectible(350, 400, 20, 20, 'potion'),
            Collectible(500, 400, 20, 20, 'coin')
        ]
        goal = Goal(750, 480, 50, 50)
    elif level == 3:
        boss = Boss(500, 480, 80, 80, 700)
        collectibles = [
            Collectible(300, 400, 20, 20, 'heart'),
            Collectible(450, 400, 20, 20, 'potion')
        ]
    return enemies, collectibles, boss, goal, platforms

def draw_game_over(win):
    win.fill(BLACK)
    font1 = pygame.font.SysFont('comicsans', 60, True)
    text = font1.render('Game Over', 1, WHITE)
    win.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
    text = font.render('Score: ' + str(score), 1, WHITE)
    win.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 10))
    text = font.render('Press R to Restart', 1, WHITE)
    win.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 50))
    pygame.display.update()

def redraw_game_window():
    # Draw background based on current level
    if backgrounds and len(backgrounds) >= level:
        win.blit(backgrounds[level - 1], (0, 0))
    else:
        win.fill(FALLBACK_BG_COLOR)
    text = font.render(f'Score: {score}  Lives: {lives}  Level: {level}', 1, (0, 0, 0))
    win.blit(text, (10, 10))
    # Draw platforms
    for platform in platforms:
        platform.draw(win)
    man.draw(win)
    for enemy in enemies:
        enemy.draw(win)
    if boss:
        boss.draw(win)
    for collectible in collectibles:
        collectible.draw(win)
    for bullet in bullets:
        bullet.draw(win)
    for boss_bullet in boss_bullets:
        boss_bullet.draw(win)
    if goal:
        goal.draw(win)
    pygame.display.update()

async def main():
    global man, enemies, collectibles, boss, bullets, boss_bullets, score, level, lives, game_over, goal, platforms
    man = Player(200, PLAYER_Y_POSITIONS[1], 64, 64)
    enemies, collectibles, boss, goal, platforms = setup_level(level)
    bullets = []
    boss_bullets = []
    shoot_loop = 0
    gravity = 0.5  # Gravity for falling
    fall_velocity = 0

    while True:
        if game_over:
            draw_game_over(win)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                score = 0
                level = 1
                lives = 3
                game_over = False
                man = Player(200, PLAYER_Y_POSITIONS[1], 64, 64)
                enemies, collectibles, boss, goal, platforms = setup_level(level)
                bullets = []
                boss_bullets = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            await asyncio.sleep(1.0 / FPS)
            continue

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        # Player shooting
        if shoot_loop > 0:
            shoot_loop += 1
        if shoot_loop > 3:
            shoot_loop = 0

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and man.x > man.vel:
            man.x -= man.vel
            man.left = True
            man.right = False
            man.standing = False
        elif keys[pygame.K_RIGHT] and man.x < WIDTH - man.width - man.vel:
            man.x += man.vel
            man.right = True
            man.left = False
            man.standing = False
        else:
            man.standing = True
            man.walkCount = 0

        # Platform collision detection
        man.on_platform = False
        for platform in platforms:
            if (man.hitbox[0] + man.hitbox[2] > platform.hitbox[0] and
                man.hitbox[0] < platform.hitbox[0] + platform.hitbox[2] and
                man.hitbox[1] + man.hitbox[3] > platform.hitbox[1] and
                man.hitbox[1] + man.hitbox[3] <= platform.hitbox[1] + platform.hitbox[3] + 2 and
                fall_velocity >= 0):  # Only land when falling or stationary
                man.y = platform.hitbox[1] - man.height - 11  # Stand on platform
                man.is_jump = False
                man.jump_count = 10
                man.on_platform = True
                fall_velocity = 0
                break

        # Apply gravity only if not on platform and not jumping
        if not man.is_jump and not man.on_platform:
            default_y = PLAYER_Y_POSITIONS.get(level, 240)
            if man.y < default_y:
                fall_velocity += gravity
                man.y += fall_velocity
                if man.y > default_y:
                    man.y = default_y
                    fall_velocity = 0
            else:
                man.y = default_y
                fall_velocity = 0
        elif man.on_platform:
            fall_velocity = 0  # Reset velocity when on platform to prevent bouncing

        # Jumping logic
        if not man.is_jump:
            if keys[pygame.K_UP]:
                man.is_jump = True
                man.right = False
                man.left = False
                man.walkCount = 0
                fall_velocity = 0
        else:
            if man.jump_count >= -10:
                neg = 1 if man.jump_count >= 0 else -1
                man.y -= (man.jump_count ** 2) * 0.5 * neg
                man.jump_count -= 1
            else:
                man.is_jump = False
                man.jump_count = 10
                fall_velocity = 0  # Ensure no residual velocity after jump

        if keys[pygame.K_SPACE] and shoot_loop == 0:
            facing = -1 if man.left else 1
            if len(bullets) < 5:
                bullets.append(Projectile(round(man.x + man.width // 2), round(man.y + man.height // 2), 6, (0, 0, 0), facing))
            shoot_loop = 1

        # Collision detection: Enemies and player
        for enemy in enemies[:]:
            if enemy.visible:
                if man.hitbox[1] < enemy.hitbox[1] + enemy.hitbox[3] and man.hitbox[1] + man.hitbox[3] > enemy.hitbox[1]:
                    if man.hitbox[0] + man.hitbox[2] > enemy.hitbox[0] and man.hitbox[0] < enemy.hitbox[0] + enemy.hitbox[2]:
                        man.hit(10)
                for bullet in bullets[:]:
                    if bullet.y - bullet.radius < enemy.hitbox[1] + enemy.hitbox[3] and bullet.y + bullet.radius > enemy.hitbox[1]:
                        if bullet.x + bullet.radius > enemy.hitbox[0] and bullet.x - bullet.radius < enemy.hitbox[0] + enemy.hitbox[2]:
                            enemy.hit(bullet.damage)
                            bullets.remove(bullet)

        # Collision detection: Boss and player
        if boss and boss.visible:
            if man.hitbox[1] < boss.hitbox[1] + boss.hitbox[3] and man.hitbox[1] + man.hitbox[3] > boss.hitbox[1]:
                if man.hitbox[0] + man.hitbox[2] > boss.hitbox[0] and man.hitbox[0] < boss.hitbox[0] + boss.hitbox[2]:
                    man.hit(boss.damage)
            for bullet in bullets[:]:
                if bullet.y - bullet.radius < boss.hitbox[1] + boss.hitbox[3] and bullet.y + bullet.radius > boss.hitbox[1]:
                    if bullet.x + bullet.radius > boss.hitbox[0] and bullet.x - bullet.radius < boss.hitbox[0] + boss.hitbox[2]:
                        boss.hit(bullet.damage)
                        bullets.remove(bullet)

        # Collision detection: Boss bullets and player
        for boss_bullet in boss_bullets[:]:
            if boss_bullet.y - boss_bullet.radius < man.hitbox[1] + man.hitbox[3] and boss_bullet.y + boss_bullet.radius > man.hitbox[1]:
                if boss_bullet.x + boss_bullet.radius > man.hitbox[0] and boss_bullet.x - boss_bullet.radius < man.hitbox[0] + man.hitbox[2]:
                    man.hit(boss_bullet.damage)
                    boss_bullets.remove(boss_bullet)

        # Move boss bullets
        for boss_bullet in boss_bullets[:]:
            if 0 < boss_bullet.x < WIDTH:
                boss_bullet.x += boss_bullet.vel
            else:
                boss_bullets.remove(boss_bullet)

        # Move player bullets
        for bullet in bullets[:]:
            if 0 < bullet.x < WIDTH:
                bullet.x += bullet.vel
            else:
                bullets.remove(bullet)

        # Collectible collision
        for collectible in collectibles[:]:
            if collectible.visible:
                if man.hitbox[1] < collectible.hitbox[1] + collectible.hitbox[3] and man.hitbox[1] + man.hitbox[3] > collectible.hitbox[1]:
                    if man.hitbox[0] + man.hitbox[2] > collectible.hitbox[0] and man.hitbox[0] < collectible.hitbox[0] + collectible.hitbox[2]:
                        collectible.collect()
                        collectibles.remove(collectible)

        # Goal collision (for levels 1 and 2)
        if goal and goal.visible:
            if man.hitbox[1] < goal.hitbox[1] + goal.hitbox[3] and man.hitbox[1] + man.hitbox[3] > goal.hitbox[1]:
                if man.hitbox[0] + man.hitbox[2] > goal.hitbox[0] and man.hitbox[0] < goal.hitbox[0] + goal.hitbox[2]:
                    if level < max_levels:
                        level += 1
                        enemies, collectibles, boss, goal, platforms = setup_level(level)
                        man.x = 200
                        man.y = PLAYER_Y_POSITIONS.get(level, 480)
                        man.on_platform = False
                        bullets = []
                        boss_bullets = []

        # Win condition for level 3 (defeat boss)
        if level == max_levels and boss and not boss.visible:
            game_over = True  # Win condition

        redraw_game_window()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())