import pygame
import sys
import os  # 新增导入os模块用于处理文件路径
import importlib.util  # 用于动态导入模块

# 初始化 Pygame
pygame.init()

# 获取当前脚本所在目录作为资源路径
resource_path = os.path.dirname(os.path.abspath(__file__))  # 添加这行获取当前脚本目录

# 游戏常量
SCREEN_WIDTH = 1200  # 原来是 800
SCREEN_HEIGHT = 900  # 原来是 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -13
PLAYER_SPEED = 6  # 稍微提高速度以匹配更大的地图

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
GRAY = (169, 169, 169)
DARK_GRAY = (100, 100, 100)

# 新增：关卡解锁状态（初始只解锁新手教程）
unlocked_levels = {
    "tutorial": True,
    "level1": False,
    "level2": False
}

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("简易 I Wanna 游戏")
clock = pygame.time.Clock()

# 加载背景图片（请确保图片路径正确）
background_image = pygame.image.load(os.path.join(resource_path, "images", "background.jpg")).convert()  # 修改为使用resource_path

# 加载玩家图片
player_image = pygame.image.load(os.path.join(resource_path, "images", "kid.png")).convert_alpha()  # 修改为使用resource_path
player_image = pygame.transform.scale(player_image, (60, 60))  # 调整图片大小为原来的1.5倍

# 新增加载第二个玩家图片
player_image_2 = pygame.image.load(os.path.join(resource_path, "images", "kid1.png")).convert_alpha()  # 修改为使用resource_path
player_image_2 = pygame.transform.scale(player_image_2, (60, 60))  # 调整图片大小为原来的1.5倍

# 加载金币图片（请确保图片路径正确）
coin_image = pygame.image.load(os.path.join(resource_path, "images", "coin.gif")).convert_alpha()  # 修改为使用resource_path
coin_image = pygame.transform.scale(coin_image, (30, 30))  # 调整大小为30x30像素

# 加载中文字体，路径就在这个py的同一个文件夹里面
try:
    # 尝试加载simhei字体
    font_path = os.path.join(resource_path, "simhei.ttf")  # 字体文件放在同级目录下
    title_font = pygame.font.Font(font_path, 48)
    ui_font = pygame.font.Font(font_path, 36)
    small_font = pygame.font.Font(font_path, 18)  # 修改字号从24改为18
except Exception as e:
    print(f"无法加载字体文件: {e}")
    # 如果加载失败，使用默认字体
    title_font = pygame.font.SysFont(None, 48)
    ui_font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 18)  # 修改字号从24改为18

# 新增加载云朵图片
cloud_image = pygame.image.load(os.path.join(resource_path, "images", "cloud.png")).convert_alpha()  # 修改为使用resource_path
cloud_image = pygame.transform.scale(cloud_image, (200, 100))  # 调整云朵图片大小

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
        self.double_jump_available = True
        self.alive = True
        self.checkpoint = (x, y)
        self.death_count = 0
        self.direction = 1
        self.animation_frame = 0
        self.animation_images = [player_image, player_image_2]
        self.image = self.animation_images[0]
        self.bullets = []
        self.last_shot_time = 0
        self.shoot_cooldown = 300
        self.is_on_ground = False  # 新增地面状态标志
        self.request_jump = False  # 新增跳跃请求标志
        
    def handle_jump(self):
        """处理跳跃逻辑，返回是否执行了跳跃"""
        if not self.jumping:
            self.vel_y = JUMP_STRENGTH
            self.jumping = True
            return True
        elif self.double_jump_available:
            self.vel_y = JUMP_STRENGTH * 0.7
            self.double_jump_available = False
            return True
        return False
    
    # 新增方法：处理玩家控制输入
    def update_controls(self):
        """处理键盘输入控制"""
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
            self.direction = 1
            
    # 新增方法：更新玩家位置
    def update_position(self, platforms):
        """更新玩家位置并处理碰撞"""
        # 应用水平移动
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
        self.is_on_ground = on_ground  # 更新地面状态标志
        
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

    def shoot(self):
        """射击方法，创建新子弹"""
        current_time = pygame.time.get_ticks()
        # 检查是否满足射击冷却条件
        if current_time - self.last_shot_time > self.shoot_cooldown:
            # 创建新子弹，从玩家中心位置发射
            bullet = Bullet(self.x + self.width//2, self.y + self.height//2, self.direction)
            self.bullets.append(bullet)
            self.last_shot_time = current_time  # 更新最后射击时间

    def update_bullets(self):
        """更新所有子弹的状态"""
        for bullet in self.bullets[:]:  # 使用切片复制列表以避免在迭代时修改列表
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)

    def draw_bullets(self, screen):
        """绘制所有子弹"""
        for bullet in self.bullets:
            bullet.draw(screen)

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
        
        pygame.draw.polygon(screen, GRAY, points)
        pygame.draw.polygon(screen, (0,0,0) ,points, 2)

    def reset(self):
        # 静态尖刺不需要重置逻辑
        pass

