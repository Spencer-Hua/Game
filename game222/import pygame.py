import pygame
import sys
import os  # 新增导入os模块用于处理文件路径
import importlib.util  # 用于动态导入模块
import random  # 新增导入random模块用于随机关卡生成
import math

# 初始化 Pygame
pygame.init()

# 获取当前脚本所在目录作为资源路径
resource_path = os.path.dirname(os.path.abspath(__file__))  # 添加这行获取当前脚本目录
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(resource_path, "bgm.mp3"))
pygame.mixer.music.play(-1, 0.0)
#加载死亡音效
die_sound = pygame.mixer.Sound(os.path.join(resource_path, "die.mp3"))
die_sound.set_volume(1) # 可选：调节音量
victory_sound = pygame.mixer.Sound(os.path.join(resource_path, "victory.mp3"))
victory_sound.set_volume(1)
# 游戏常量
SCREEN_WIDTH = 1200  # 原来是 800
SCREEN_HEIGHT = 900  # 原来是 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -11
PLAYER_SPEED = 5  # 稍微提高速度以匹配更大的地图

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
    "level2": False,
    "boss": False
}

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("简易 I Wanna 游戏")
clock = pygame.time.Clock()

# 加载背景图片（请确保图片路径正确）
background_image = pygame.image.load(os.path.join(resource_path, "images", "background.jpg")).convert()  # 修改为使用resource_path

# 加载玩家图片
player_image = pygame.image.load(os.path.join(resource_path, "images", "kid.png")).convert_alpha()  # 修改为使用resource_path
player_image = pygame.transform.scale(player_image, (50, 50))  # 调整图片大小为原来的1.5倍

# 新增加载第二个玩家图片
player_image_2 = pygame.image.load(os.path.join(resource_path, "images", "kid1.png")).convert_alpha()  # 修改为使用resource_path
player_image_2 = pygame.transform.scale(player_image_2, (50, 50))  # 调整图片大小为原来的1.5倍

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


