import pygame
import random
import math

# 初始化 Pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("烟花动画")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

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

# 主程序
def main():
    clock = pygame.time.Clock()
    fireworks = []

    # 设置背景颜色
    screen.fill(BLACK)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 每隔一段时间发射烟花
        if random.random() < 0.02:
            firework = Firework(random.randint(100, 700), random.randint(100, 400), random.choice([RED, GREEN, BLUE]))
            fireworks.append(firework)

        # 更新屏幕
        screen.fill(BLACK)
        
        for firework in fireworks:
            firework.update()
            firework.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