# 动态尖刺类（新MovingSpike类），继承自StaticSpike
class MovingSpike(StaticSpike):
    def __init__(self, x, y, width=45, height=30, direction="up"):
        super().__init__(x, y, width, height, direction)
        self.moving_up = False  # 新增标志表示尖刺是否正在向上移动
        self.speed = 0  # 尖刺的速度
        self.original_y = y 
        self.original_x = x # 记录初始位置
        

    def update(self):
        if self.direction == "up":
            self.y -= self.speed
        elif self.direction == "down":
            self.y += self.speed
        elif self.direction == "left":
            self.x -= self.speed
        elif self.direction == "right":
            self.x += self.speed

        # 如果尖刺飞出屏幕，重置
        if (self.x + self.width < 0 or self.x > SCREEN_WIDTH or
            self.y + self.height < 0 or self.y > SCREEN_HEIGHT):
            self.moving_up = False
            self.speed = 0

    def trigger_spike(self, player):
        # 根据朝向判断玩家是否在尖刺的前方
        if self.direction == "up" and self.y-200 <= player.y + player.height <= self.y and player.x + player.width > self.x and player.x < self.x + self.width:
            self.speed = 7
            
        elif self.direction == "down" and self.y + self.height + 200>= player.y >= self.y + self.height and player.x + player.width > self.x and player.x < self.x + self.width:
            self.speed = 7
            
        elif self.direction == "left" and self.x-200 <= player.x + player.width <= self.x and player.y + player.height > self.y and player.y < self.y + self.height:
            self.speed = 7
            
        elif self.direction == "right" and self.x+200 >=player.x >= self.x + self.width and player.y + player.height > self.y and player.y < self.y + self.height:
            self.speed = 7
            


    def reset(self):
        # 重置动态尖刺状态
        self.x = self.original_x
        self.y = self.original_y
        self.speed = 0

# 新增 Cloud 类
class Cloud:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = cloud_image.get_width()
        self.height = cloud_image.get_height()


    def draw(self, screen):
        screen.blit(cloud_image, (self.x, self.y))

