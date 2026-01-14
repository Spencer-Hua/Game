import pygame
import sys

# 初始化 Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1200  # 原来是 800
SCREEN_HEIGHT = 900  # 原来是 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -14
PLAYER_SPEED = 7  # 稍微提高速度以匹配更大的地图

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
PURPLE = (180, 70, 240)
LIGHT_BLUE = (100, 200, 255)
DARK_RED = (150, 0, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("简易 I Wanna 游戏")
clock = pygame.time.Clock()

# 加载背景图片（请确保图片路径正确）
background_image = pygame.image.load(".\\images\\background.jpg").convert()

# 加载玩家图片
player_image = pygame.image.load(".\images\kid.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (60, 60))  # 调整图片大小为原来的1.5倍

# 新增加载第二个玩家图片
player_image_2 = pygame.image.load(".\images\kid1.png").convert_alpha()
player_image_2 = pygame.transform.scale(player_image_2, (60, 60))  # 调整图片大小为原来的1.5倍

# 加载金币图片（请确保图片路径正确）
coin_image = pygame.image.load(".\\images\\coin.gif").convert_alpha()
coin_image = pygame.transform.scale(coin_image, (30, 30))  # 调整大小为30x30像素

# 玩家类
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = player_image.get_width()-10
        self.height = player_image.get_height()
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
        self.double_jump_available = True  # 新增二段跳状态
        self.alive = True
        self.checkpoint = (x, y)
        self.death_count = 0
        self.direction = 1  # 1 for right, -1 for left
        self.animation_frame = 0  # 新增动画帧计数器
        self.animation_images = [player_image, player_image_2]  # 新增动画图片列表
        self.image = self.animation_images[0]  # 初始图片

    def jump(self):
        if not self.jumping:
            self.vel_y = JUMP_STRENGTH
            self.jumping = True
        elif self.double_jump_available:  # 如果已经在空中且二段跳可用
            self.vel_y = JUMP_STRENGTH * 0.7  # 第二次跳跃更高一些
            self.double_jump_available = False  # 用过之后设为不可用

    def move(self, platforms):
        # 水平移动
        self.x += self.vel_x

        # 水平碰撞检测
        for platform in platforms:
            if self.check_collision(platform):
                if self.vel_x > 0:  # 向右移动
                    self.x = platform.x - self.width
                elif self.vel_x < 0:  # 向左移动
                    self.x = platform.x + platform.width

        # 应用重力
        self.vel_y += GRAVITY
        self.y += self.vel_y

        # 垂直碰撞检测
        on_ground = False
        for platform in platforms:
            if self.check_collision(platform):
                if self.vel_y > 0:  # 下落
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.jumping = False
                    on_ground = True
                    self.double_jump_available = True  # 触地后重置二段跳状态
                elif self.vel_y < 0:  # 上升
                    self.y = platform.y + platform.height
                    self.vel_y = 0
                    self.jumping = True  # 碰到头顶的平台时保持跳跃状态
                    
        # 边界检查
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        if self.y > SCREEN_HEIGHT:
            self.die()

        self.update_animation()  # 在移动后更新动画

        return on_ground

    def check_collision(self, obj):
        return (self.x < obj.x + obj.width and
                self.x + self.width > obj.x and
                self.y < obj.y + obj.height and
                self.y + self.height > obj.y)

    def die(self):
        self.alive = False
        self.death_count += 1
        # 新增自动复活逻辑标志
        self.auto_respawn_timer = 30  # 30帧后自动复活

    def respawn(self):
        self.x, self.y = self.checkpoint
        self.vel_x = 0
        self.vel_y = 0
        self.alive = True

    def draw(self, screen):
        # 根据方向翻转图片
        current_image = self.image
        if self.direction == -1:  # 面向左边
            flipped_image = pygame.transform.flip(current_image, True, False)
            screen.blit(flipped_image, (self.x, self.y))
        else:  # 面向右边
            screen.blit(current_image, (self.x, self.y))

    def update_animation(self):
        # 更新动画帧
        if self.vel_x == 0:  # 玩家未水平移动
            self.image = player_image  # 设置为 kid.png
        else:
            self.animation_frame = (self.animation_frame + 1) % 10  # 每10帧循环一次
            if self.vel_x != 0:  # 只有在移动时才切换动画
                self.image = self.animation_images[self.animation_frame // 5]  # 每5帧切换一次图片

# 平台类
class Platform:
    def __init__(self, x, y, width, height, color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

# 尖刺基类（原Spike类）
class StaticSpike:
    def __init__(self, x, y, width=45, height=30, direction="up"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.direction = direction
        print(f"初始化尖刺: ({self.x}, {self.y})")  # 简化调试信息

    def check_collision(self, player):
        # 简单的矩形碰撞检测
        return (player.x < self.x + self.width and
                player.x + player.width > self.x and
                player.y < self.y + self.height and
                player.y + player.height > self.y)

    def draw(self, screen):
        # 根据方向绘制尖刺
        points = []
        if self.direction == "up":
            points = [(self.x, self.y + self.height),
                      (self.x + self.width//2, self.y),
                      (self.x + self.width, self.y + self.height)]
        elif self.direction == "down":
            points = [(self.x, self.y),
                      (self.x + self.width//2, self.y + self.height),
                      (self.x + self.width, self.y)]
        elif self.direction == "left":
            points = [(self.x + self.width, self.y),
                      (self.x, self.y + self.height//2),
                      (self.x + self.width, self.y + self.height)]
        else:  # right
            points = [(self.x, self.y),
                      (self.x + self.width, self.y + self.height//2),
                      (self.x, self.y + self.height)]
        
        pygame.draw.polygon(screen, RED, points)
        pygame.draw.polygon(screen, DARK_RED, points, 2)

    def reset(self):
        # 静态尖刺不需要重置逻辑
        pass

# 动态尖刺类（新MovingSpike类），继承自StaticSpike
class MovingSpike(StaticSpike):
    def __init__(self, x, y, width=45, height=30, direction="up"):
        super().__init__(x, y, width, height, direction)
        self.moving_up = False  # 新增标志表示尖刺是否正在向上移动
        self.speed_y = 0  # 尖刺的垂直速度
        self.original_y = y  # 记录初始位置

    def update(self):
        if self.moving_up:
            self.y += self.speed_y
            self.speed_y -= 1  # 模拟加速度
            if self.y + self.height < 0:  # 如果尖刺完全移出屏幕上方，则隐藏它
                self.moving_up = False

    def trigger_spike(self, player):
        # 判断玩家是否在尖刺正上方
        if (player.x + player.width > self.x and 
            player.x < self.x + self.width and
            player.y + player.height <= self.y + 100):  # 玩家底部接触到尖刺顶部
            self.moving_up = True
            self.speed_y = -15  # 设置一个较大的初始速度

    def reset(self):
        # 重置动态尖刺状态
        self.y = self.original_y
        self.moving_up = False
        self.speed_y = 0

# 存档点类
class Checkpoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.activated = False

    def activate(self, player):
        if not self.activated:
            player.checkpoint = (self.x, self.y)
            self.activated = True

    def check_collision(self, player):
        return (player.x < self.x + self.width and
                player.x + player.width > self.x and
                player.y < self.y + self.height and
                player.y + player.height > self.y)

    def draw(self, screen):
        color = YELLOW if self.activated else PURPLE
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

        # 绘制存档点标志
        if self.activated:
            pygame.draw.circle(screen, GREEN, (self.x + self.width//2, self.y + self.height//2), 5)
        else:
            pygame.draw.circle(screen, WHITE, (self.x + self.width//2, self.y + self.height//2), 5)

# 在 Spike 类之后添加金币类
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = coin_image.get_width()
        self.height = coin_image.get_height()
        self.collected = False

    def check_collision(self, player):
        if not self.collected:
            return (player.x < self.x + self.width and
                    player.x + player.width > self.x and
                    player.y < self.y + self.height and
                    player.y + player.height > self.y)
        return False

    def draw(self, screen):
        if not self.collected:
            screen.blit(coin_image, (self.x, self.y))

# 创建游戏对象
def create_level():
    platforms = [
        # 地面
        Platform(0, 825, 1200, 75),  # 按照原来的比例1.5倍调整
        
        # 平台
        Platform(150, 675, 150, 30),
        Platform(375, 600, 150, 30),
        Platform(600, 525, 150, 30),
        Platform(825, 450, 150, 30),
        Platform(975, 375, 150, 30),
        Platform(300, 375, 120, 30),
        Platform(150, 300, 120, 30),
        Platform(450, 225, 120, 30),
        Platform(750, 150, 120, 30),
    ]

    spikes = [
        # 地面上的尖刺
        MovingSpike(450, 800, 45, 30, "up"),
        MovingSpike(495, 800, 45, 30, "up"),
        MovingSpike(540, 800, 45, 30, "up"),
        MovingSpike(735, 800, 45, 30, "up"),
        MovingSpike(780, 800, 45, 30, "up"),
        MovingSpike(825, 800, 45, 30, "up"),

        # 平台上的尖刺
        MovingSpike(375, 570, 45, 30, "up"),
        MovingSpike(600, 495, 45, 30, "up"),
        MovingSpike(825, 420, 45, 30, "up"),

        # 墙上的尖刺
        MovingSpike(1170, 450, 30, 45, "left"),
        MovingSpike(1170, 495, 30, 45, "left"),

        
    ]

    static_spikes = [
    StaticSpike(225, 75, 45, 30, "down"),
    StaticSpike(270, 75, 45, 30, "down"),
    StaticSpike(315, 75, 45, 30, "down"),

    ]

    checkpoints = [
        Checkpoint(1050, 750),
        Checkpoint(225, 270),
    ]
    
    # 添加金币
    coins = [
        Coin(225, 630),
        Coin(450, 570),
        Coin(675, 495),
        Coin(900, 420),
        Coin(375, 330),
        Coin(225, 225),
    ]

    goal = Platform(1125, 150, 45, 45, YELLOW)  # goal 的尺寸也按比例放大

    return platforms, spikes, static_spikes, checkpoints, goal, coins

# 创建游戏对象
platforms, spikes, static_spikes, checkpoints, goal, coins = create_level()
player = Player(50, 500)
game_state = "playing"  # "playing", "win"
font = pygame.font.SysFont(None, 36)
collected_coins = 0  # 新增金币计数器
start_ticks = pygame.time.get_ticks()  # 新增开始时间戳

# 粒子效果类
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = pygame.math.Vector2(3, 3)
        self.vel = pygame.math.Vector2(
            (pygame.time.get_ticks() % 5) - 2.5,
            (pygame.time.get_ticks() % 5) - 7.5
        )
        self.lifetime = 30

    def update(self):
        self.x += self.vel.x
        self.y += self.vel.y
        self.vel.y += 0.1

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size.x, self.size.y))

particles = []

# 游戏主循环
running = True
while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and player.alive:
                player.jump()
            elif event.key == pygame.K_r:
                # 重置游戏
                platforms, spikes, checkpoints, goal = create_level()
                player = Player(50, 500)
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()  # 只有在按R时才重置计时器
            elif event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                mouse_pos = pygame.mouse.get_pos()
                if link_rect.collidepoint(mouse_pos):
                    import os
                    # 打开当前脚本所在目录下的日志.txt 文件
                    log_path = os.path.join(os.path.dirname(__file__), "Directions.txt")
                    if os.path.exists(log_path):
                        os.startfile(log_path)  # Windows系统使用startfile

    # 玩家控制
    if player.alive and game_state == "playing":
        keys = pygame.key.get_pressed()
        player.vel_x = 0
        if keys[pygame.K_LEFT]:
            player.vel_x = -PLAYER_SPEED
            player.direction = -1
        if keys[pygame.K_RIGHT]:
            player.vel_x = PLAYER_SPEED
            player.direction = 1

    # 更新游戏状态
    if player.alive and game_state == "playing":
        # 移动玩家
        on_ground = player.move(platforms)

        # 检查尖刺碰撞及触发
        for spike in spikes:
            spike.trigger_spike(player)
            # 检查玩家与尖刺的碰撞
            if spike.check_collision(player):
                player.die()
                # 创建死亡粒子
                for _ in range(20):
                    particles.append(Particle(player.x + player.width//2,
                                            player.y + player.height//2,
                                            BLUE))

            # 添加对update方法的调用
            spike.update()
        for static_spike in static_spikes:
            if static_spike.check_collision(player):
                player.die()
                # 创建死亡粒子
                for _ in range(20):
                    particles.append(Particle(player.x + player.width//2,
                                              player.y + player.height//2,
                                              BLUE))
        # 检查存档点碰撞
        for checkpoint in checkpoints:
            if checkpoint.check_collision(player):
                checkpoint.activate(player)

        # 检查金币碰撞
        for coin in coins[:]:  # 使用切片复制列表以避免在迭代时修改列表
            if coin.check_collision(player):
                coin.collected = True
                collected_coins += 1
                coins.remove(coin)  # 从列表中移除金币

        # 检查目标碰撞
        if player.check_collision(goal):
            game_state = "win"

    # 玩家死亡处理
    if not player.alive:
        # 更新粒子
        for particle in particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                particles.remove(particle)
                
        # 新增自动复活逻辑
        player.auto_respawn_timer -= 1
        if player.auto_respawn_timer <= 0:
            # 如果有激活的存档点，则在最近的存档点复活
            if any(cp.activated for cp in checkpoints):
                # 找到最后一个激活的存档点（最新存档点）
                last_checkpoint = next(cp for cp in checkpoints if cp.activated)
                # 调用respawn方法并在存档点位置复活
                player.respawn()
                player.x = last_checkpoint.x
                player.y = last_checkpoint.y - player.height
            else:
                # 否则在原点复活
                player.respawn()
            player.vel_x = 0
            player.vel_y = 0
            particles.clear()  # 清除剩余粒子
            
            # 当玩家死亡时，重置所有尖刺的状态
            for spike in spikes:
                spike.reset()

    # 绘制游戏
    screen.fill((30, 30, 50))  # 深蓝色背景

    # 绘制背景图片（添加了自适应屏幕尺寸的功能）
    scaled_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_background, (0, 0))  # 在(0,0)位置绘制缩放后的背景图片
    
    # 绘制游戏对象
    for platform in platforms:
        platform.draw(screen)

    for spike in spikes:
        spike.draw(screen)
    for static_spike in static_spikes:
        static_spike.draw(screen)

    for checkpoint in checkpoints:
        checkpoint.draw(screen)

    pygame.draw.rect(screen, YELLOW, (goal.x, goal.y, goal.width, goal.height))
    pygame.draw.rect(screen, BLACK, (goal.x, goal.y, goal.width, goal.height), 2)

    # 绘制金币
    for coin in coins:
        coin.draw(screen)

    # 绘制玩家
    if player.alive:
        player.draw(screen)

    # 绘制粒子
    for particle in particles:
        particle.draw(screen)

    # 绘制UI
    death_text = pygame.font.SysFont(None, 24).render(f"Death_count: {player.death_count}  Collected_coins: {collected_coins}", True, WHITE)
    screen.blit(death_text, (10, 10))
    
    # 新增计时器逻辑
    current_time = pygame.time.get_ticks() - start_ticks
    timer_text = pygame.font.SysFont(None, 18).render(f"Gaming time: {current_time // 1000}seconds", True, WHITE)
    screen.blit(timer_text, (10, 40))  # 在左上角绘制计时器
    
    if game_state == "win":
        win_text = font.render("恭喜通关! 按 R 重新开始", True, YELLOW)
        screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

    # 绘制操作说明
    controls = [
        "方向键: 移动",
        "↑键: 跳跃",
        "R: 重新开始",
        "ESC: 退出"
    ]

    for i, text in enumerate(controls):
        ctrl_text = pygame.font.SysFont(None, 24).render(text, True, LIGHT_BLUE)
        screen.blit(ctrl_text, (SCREEN_WIDTH - ctrl_text.get_width() - 10, 10 + i * 30))

    # 新增超链接文本
    link_text = pygame.font.SysFont(None, 24).render("Directions.txt", True, LIGHT_BLUE)
    link_rect = link_text.get_rect()
    link_rect.topleft = (SCREEN_WIDTH - link_text.get_width() - 10, 10 + (i + 1) * 30)
    screen.blit(link_text, link_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()