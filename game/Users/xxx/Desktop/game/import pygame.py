
# 尖刺类
class Spike:
    def __init__(self, x, y, width=60, height=45, direction="up"):  # 修改尖刺的默认宽度和高度
        self.x = x
        self.y = y
        self.width = width  # 根据 spike.png 的实际宽度调整
        self.height = height  # 根据 spike.png 的实际高度调整
        self.direction = direction  # "up", "down", "left", "right"
        self.moving_up = False  # 新增标志表示尖刺是否正在向上移动
        self.speed_y = 0  # 尖刺的垂直速度
        self.original_y = y  # 记录初始位置
        self.image = spike_image  # 加载尖刺图片
        print(f"初始化尖刺: ({self.x}, {self.y}), moving_up={self.moving_up}")  # 添加调试信息