# 玩家类
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = player_image.get_width()-15
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
        self.shoot_cooldown = 1000
        self.is_on_ground = False  # 新增地面状态标志
        self.request_jump = False  # 新增跳跃请求标志
        
    def handle_jump(self):
        """处理跳跃逻辑，返回是否执行了跳跃"""
        if not self.jumping and self.is_on_ground== True:
            self.vel_y = JUMP_STRENGTH
            self.jumping = True
            return True
        elif self.double_jump_available:
            self.vel_y = JUMP_STRENGTH * 0.8
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
        return (player.x < self.x <player.x + player.width and
                player.y < self.y <player.y + player.height
            )

    def draw(self, screen):
        # 绘制子弹为红色矩形
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 100
        self.height = 100
        self.vel_x = 2  # 水平移动速度
        self.vel_y = 2
        self.health = 5  # BOSS血量
        self.max_health = 5
        self.direction = 1  # 1为右，-1为左
        self.bullets = []  # BOSS的子弹
        self.last_shot_time = 0
        self.shoot_cooldown = 1000  # 射击冷却时间（毫秒）
        self.move_pattern = 0  # 移动模式
        self.pattern_timer = 0
        self.attack_pattern = 0  # 攻击模式
        self.attack_timer = 0
        
    def update(self, player):
        """更新BOSS状态"""
        current_time = pygame.time.get_ticks()
        
        self.x += self.vel_x
        self.y += self.vel_y

        # 碰到左右边界，水平速度反向
        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.vel_x *= -1

        # 碰到上下边界，垂直速度反向
        if self.y <= 100 or self.y >= SCREEN_HEIGHT - 100 - self.height:
            self.vel_y *= -1

        # 保持 BOSS 在屏幕内（防止卡出边界）
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - 100 - self.height))
        
        # 攻击模式切换
        if current_time - self.attack_timer > 1000:  # 每2秒切换一次攻击模式
            self.attack_pattern = random.randint(0, 2)
            self.attack_timer = current_time
        
        # 根据攻击模式射击
        if current_time - self.last_shot_time > self.shoot_cooldown:
            if self.attack_pattern == 0:  # 单发子弹
                self.shoot_single(player)
            elif self.attack_pattern == 1:  # 三发子弹
                self.shoot_triple(player)
            elif self.attack_pattern == 2:  # 圆形弹幕
                self.shoot_circle()
            self.last_shot_time = current_time
        
        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)
    
    def is_on_ground(self):
        """检查BOSS是否在地面上"""
        return self.y >= SCREEN_HEIGHT - 200 - self.height - 5
    
    def shoot_single(self, player):
        """单发子弹攻击"""
        # 计算朝向玩家的方向
        dx = player.x - self.x
        dy = player.y - self.y
        distance = max(1, (dx**2 + dy**2)**0.5)  # 避免除以0
        direction_x = dx / distance
        direction_y = dy / distance
        
        bullet = BossBullet(self.x + self.width//2, self.y + self.height//2, direction_x, direction_y)
        self.bullets.append(bullet)
    
    def shoot_triple(self, player):
        """三发子弹攻击"""
        # 中间子弹直接瞄准玩家
        dx = player.x - self.x
        dy = player.y - self.y
        distance = max(1, (dx**2 + dy**2)**0.5)
        direction_x = dx / distance
        direction_y = dy / distance
        
        self.bullets.append(BossBullet(self.x + self.width//2, self.y + self.height//2, direction_x, direction_y))
        
        # 左右子弹有角度偏移
        angle_offset = 0.3  # 约17度
        left_dx = direction_x * math.cos(angle_offset) - direction_y * math.sin(angle_offset)
        left_dy = direction_x * math.sin(angle_offset) + direction_y * math.cos(angle_offset)
        right_dx = direction_x * math.cos(-angle_offset) - direction_y * math.sin(-angle_offset)
        right_dy = direction_x * math.sin(-angle_offset) + direction_y * math.cos(-angle_offset)
        
        self.bullets.append(BossBullet(self.x + self.width//2, self.y + self.height//2, left_dx, left_dy))
        self.bullets.append(BossBullet(self.x + self.width//2, self.y + self.height//2, right_dx, right_dy))
    
    def shoot_circle(self):
        """圆形弹幕攻击"""
        num_bullets = 8  # 8个方向的子弹
        for i in range(num_bullets):
            angle = 2 * math.pi * i / num_bullets
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            bullet = BossBullet(self.x + self.width//2, self.y + self.height//2, direction_x, direction_y)
            self.bullets.append(bullet)
    
    def take_damage(self):
        """BOSS受到伤害"""
        self.health -= 1
        if self.health <= 0:
            return True  # BOSS被击败
        return False
    
    def draw(self, screen):
        """绘制BOSS"""
        # 绘制BOSS主体（红色矩形）
        pygame.draw.rect(screen, DARK_RED, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        
        # 绘制BOSS眼睛
        eye_color = RED if self.attack_pattern == 2 else BLACK  # 攻击时眼睛变红
        pygame.draw.circle(screen, eye_color, (self.x + 25, self.y + 25), 8)
        pygame.draw.circle(screen, eye_color, (self.x + 55, self.y + 25), 8)
        
        # 绘制血条
        bar_width = 400
        bar_height = 30
        # 将血条放在屏幕底部中间位置
        bar_x = SCREEN_WIDTH//2 - bar_width//2
        bar_y = SCREEN_HEIGHT - 50  # 距离屏幕底部50像素
        
        # 背景
        pygame.draw.rect(screen, BLACK, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        # 空血条
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        # 当前血量
        health_width = int(bar_width * self.health / self.max_health)
        pygame.draw.rect(screen, RED, (bar_x, bar_y, health_width, bar_height))
        
        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen)
# BOSS子弹类
class BossBullet(Bullet):
    def __init__(self, x, y, direction_x, direction_y):
        super().__init__(x, y, 1)  # direction参数在这里不重要
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = 5
        self.color = PURPLE  # BOSS子弹为紫色
        
    def update(self):
        """更新子弹位置"""
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 检查是否超出屏幕
        if (self.x < -self.width or self.x > SCREEN_WIDTH + self.width or
            self.y < -self.height or self.y > SCREEN_HEIGHT + self.height):
            self.active = False
    
    def draw(self, screen):
        """绘制BOSS子弹"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 5)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), 5, 1)
class Goal:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = YELLOW
        self.image = pygame.image.load(os.path.join(resource_path, "images", "goal.png")).convert_alpha() 
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, player):
        """检查玩家是否与目标相交"""
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)



# 平台类
class Platform:
    def __init__(self, x, y, width, height, color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.image = pygame.image.load(os.path.join(resource_path, "images", "platform.png")).convert_alpha() 
        self.image = pygame.transform.scale(self.image, (self.width, self.height))


    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

class FakePlatform:

    def __init__(self, x, y, width, height, color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.alpha = 255  # 初始不透明
        self.image = pygame.image.load(os.path.join(resource_path, "images", "platform.png")).convert_alpha() 
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def update_alpha(self, player):
        """根据是否与玩家重叠设置透明度"""
        if (player.x < self.x + self.width and
            player.x + player.width > self.x and
            player.y < self.y + self.height and
            player.y + player.height > self.y):
            self.alpha = 100  # 重叠 → 半透明
        else:
            self.alpha = 255  # 无重叠 → 不透明

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
# 尖刺基类（原Spike类）
class StaticSpike:
    def __init__(self, x, y, width=45, height=30, direction="up"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.direction = direction

    def check_collision(self, player):
        # 使用多边形进行碰撞检测
        spike_points = self.get_spike_points()

        # 创建一个面具（mask）用于碰撞检测
        spike_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(spike_surface, (255, 255, 255), spike_points)
        spike_mask = pygame.mask.from_surface(spike_surface)

        # 玩家矩形的碰撞面具
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        player_surface = pygame.Surface((player.width, player.height), pygame.SRCALPHA)
        player_surface.fill((255, 255, 255))  # 填充白色
        player_mask = pygame.mask.from_surface(player_surface)

        # 计算碰撞区域的偏移量
        offset_x = player.x - self.x
        offset_y = player.y - self.y

        # 检查碰撞
        overlap = spike_mask.overlap(player_mask, (offset_x, offset_y))
        return overlap is not None

    def get_spike_points(self):
        # 根据方向返回尖刺的点
        points = []
        if self.direction == "up":
            points = [(0, self.height), 
                      (self.width // 2, 0), 
                      (self.width, self.height)]
        elif self.direction == "down":
            points = [(0, 0), 
                      (self.width // 2, self.height), 
                      (self.width, 0)]
        elif self.direction == "left":
            points = [(self.width, 0), 
                      (0, self.height // 2), 
                      (self.width, self.height)]
        elif self.direction == "right":
            points = [(0, 0), 
                      (self.width, self.height // 2), 
                      (0, self.height)]
        return points

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

        """# 如果尖刺飞出屏幕，重置
        if (self.x + self.width < 0 or self.x > SCREEN_WIDTH or
            self.y + self.height < 0 or self.y > SCREEN_HEIGHT):
            self.moving_up = False
            self.speed = 0
            self.reset()"""
    def trigger_spike(self, player):
        # 根据朝向判断玩家是否在尖刺的前方
        if self.direction == "up" and self.y-100 <= player.y + player.height <= self.y and player.x + player.width > self.x and player.x < self.x + self.width:
            self.speed = 12
            
        elif self.direction == "down" and self.y + self.height + 100>= player.y >= self.y + self.height and player.x + player.width > self.x and player.x < self.x + self.width:
            self.speed = 12
            
        elif self.direction == "left" and self.x-100 <= player.x + player.width <= self.x and player.y + player.height > self.y and player.y < self.y + self.height:
            self.speed = 12
            
        elif self.direction == "right" and self.x+100 >=player.x >= self.x + self.width and player.y + player.height > self.y and player.y < self.y + self.height:
            self.speed = 12
            


    def reset(self):
        # 重置动态尖刺状态
        self.x = self.original_x
        self.y = self.original_y
        self.speed = 0


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

# 金币类
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

# 烟花粒子类
class Firework:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.exploded = False
        self.create_particles()

    def create_particles(self):
        # 创建粒子
        num_particles = random.randint(50, 100)
        angle_step = 2 * math.pi / num_particles
        for i in range(num_particles):
            angle = i * angle_step
            speed = random.uniform(1, 3)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append([self.x, self.y, vx, vy, self.color, random.randint(1, 4)])

    def update(self):
        if not self.exploded:
            self.exploded = True
            self.create_particles()

        # 更新粒子位置
        for particle in self.particles:
            particle[0] += particle[2]
            particle[1] += particle[3]
            particle[5] -= 0.05  # 粒子衰减

            if particle[5] <= 0:
                self.particles.remove(particle)

    def draw(self):
        for particle in self.particles:
            pygame.draw.circle(screen, particle[4], (int(particle[0]), int(particle[1])), int(particle[5]))

def show_game_over_screen():
    """显示游戏结束界面"""
    game_over_font = pygame.font.SysFont("SimHei", 48)
    restart_font = pygame.font.SysFont("SimHei", 36)
    
    # 创建半透明覆盖层
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 黑色半透明背景
    die_sound.play()
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
        for fake_platform in fakeplatforms:
            fake_platform.draw(screen)
        
        # 添加半透明覆盖层
        screen.blit(overlay, (0, 0))
        
        # 显示 "Game Over"
        game_over_text = game_over_font.render("游戏结束", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3))
        
        # 显示死亡次数
        death_count_text = restart_font.render(f"死亡次数: {player.death_count}", True, WHITE)
        screen.blit(death_count_text, (SCREEN_WIDTH // 2 - death_count_text.get_width() // 2, SCREEN_HEIGHT // 2))
        
        # 显示重新开始提示
        restart_text = restart_font.render("按r键返回", True, LIGHT_BLUE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        
        pygame.display.flip()
        
        # 事件处理 - 等待任意按键
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif  event.type == event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:

                    return  # 返回主游戏循环
            
def show_game_win_screen():
    """显示游戏胜利界面"""
    win_font = pygame.font.SysFont("SimHei", 48)
    restart_font = pygame.font.SysFont("SimHei", 36)
    
    # 创建半透明覆盖层
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 黑色半透明背景
    victory_sound.play()
    fireworks = []
    pygame.mixer.music.pause()
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
        for fake_platform in fakeplatforms:
            fake_platform.draw(screen)
        
        # 添加半透明覆盖层
        screen.blit(overlay, (0, 0))
        
        # 显示 "游戏胜利"
        win_text = win_font.render("游戏胜利", True, GREEN)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 3))
        
        # 显示获胜信息
        victory_info_text = restart_font.render(f"总死亡次数: {player.death_count}", True, WHITE)
        screen.blit(victory_info_text, (SCREEN_WIDTH // 2 - victory_info_text.get_width() // 2, SCREEN_HEIGHT // 2))
        
        # 显示重新开始提示
        restart_text = restart_font.render("按鼠标左键返回", True, LIGHT_BLUE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        if random.random() < 0.02:
            firework = Firework(random.randint(100, 700), random.randint(100, 400), random.choice([RED, GREEN, BLUE]))
            fireworks.append(firework)

        # 更新屏幕

        
        for firework in fireworks:
            firework.update()
            firework.draw()

        pygame.display.flip()
        clock.tick(60)

        
        # 事件处理 - 等待鼠标点击
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                victory_sound.stop()
                pygame.mixer.music.unpause()
                return  # 返回主游戏循环

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
        
        
        # 新增BOSS关按钮
        boss_color = LIGHT_BLUE if unlocked_levels["boss"] else DARK_GRAY
        boss_text = pygame.font.SysFont("SimHei", 36).render("BOSS挑战", True, boss_color)
        boss_rect = boss_text.get_rect()
        boss_rect.topleft = (SCREEN_WIDTH//2 - boss_rect.width//2, 375)
        screen.blit(boss_text, boss_rect)

        # 新增：随机关卡按钮
        random_level_text = pygame.font.SysFont("SimHei", 36).render("随机关卡", True, LIGHT_BLUE)
        random_level_rect = random_level_text.get_rect()
        random_level_rect.topleft = (SCREEN_WIDTH//2 - random_level_rect.width//2, 450)
        screen.blit(random_level_text, random_level_rect)

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
                    elif random_level_rect.collidepoint(mouse_pos):  # 新增：处理随机关卡选择
                        selecting = False
                        return "random"
                    elif boss_rect.collidepoint(mouse_pos) and unlocked_levels["boss"]:  # 新增BOSS关选择
                        selecting = False
                        boss=[Boss(600,600)]
                        return "boss"

        pygame.display.flip()
        clock.tick(FPS)

# 创建游戏对象
def create_level():
    fakeplatforms=[

    ]
    platforms = [
        # 地面
        Platform(0, 825, 1200, 75),  # 按照原来的比例1.5倍调整
        
        # 平台
        Platform(150, 675, 150, 30),
        Platform(375, 600, 150, 30),
        Platform(600, 525, 150, 30),
        Platform(825, 450, 150, 30),
        Platform(300, 420, 120, 30),
        Platform(150, 300, 120, 30),
        Platform(450, 225, 120, 30),
        Platform(750, 150, 120, 30),
    ]

    spikes = [

        # 墙上的尖刺
        MovingSpike(1170, 450, 30, 45, "left"),
        MovingSpike(450, 650, 45, 30, "up"),
        MovingSpike(300, 390, 45, 30, "up")

    ]

    static_spikes = [
    StaticSpike(225, 75, 45, 30, "down"),
    StaticSpike(270, 75, 45, 30, "down"),
    StaticSpike(315, 75, 45, 30, "down"),
    StaticSpike(660, 30, 45, 30, "down"),
    StaticSpike(825, 420, 45, 30, "up")

    ]

    checkpoints = [
        Checkpoint(900, 420),
        Checkpoint(225, 270),
    ]
    
    bullets = []
    # 添加金币
    coins = [
        Coin(225, 630),
        Coin(450, 570),
        Coin(930, 425),
        Coin(375, 330),
        Coin(225, 225),
    ]

    goal = Goal(1000, 150, 45, 45)  # 放置在右上角


    return platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms

# 新增关卡2地图
def create_level2():
    platforms = [
         # 平台 - 更复杂的布局
        Platform(60, 700, 100, 50),
        Platform(300, 750, 50, 50),
        Platform(400, 700, 100, 50),
        Platform(0, 400, 350, 50),
        Platform(200, 365, 100, 35),
        Platform(100, 250, 50, 50),
        Platform(230, 100, 50, 50),
        Platform(390, 220, 50, 50),

        Platform(500, 320, 150, 30),
        Platform(650, 350, 150, 50),
        Platform(900 ,350, 100, 50),
        Platform(950 ,200, 50, 50),
        Platform(950, 700, 50, 50),
        Platform(700, 750, 300, 50),
        Platform(800, 520, 50, 50),
        Platform(850, 520, 50, 25),
        
        # 垂直平台
        Platform(160, 750, 50, 150),
        Platform(450, 530, 50, 170),
        Platform(500, 350, 50, 200),
        Platform(1000, 150, 50, 250),
        Platform(1000, 650, 50, 100),
        
    ]
    fakeplatforms = [
        FakePlatform(800,350,100,50)
    ]


    spikes = [
        # 动态尖刺
        MovingSpike(1000 ,300, 40, 50, "left"),
        MovingSpike(160 ,705, 50, 50, "up"),
        # 墙上的尖刺
        MovingSpike(210, 800, 50, 50, "right"),
    ]

    static_spikes = [
        # 天花板尖刺
        StaticSpike(330, 95, 50, 50, "down"),
        
        # 平台上的尖刺
        
        StaticSpike(300 ,705, 50, 50, "up"),

        StaticSpike(450, 350, 50, 50, "left"),
        StaticSpike(200 ,315, 50, 50, "up"),
        StaticSpike(250 ,315, 50, 50, "up"),
        StaticSpike(225 ,315, 50, 50, "down"),
        StaticSpike(225 ,265, 50, 50, "up"),

        StaticSpike(600 ,270, 50, 50, "up"),
        StaticSpike(750 ,300, 50, 50, "up"),
        
        #StaticSpike(900 ,300, 40, 50, "up"),
        #StaticSpike(960 ,300, 40, 50, "left"),
        StaticSpike(1000,110, 50, 40, "up"),
        StaticSpike(1050,200, 30, 50, "right"),
        StaticSpike(950 ,400, 50, 50, "down"),
        StaticSpike(1100,550, 50, 50, "up"),
        StaticSpike(1100,600, 50, 50, "down"),
        StaticSpike(850, 700, 50, 50,"up"),
        StaticSpike(800, 570, 50, 50,"down"),
        StaticSpike(800, 470, 50, 50,"up"),
        StaticSpike(850, 470, 50, 50,"up"),
    ]

    checkpoints = [
        Checkpoint(450, 500),
        Checkpoint(0,370),
        Checkpoint(670, 320),
        Checkpoint(1000, 600)
    ]
    coins = [Coin(225, 630),Coin(900, 720),Coin(1030,420),Coin(375, 330),Coin(750,250)]
    goal = Goal(700, 705, 45, 45)

    bullets = []

    return platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms
# 创建BOSS关卡
def create_boss_level():
    """创建BOSS关卡"""
    platforms = [
        # 地面
        Platform(0, 825, 1200, 75),
        
        # 战斗平台
        Platform(200, 750, 150, 20),
        Platform(500, 650, 200, 20),
        Platform(850, 700, 150, 20),
        
        # 高处平台
        Platform(300, 500, 100, 20),
        Platform(600, 450, 200, 20),
        
    ]

    spikes = [
        # 地面尖刺
     
    ]

    static_spikes = [
        # 墙上的尖刺
 
    ]

    fakeplatforms=[

    ]

    checkpoints = [
    ]

    # 创建BOSS
    boss = Boss(600, 600)
    
    # 添加一些金币作为奖励
    coins = [

    ]
    bullets = []

    # 胜利区域（击败BOSS后到达）
    goal = Goal(SCREEN_WIDTH - 45, 50, 45, 45)

    return platforms, spikes, static_spikes, checkpoints, goal, coins, boss, bullets, fakeplatforms

def create_random_level():
    """随机生成关卡，包含随机分布的平台、尖刺、存档点和终点"""
    platforms = []
    spikes = []
    static_spikes = []
    checkpoints = []
    fakeplatforms=[]

    # 生成基础地面
    platforms.append(Platform(0, 825, 1200, 75))

    # 随机生成平台（增加重叠检测）
    for i in range(15):  # 生成15个随机平台
        attempts = 0
        while attempts < 100:  # 限制尝试次数防止无限循环
            x = random.randint(50, 1100)
            # 修改y值生成范围，从下往上生成
            y = random.randint(200, 750)  # 原来是100-750
            width = random.choice([80, 120, 160])
            height = random.choice([20, 30])
            new_platform = Platform(x, y, width, height)

            # 检查是否与现有平台重叠
            overlap = False
            for p in platforms:
                # 平台碰撞检测
                if (new_platform.x < p.x + p.width and
                    new_platform.x + new_platform.width > p.x and
                    new_platform.y < p.y + p.height and
                    new_platform.y + new_platform.height > p.y):
                    overlap = True
                    break

            if not overlap:
                platforms.append(new_platform)
                
                # 新增：如果平台较高，在其附近生成一个辅助平台
                '''if y <= 300:  # 当平台高度小于等于300时，生成辅助平台
                    helper_platform_attempts = 0
                    while helper_platform_attempts < 10:  # 尝试生成辅助平台
                        helper_x = new_platform.x + random.randint(-50, 50)
                        helper_y = new_platform.y + random.randint(50, 80)
                        helper_width = random.choice([80, 120])
                        helper_height = random.choice([20, 30])
                        helper_platform = Platform(helper_x, helper_y, helper_width, helper_height)
                        
                        # 检查是否与现有平台重叠
                        helper_overlap = False
                        for p in platforms:
                            if (helper_platform.x < p.x + p.width and
                                helper_platform.x + helper_platform.width > p.x and
                                helper_platform.y < p.y + p.height and
                                helper_platform.y + helper_platform.height > p.y):
                                helper_overlap = True
                                break
                        
                        if not helper_overlap:
                            platforms.append(helper_platform)
                            break
                        helper_platform_attempts += 1'''
                
                break
            attempts += 1
    
    # 随机生成尖刺（避开出生区域且增加密度）
    for platform in platforms[1:]:  # 不在地面上生成动态尖刺
        # 新增：排除左下角区域（x<200且y>600）
        if platform.x < 200 and platform.y > 600:
            continue
            
        # 将生成概率从30%提升到50%
        if random.random() > 0.7:  # 降低尖刺密度
            # 确保尖刺生成位置不在出生区域（x<200）
            if platform.x > 200:
                spike_x = random.randint(platform.x, platform.x + platform.width - 30)
                direction = "up"  # 固定朝上
                # 添加碰撞检测防止尖刺重叠
                overlap = False
                for s in spikes + static_spikes:
                    if (spike_x < s.x + s.width and
                        spike_x + 30 > s.x and
                        platform.y - 30 < s.y + s.height and
                        platform.y > s.y):
                        overlap = True
                        break
                if not overlap:
                    spikes.append(MovingSpike(spike_x, platform.y - 30, 30, 30, direction))
    
    # 生成更多静态尖刺（从3个增加到5个）
    for _ in range(3):  # 减少静态尖刺数量
        attempts = 0
        while attempts < 100:
            x = random.randint(50, 1150)
            y = random.randint(700, 800)  # 调整y范围避开出生点
            direction = "up"  # 固定朝上
            
            # 新增：检查是否在左下角区域（x<200且y>600）
            if x < 200 and y > 600:
                attempts += 1
                continue
                
            # 检查是否与出生区域冲突（x<200, y在400-600）
            if x < 200 and 400 < y < 600:
                attempts += 1
                continue
                
            # 检查是否与平台重叠
            on_platform = False
            for p in platforms:
                if (x < p.x + p.width and
                    x + 30 > p.x and
                    y < p.y + p.height and
                    y + 30 > p.y):
                    on_platform = True
                    break
            
            # 检查是否与其他尖刺重叠
            overlap = False
            for s in spikes + static_spikes:
                if (x < s.x + s.width and
                    x + 30 > s.x and
                    y < s.y + s.height and
                    y + 30 > s.y):
                    overlap = True
                    break
            
            if on_platform and not overlap:
                static_spikes.append(StaticSpike(x, y, 30, 30, direction))
                break
            attempts += 1
    
    # 随机生成存档点（确保在平台上且不与尖刺重合）
    for _ in range(1):  # 修改为只生成1个存档点
        attempts = 0
        while attempts < 100:
            if len(platforms[1:]) == 0:  # 添加平台列表非空检查
                break  # 如果没有可选平台，跳过生成
                
            platform = random.choice(platforms[1:])  # 选择非地面平台
            checkpoint_x = random.randint(platform.x, platform.x + platform.width - 30)
            new_checkpoint = Checkpoint(checkpoint_x, platform.y - 30)
            
            # 检查是否与其他存档点重叠
            overlap = False
            for cp in checkpoints:
                if (new_checkpoint.x < cp.x + cp.width and
                    new_checkpoint.x + cp.width > cp.x):
                    overlap = True
                    break
            
            # 检查与尖刺的重叠
            if not overlap:
                for spike in spikes + static_spikes:
                    if (new_checkpoint.x < spike.x + spike.width and
                        new_checkpoint.x + new_checkpoint.width > spike.x and
                        new_checkpoint.y < spike.y + spike.height and
                        new_checkpoint.y + new_checkpoint.height > spike.y):
                        overlap = True
                        break
            
            if not overlap:
                checkpoints.append(new_checkpoint)
                break
            attempts += 1
    
    # 生成终点（确保在最高平台）
    if len(platforms[1:]) > 0:  # 添加非空检查
        highest_platform = max(platforms[1:], key=lambda p: p.y)  # 找到最高平台
    else:
        highest_platform = platforms[0]  # 默认使用地面
    goal = Goal(SCREEN_WIDTH - 600, 150, 45, 45)  # 放置在右上角
    
    # 初始化金币列表（空列表）
    coins = []
    bullets = []
    
    return platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms


# 创建游戏对象
platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level()
player = Player(50, 500)
game_state = "playing"  # "playing", "win"
font = pygame.font.SysFont(None, 36)
collected_coins = 0  # 新增金币计数器
start_ticks = pygame.time.get_ticks()  # 新增开始时间戳




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
    fakeplatforms=[]

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
    goal = Goal(800, 350, 45, 45)  # 使用黄色方形区域表示通关位置
    
    # 创建教学文本，使用更小的字体并移除箭头指示
    tutorial_texts = [
        {"text": "← → 键：左右移动", "pos": (200, 750)},
        {"text": "↑ 键：跳跃", "pos": (250, 600)},
        {"text": "↑ 键：二段跳（在空中再次按下跳跃）", "pos": (450, 450)},
        {"text": "空格键：射击", "pos": (900, 550)},
        {"text": "必须收集满5个硬币才能过关", "pos": (100, 100)},
        {"text": "ESC键返回关卡选择", "pos": (100, 130)},
        {"text": "传送门是通关位置", "pos": (800, 320)},
        {"text": "这个尖刺会向上弹起", "pos": (900, 720)},
        {"text": "按k可以紫砂", "pos": (700, 120)}
        
    ]
    
    return platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,fakeplatforms

# 游戏主循环前展示关卡选择界面
selected_level = show_level_selection()
if selected_level is None:
    pygame.quit()
    sys.exit()

# 根据选择的关卡创建不同地图
if selected_level == "tutorial":
    # 新手教程关卡
    platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,fakeplatforms = create_tutorial_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
elif selected_level == "level1":
    # 关卡1
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
elif selected_level == "level2":  # 新增：处理关卡2
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level2()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
elif selected_level == "boss":
    platforms, spikes, static_spikes, checkpoints, goal, coins, boss, bullets,fakeplatforms= create_boss_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()
    boss_defeated = False
else:  # 处理随机生成的关卡
    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_random_level()
    player = Player(50, 600)
    game_state = "playing"
    start_ticks = pygame.time.get_ticks()



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
            elif event.key == pygame.K_SPACE and player.alive and game_state != "win":
                # 向当前方向发射一颗子弹
                player.shoot()
                bullets.append(Bullet(player.x + player.width//2, player.y + player.height//2, player.direction))
            elif event.key == pygame.K_k:
                if selected_level == "random":  # 处理随机关卡重置
                    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_random_level()
                    player = Player(50, 600)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                else:  # 处理普通关卡重置
                    player.die()
                
            elif event.key == pygame.K_ESCAPE:
                if platforms:  # 如果列表非空，才进行删除
                    platforms.clear()

                # 删除尖刺实例
                if spikes:
                    spikes.clear()

                # 删除静态尖刺实例
                if static_spikes:
                    static_spikes.clear()

                # 删除存档点实例
                if checkpoints:
                    checkpoints.clear()

                # 删除金币实例
                if coins:
                    coins.clear()

                # 删除子弹实例
                if bullets:
                    bullets.clear()

                # 删除假平台实例
                if fakeplatforms:
                    fakeplatforms.clear()
                
                if goal:
                    del goal

                # 修改为返回关卡选择界面
                selected_level = None
                running = False
                next_level = show_level_selection()
                if next_level is not None:
                    selected_level = next_level
                    # 重新初始化游戏
                    if selected_level == "tutorial":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,fakeplatforms= create_tutorial_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level1":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms= create_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "level2":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level2()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "random":  # 处理随机关卡返回
                        platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_random_level()
                        player = Player(50, 600)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    elif selected_level == "boss":
                        platforms, spikes, static_spikes, checkpoints, goal, coins, boss, bullets,fakeplatforms = create_boss_level()
                        player = Player(50, 500)
                        game_state = "playing"
                        start_ticks = pygame.time.get_ticks()
                    running = True  # 重新开始游戏循环
   
    # 玩家控制 - 现在完全封装在Player类中
    if player.alive and game_state == "playing":
        player.update_controls()  # 处理键盘输入
        player.update_position(platforms)  # 更新位置和碰撞检测
    for fakePlatform in fakeplatforms:
        fakePlatform.update_alpha(player)

    # 更新游戏状态
    if player.alive and game_state == "playing":
        # 检查尖刺碰撞及触发
        for spike in spikes:
            spike.trigger_spike(player)
            # 检查玩家与尖刺的碰撞
            if spike.check_collision(player):
                player.die()
            spike.update()
        for static_spike in static_spikes:
            if static_spike.check_collision(player):
                player.die()
        # 检查存档点碰撞
        for checkpoint in checkpoints:
            if checkpoint.check_collision(player):
                checkpoint.activate(player)
        
        
        if selected_level == "boss":
            boss.update(player)
            Player.update_bullets(player)
        
            # 检查玩家子弹与BOSS的碰撞
            for bullet in player.bullets[:]:
                if bullet.check_collision(boss):
                    player.bullets.remove(bullet)
                    if boss.take_damage():
                        boss.health -= 1
                        boss_defeated = True
                        game_state = "win"
                        show_game_win_screen()
        
            # 检查BOSS子弹与玩家的碰撞
            for bullet in boss.bullets[:]:
                if bullet.check_collision(player):
                    player.die()
                    boss.bullets.remove(bullet) 

        # 检查金币碰撞
        for coin in coins[:]:  # 使用切片复制列表以避免在迭代时修改列表
            if coin.check_collision(player):
                coin.collected = True
                collected_coins += 1
                coins.remove(coin)  # 从列表中移除金币
    if player.check_collision(goal) and collected_coins>=5:
        game_state = "win"
        collected_coins = 0

        # 通关后解锁下一关
        if selected_level == "tutorial" and not unlocked_levels["level1"]:
            unlocked_levels["level1"] = True
            # 自动进入第一关
            selected_level = "level1"
        elif selected_level == "level1" and not unlocked_levels["level2"]:
            unlocked_levels["level2"] = True
            # 自动进入第二关
            selected_level = "level2"
        elif selected_level == "level2" and not unlocked_levels["boss"]:
            unlocked_levels["boss"] = True
            selected_level = "boss"
        else:
            # 如果已经是最后一关，返回关卡选择界面
            selected_level = None
    
        # 重新初始化游戏
        running = False  # 结束当前游戏循环
        if selected_level is not None:
            if selected_level == "tutorial":
                platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts ,fakeplatforms= create_tutorial_level()
                player = Player(50, 500)
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()
            elif selected_level == "level1":
                platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms= create_level()
                player = Player(50, 500)
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()
            elif selected_level == "level2":
                platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level2()
                player = Player(50, 500)
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()
            elif selected_level == "boss":
                platforms, spikes, static_spikes, checkpoints, goal, coins, boss, bullets,fakeplatforms = create_boss_level()
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
                    platforms, spikes, static_spikes, checkpoints, goal, coins, tutorial_texts,fakeplatforms= create_tutorial_level()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                elif selected_level == "level1":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms= create_level()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                elif selected_level == "level2":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, bullets,fakeplatforms = create_level2()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                elif selected_level == "boss":
                    platforms, spikes, static_spikes, checkpoints, goal, coins, boss, bullets,fakeplatforms = create_boss_level()
                    player = Player(50, 500)
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                running = True  # 重新开始游戏循环"""

        # 检查目标碰撞

        # 新增：更新子弹
    for bullet in bullets[:]:
        bullet.update()
        if not bullet.active:
            bullets.remove(bullet)

    # 玩家死亡处理
    if not player.alive:
        for spike in spikes:
                spike.reset()   
        
        if selected_level == "boss":
            boss.x, boss.y = 600, 600  # 重置位置
            boss.health = boss.max_health  # 重置血量
            boss.bullets.clear()  # 清空子弹
            boss.direction = 1  # 重置方向
            boss.vel_x, boss.vel_y = 2, 2  # 重置速度
            boss.move_pattern = 0
            boss.attack_pattern = 0
            boss.pattern_timer = 0
            boss.attack_timer = 0
        show_game_over_screen()
        
        bullets.clear()
        player.bullets.clear()
        if selected_level == "boss":
            boss.bullets.clear()

        player.alive = True
        player.respawn()      
        
            

    # 绘制游戏
    screen.fill((30, 30, 50))  # 深蓝色背景

    # 绘制背景图片（添加了自适应屏幕尺寸的功能）
    scaled_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_background, (0, 0))  # 在(0,0)位置绘制缩放后的背景图片
    
    # 绘制游戏对象
    for platform in platforms:
        platform.draw(screen)

    goal.draw(screen)

  

    for spike in spikes:
        spike.draw(screen)

    for static_spike in static_spikes:
        static_spike.draw(screen)
    for fakeplatform in fakeplatforms:
        fakeplatform.draw(screen)
    for checkpoint in checkpoints:
        checkpoint.draw(screen)

    if selected_level == "boss" :
        boss.draw(screen)



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


    # 绘制UI
    death_text = pygame.font.SysFont("SimHei", 24).render(f"死亡数: {player.death_count}  硬币: {collected_coins}/5", True, WHITE)
    screen.blit(death_text, (10, 10))
    
    # 新增计时器逻辑
    current_time = pygame.time.get_ticks() - start_ticks
    timer_text = pygame.font.SysFont("SimHei", 18).render(f"游戏时间: {current_time // 1000}秒", True, WHITE)
    screen.blit(timer_text, (10, 40))  # 在左上角绘制计时器
    
    if game_state == "win":
        win_text = pygame.font.SysFont("SimHei", 24).render("恭喜通关! 按 esc 返回开始界面", True, YELLOW)
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

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()