# 存档点类
class Checkpoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.activated = False
        self.activation_time = None  # 新增：记录激活时间

    def activate(self, player):
        if not self.activated:
            player.checkpoint = (self.x, self.y)
            self.activated = True
            self.activation_time = pygame.time.get_ticks()  # 记录当前时间

    def check_collision(self, player):
        return (player.x < self.x + self.width and
                player.x + player.width > self.x and
                self.y + self.height > player.y and
                self.y < player.y + player.height)

    def draw(self, screen):
        color = YELLOW if self.activated else PURPLE
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

        # 绘制存档点标志
        if self.activated:
            pygame.draw.circle(screen, GREEN, (self.x + self.width//2, self.y + self.height//2), 7)
        else:
            pygame.draw.circle(screen, WHITE, (self.x + self.width//2, self.y + self.height//2), 7)

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

# 在Coin类之后添加子弹类
class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.width = 5  # 很小的碰撞体积
        self.height = 5
        self.speed = 10
        self.direction = direction  # 1为向右，-1为向左
        self.active = True
        self.range = 600  # 新增射程限制，单位为像素
        self.distance_traveled = 0  # 已飞行的距离

    def update(self):
        # 子弹向前飞行
        self.x += self.speed * self.direction
        self.distance_traveled += abs(self.speed * self.direction)  # 更新已飞行距离
        
        # 如果子弹移出屏幕或达到射程，标记为非活动
        if self.x < -self.width or self.x > SCREEN_WIDTH + self.width or self.distance_traveled >= self.range:
            self.active = False

    def check_collision(self, player):
        return (player.x < self.x + self.width and
                player.x + player.width > self.x and
                player.y < self.y + self.height and
                player.y + player.height > self.y)

    def draw(self, screen):
        # 绘制子弹为红色矩形
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
def show_game_over_screen():
    """显示游戏结束界面"""
    game_over_font = pygame.font.SysFont("SimHei", 48)
    restart_font = pygame.font.SysFont("SimHei", 36)
    
    # 创建半透明覆盖层
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 黑色半透明背景
    
    while True:
        # 绘制游戏背景（保持游戏场景可见）
        scaled_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_background, (0, 0))
        
        # 绘制游戏对象（平台、尖刺等）
        for platform in platforms:
            platform.draw(screen)
        for spike in spikes:
            spike.draw(screen)
        for static_spike in static_spikes:
            static_spike.draw(screen)
        for checkpoint in checkpoints:
            checkpoint.draw(screen)
        for coin in coins:
            coin.draw(screen)
        
        # 添加半透明覆盖层
        screen.blit(overlay, (0, 0))
        
        # 显示 "Game Over"
        game_over_text = game_over_font.render("游戏结束", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3))
        
        # 显示死亡次数
        death_count_text = restart_font.render(f"死亡次数: {player.death_count}", True, WHITE)
        screen.blit(death_count_text, (SCREEN_WIDTH // 2 - death_count_text.get_width() // 2, SCREEN_HEIGHT // 2))
        
        # 显示重新开始提示
        restart_text = restart_font.render("按任意键返回", True, LIGHT_BLUE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        
        pygame.display.flip()
        
        # 事件处理 - 等待任意按键
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return  # 返回主游戏循环

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
        Platform(300, 375, 120, 30),
        Platform(150, 300, 120, 30),
        Platform(450, 225, 120, 30),
        Platform(750, 150, 120, 30),
    ]

    spikes = [
        # 地面上的尖刺
        #MovingSpike(450, 800, 45, 30, "up"),
        #MovingSpike(495, 800, 45, 30, "up"),
        #MovingSpike(540, 800, 45, 30, "up"),
        #MovingSpike(735, 800, 45, 30, "up"),
        #MovingSpike(780, 800, 45, 30, "up"),
        #MovingSpike(825, 800, 45, 30, "up"),

        # 平台上的尖刺
        #MovingSpike(375, 570, 45, 30, "up"),
        #MovingSpike(600, 495, 45, 30, "up"),
        #MovingSpike(825, 420, 45, 30, "up"),

        # 墙上的尖刺
        MovingSpike(1170, 450, 30, 45, "left"),
        #MovingSpike(1170, 495, 30, 45, "left"),

        
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

    # 添加一个测试用的子弹
    bullets = [

    ]

    return platforms, spikes, static_spikes, checkpoints, goal, coins, bullets

# 新增关卡2地图
def create_level2():
    platforms = [
        # 地面
        Platform(0, 825, 1200, 75),
        
        # 平台 - 更复杂的布局
        Platform(100, 700, 100, 30),
        Platform(250, 650, 100, 30),
        Platform(400, 600, 100, 30),
        Platform(550, 550, 100, 30),
        Platform(700, 500, 100, 30),
        Platform(850, 450, 100, 30),
        Platform(1000, 400, 100, 30),
        
        # 垂直平台
        Platform(200, 500, 30, 200),
        Platform(500, 400, 30, 200),
        Platform(800, 300, 30, 200),
        
        # 移动平台
        Platform(300, 400, 100, 30, BLUE),
        Platform(600, 300, 100, 30, BLUE),
    ]

    spikes = [
        # 动态尖刺
        MovingSpike(350, 795, 45, 30, "up"),
        MovingSpike(395, 795, 45, 30, "up"),
        MovingSpike(650, 795, 45, 30, "up"),
        MovingSpike(695, 795, 45, 30, "up"),
        
        # 墙上的尖刺
        MovingSpike(1170, 300, 30, 45, "left"),
        MovingSpike(1170, 345, 30, 45, "left"),
        MovingSpike(1170, 390, 30, 45, "left"),
    ]

    static_spikes = [
        # 天花板尖刺
        StaticSpike(150, 75, 45, 30, "down"),
        StaticSpike(195, 75, 45, 30, "down"),
        StaticSpike(240, 75, 45, 30, "down"),
        
        # 平台上的尖刺
        StaticSpike(550, 520, 45, 30, "up"),
        StaticSpike(850, 420, 45, 30, "up"),
    ]
    clouds =[]

    checkpoints = [
        Checkpoint(150, 750),
        Checkpoint(600, 350),
        Checkpoint(1050, 150),
    ]
    
    # 添加金币
    coins = [
        Coin(150, 670),
        Coin(300, 620),
        Coin(450, 570),
        Coin(600, 520),
        Coin(750, 470),
        Coin(900, 420),
        Coin(1050, 370),
        Coin(250, 450),
        Coin(550, 350),
        Coin(850, 250),
    ]

    goal = Platform(1125, 100, 45, 45, YELLOW)

    bullets = []

    return platforms, spikes, static_spikes, checkpoints, goal, coins, bullets

# 创建游戏对象
platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level()
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

# 新增关卡选择界面函数
def show_level_selection():
    selecting = True
    # 创建地面和玩家对象用于关卡选择界面
    ground = Platform(0, 825, 1200, 75)
    level_selection_player = Player(50, 500)
    
    while selecting:
        # 使用背景图片而不是纯色填充
        scaled_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_background, (0, 0))
        ground.draw(screen)
        
        title_text = pygame.font.SysFont("SimHei", 48).render("选择关卡", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))

        # 新手教程按钮（始终可点击）
        tutorial_text = pygame.font.SysFont("SimHei", 36).render("新手教程", True, LIGHT_BLUE)
        tutorial_rect = tutorial_text.get_rect()
        tutorial_rect.topleft = (SCREEN_WIDTH//2 - tutorial_rect.width//2, 150)
        screen.blit(tutorial_text, tutorial_rect)

        # 关卡1按钮（根据解锁状态显示不同颜色）
        level1_color = LIGHT_BLUE if unlocked_levels["level1"] else DARK_GRAY
        level1_text = pygame.font.SysFont("SimHei", 36).render("关卡1", True, level1_color)
        level1_rect = level1_text.get_rect()
        level1_rect.topleft = (SCREEN_WIDTH//2 - level1_rect.width//2, 225)
        screen.blit(level1_text, level1_rect)

        # 关卡2按钮（根据解锁状态显示不同颜色）
        level2_color = LIGHT_BLUE if unlocked_levels["level2"] else DARK_GRAY
        level2_text = pygame.font.SysFont("SimHei", 36).render("关卡2", True, level2_color)
        level2_rect = level2_text.get_rect()
        level2_rect.topleft = (SCREEN_WIDTH//2 - level2_rect.width//2, 300)
        screen.blit(level2_text, level2_rect)
        
        # 绘制关卡选择界面的玩家
        keys = pygame.key.get_pressed()
        level_selection_player.vel_x = 0
        if keys[pygame.K_LEFT]:
            level_selection_player.vel_x = -PLAYER_SPEED
            level_selection_player.direction = -1
        elif keys[pygame.K_RIGHT]:
            level_selection_player.vel_x = PLAYER_SPEED
            level_selection_player.direction = 1
            
        # 更新玩家位置并处理地面碰撞
        level_selection_player.x += level_selection_player.vel_x
        level_selection_player.y += level_selection_player.vel_y
        
        # 应用重力
        level_selection_player.vel_y += GRAVITY
        
        # 地面碰撞检测
        on_ground = False
        if level_selection_player.check_collision(ground):
            if level_selection_player.vel_y > 0:  # 下落
                level_selection_player.y = ground.y - level_selection_player.height
                level_selection_player.vel_y = 0
                on_ground = True
                # 重置跳跃状态
                level_selection_player.jumping = False
                level_selection_player.double_jump_available = True
        
        # 边界检查
        if level_selection_player.x < 0:
            level_selection_player.x = 0
        if level_selection_player.x > SCREEN_WIDTH - level_selection_player.width:
            level_selection_player.x = SCREEN_WIDTH - level_selection_player.width

        # 更新和绘制子弹
        level_selection_player.update_bullets()
        level_selection_player.draw(screen)
        level_selection_player.draw_bullets(screen)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    level_selection_player.handle_jump()
                # 按空格键发射子弹
                if event.key == pygame.K_SPACE:
                    level_selection_player.shoot()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if tutorial_rect.collidepoint(mouse_pos):
                        selecting = False
                        return "tutorial"
                    elif level1_rect.collidepoint(mouse_pos) and unlocked_levels["level1"]:
                        selecting = False
                        return "level1"
                    elif level2_rect.collidepoint(mouse_pos) and unlocked_levels["level2"]:
                        selecting = False
                        return "level2"

        pygame.display.flip()
        clock.tick(FPS)

# 新增创建新手教程关卡函数
def create_tutorial_level():
    """创建新手教程关卡"""
    platforms = [
        # 教程地面
        Platform(0, 825, 1200, 75),
        
        # 基础移动教学平台
        Platform(150, 700, 150, 30),
        Platform(350, 700, 150, 30),
        Platform(550, 700, 150, 30),

        # 跳跃教学平台
        Platform(250, 550, 100, 30),
        Platform(450, 400, 100, 30),
        Platform(600, 250, 100, 30),
        
        # 子弹演示平台
        Platform(900, 600, 150, 30),
    ]

    spikes = [
        # 新增：在通关区域添加一个动态尖刺
        MovingSpike(900, 795, 45, 30, "up")
    ]
    
    static_spikes = [
        # 新增静态刺
        StaticSpike(700, 795, 45, 30, "up")
    ]

    checkpoints = [
        # 新增：在通关路径上添加一个存档点
        Checkpoint(800, 790)
    ]

    clouds = [
        Cloud(SCREEN_WIDTH * 0.5, 100),
    ]

    # 添加教学用金币
    coins = [
        Coin(200, 670),  # 移动教学区
        Coin(400, 670),
        Coin(600, 670),
        Coin(800, 670),
        
        Coin(270, 520),  # 跳跃教学区
        Coin(470, 370),
        Coin(670, 220),
    ]
    
    # 修改为黄色方形区域作为通关目标
    goal = Platform(1100, 150, 45, 45, YELLOW)  # 使用黄色方形区域表示通关位置
    
    # 创建教学文本，使用更小的字体并移除箭头指示
    tutorial_texts = [
        {"text": "← → 键：左右移动", "pos": (200, 750)},
        {"text": "↑ 键：跳跃", "pos": (250, 600)},
        {"text": "↑ 键：二段跳（在空中再次按下跳跃）", "pos": (450, 450)},
        {"text": "空格键：射击", "pos": (900, 550)},
        {"text": "按R键重新开始关卡", "pos": (100, 100)},
        {"text": "ESC键返回关卡选择", "pos": (100, 130)},
        {"text": "黄色方形区域是通关位置", "pos": (100, 160)},
        {"text": "这个尖刺会向上弹起", "pos": (900, 720)},
        {"text": "这个尖刺是固定的", "pos": (700, 720)}
    ]
    
    return platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,clouds

# 游戏主循环前展示关卡选择界面
selected_level = show_level_selection()
if selected_level is None:
    pygame.quit()
    sys.exit()

# 根据选择的关卡创建不同地图
if selected_level == "tutorial":
    # 新手教程关卡
    platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,clouds = create_tutorial_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
elif selected_level == "level1":
    # 关卡1
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,clouds  = create_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
elif selected_level == "level2":  # 新增：处理关卡2
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level2()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
else:
    # 默认关卡
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()

# 初始化云朵


# 游戏主循环
running = True
while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and player.alive:
                player.handle_jump()  # 使用统一方法处理跳跃
            elif event.key == pygame.K_SPACE and player.alive:
                # 向当前方向发射一颗子弹
                bullets.append(Bullet(player.x + player.width//2, player.y + player.height//2, player.direction))
            elif event.key == pygame.K_r:
                # 重置游戏
                platforms, spikes, checkpoints, goal = create_level()
                player = Player(50, 500)
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()  # 只有在按R时才重置计时器
            elif event.key == pygame.K_ESCAPE:
                # 修改为返回关卡选择界面
                selected_level = None
                running = False
                next_level = show_level_selection()
                if next_level is not None:
                    selected_level = next_level
                    # 重新初始化游戏
                    if selected_level == "tutorial":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts = create_tutorial_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level1":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level2":  # 新增：处理关卡2
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level2()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    running = True  # 重新开始游戏循环
   
    # 玩家控制 - 现在完全封装在Player类中
    if player.alive and game_state == "playing":
        player.update_controls()  # 处理键盘输入
        player.update_position(platforms)  # 更新位置和碰撞检测

    # 更新游戏状态
    if player.alive and game_state == "playing":
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
            # 通关后解锁下一关
            if selected_level == "tutorial" and not unlocked_levels["level1"]:
                unlocked_levels["level1"] = True
                # 自动进入第一关
                selected_level = "level1"
            elif selected_level == "level1" and not unlocked_levels["level2"]:
                unlocked_levels["level2"] = True
                # 自动进入第二关
                selected_level = "level2"
            else:
                # 如果已经是最后一关，返回关卡选择界面
                selected_level = None
        
            # 重新初始化游戏
            running = False  # 结束当前游戏循环
            if selected_level is not None:
                if selected_level == "tutorial":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,clouds = create_tutorial_level()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                elif selected_level == "level1":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets= create_level()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                elif selected_level == "level2":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level2()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                running = True  # 重新开始游戏循环
            else:
                # 显示关卡选择界面
                next_level = show_level_selection()
                if next_level is not None:
                    selected_level = next_level
                    # 重新初始化游戏
                    if selected_level == "tutorial":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,clouds = create_tutorial_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level1":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets= create_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level2":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets = create_level2()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    running = True  # 重新开始游戏循环

        # 新增：更新子弹
        for bullet in bullets[:]:
            bullet.update()
            if not bullet.active:
                bullets.remove(bullet)

    # 玩家死亡处理
    if not player.alive:
        for spike in spikes:
                spike.reset()
        # 更新粒子
        for particle in particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                particles.remove(particle)
        
        show_game_over_screen()

        player.alive = True
        player.respawn()      
        # 新增自动复活逻辑
        player.auto_respawn_timer -= 1
        if player.auto_respawn_timer <= 0:
            # 获取所有激活的存档点
            active_checkpoints = [cp for cp in checkpoints if cp.activated]
            if active_checkpoints:
                # 按激活时间排序，找到最新的存档点
                last_checkpoint = max(active_checkpoints, key=lambda x: x.activation_time)
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

    pygame.draw.rect(screen, YELLOW, (goal.x, goal.y, goal.width, goal.height)) if goal else None
    pygame.draw.rect(screen, BLACK, (goal.x, goal.y, goal.width, goal.height), 2) if goal else None

    # 绘制金币
    for coin in coins:
        coin.draw(screen)

    # 新增：绘制子弹
    for bullet in bullets:
        bullet.draw(screen)

    # 绘制教程文本（如果当前是教程关卡）
    if selected_level == "tutorial":
        for tutorial_text_info in tutorial_texts:
            text_surface = small_font.render(tutorial_text_info["text"], True, YELLOW)
            screen.blit(text_surface, tutorial_text_info["pos"])

    # 绘制玩家
    if player.alive:
        player.draw(screen)

    # 绘制粒子
    for particle in particles:
        particle.draw(screen)

    # 绘制UI
    death_text = pygame.font.SysFont("SimHei", 24).render(f"死亡数: {player.death_count}  硬币: {collected_coins}", True, WHITE)
    screen.blit(death_text, (10, 10))
    
    # 新增计时器逻辑
    current_time = pygame.time.get_ticks() - start_ticks
    timer_text = pygame.font.SysFont("SimHei", 18).render(f"游戏时间: {current_time // 1000}秒", True, WHITE)
    screen.blit(timer_text, (10, 40))  # 在左上角绘制计时器
    
    if game_state == "win":
        win_text = pygame.font.SysFont("SimHei", 24).render("恭喜通关! 按 R 重新开始", True, YELLOW)
        screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, SCREEN_HEIGHT//2))

    # 绘制操作说明
    controls = [
        "方向键: 移动",
        "↑键: 跳跃",
        "R: 重新开始",
        "ESC: 退出"
    ]

    for i, text in enumerate(controls):
        ctrl_text = pygame.font.SysFont("SimHei", 24).render(text, True, LIGHT_BLUE)
        screen.blit(ctrl_text, (SCREEN_WIDTH - ctrl_text.get_width() - 10, 10 + i * 30))

    # 新增超链接文本
    link_text = pygame.font.SysFont("SimHei", 24).render("Directions.txt", True, LIGHT_BLUE)
    link_rect = link_text.get_rect()
    link_rect.topleft = (SCREEN_WIDTH - link_text.get_width() - 10, 10 + (i + 1) * 30)
    screen.blit(link_text, link_rect)



    # 绘制云朵（在绘制玩家、平台等元素之前）
    for cloud in clouds:
        cloud.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()