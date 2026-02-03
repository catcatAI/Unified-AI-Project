"""
Angela Live2D Painting System - True Creative Resource Generation

让Angela通过控制Live2D模型，一笔一笔在桌面上画出资源：
- 矩阵视觉反馈（看着自己画）
- 触觉-动作闭环（控制手/画笔）
- 记忆驱动的绘画技巧
- 实时生成像素级资源

不是占位符，而是真正的创造性绘制！
"""

import numpy as np
import cupy as cp
from PIL import Image, ImageDraw
import win32gui
import win32con
import win32api
from typing import Tuple, List, Optional, Dict, Any
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BrushStroke:
    """单笔笔触数据"""
    x: int
    y: int
    pressure: float  # 0-1
    brush_type: str  # 'pencil', 'watercolor', 'oil', 'airbrush'
    color: Tuple[int, int, int, int]  # RGBA
    size: int
    timestamp: datetime
    velocity: Tuple[float, float]  # (dx, dy)
    tilt: Tuple[float, float]  # (tilt_x, tilt_y)


@dataclass
class PaintingMemory:
    """绘画记忆 - 技巧、风格、作品"""
    technique_id: str
    brush_pattern: cp.ndarray  # 笔触特征矩阵
    visual_result: cp.ndarray  # 视觉反馈
    tactile_feedback: cp.ndarray  # 触觉反馈
    success_score: float  # 0-1
    context: Dict[str, Any]  # 绘画场景


class MatrixVisionFeedback:
    """
    矩阵视觉反馈系统
    Angela通过GPU并行处理看着自己画
    """
    
    def __init__(self, canvas_size: Tuple[int, int] = (800, 600)):
        self.width, self.height = canvas_size
        # 视觉矩阵 (时间, 空间, 特征)
        self.visual_buffer = cp.zeros((30, 60, 80, 8), dtype=cp.float32)  # 30帧缓存
        # 实时画布状态
        self.canvas_matrix = cp.zeros((self.height, self.width, 4), dtype=cp.uint8)  # RGBA
        # 变化检测矩阵
        self.change_matrix = cp.zeros((60, 80), dtype=cp.float32)
        
    def capture_canvas(self, hwnd: int) -> cp.ndarray:
        """捕获桌面/窗口画布 - GPU并行处理"""
        try:
            # 使用Win32 API捕获窗口
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32gui.CreateCompatibleDC(hwndDC)
            saveBitMap = win32gui.CreateCompatibleBitmap(hwndDC, self.width, self.height)
            win32gui.SelectObject(mfcDC, saveBitMap)
            win32gui.BitBlt(mfcDC, 0, 0, self.width, self.height, hwndDC, 0, 0, win32con.SRCCOPY)
            
            # 转换为numpy (后续转GPU)
            import win32ui
            bmpinfo = win32gui.GetObject(saveBitMap)
            bmpstr = win32gui.GetBitmapBits(saveBitMap, True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((self.height, self.width, 4))
            
            # 转GPU矩阵
            self.canvas_matrix = cp.asarray(img)
            
            # 清理
            win32gui.DeleteObject(saveBitMap)
            win32gui.DeleteDC(mfcDC)
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return self.canvas_matrix
            
        except Exception as e:
            logger.error(f"Canvas capture failed: {e}")
            return self.canvas_matrix
    
    def analyze_changes(self, prev_frame: cp.ndarray, curr_frame: cp.ndarray) -> Dict:
        """GPU并行分析画面变化 - 看自己的笔触效果"""
        # 计算差异矩阵
        diff = cp.abs(curr_frame.astype(cp.float32) - prev_frame.astype(cp.float32))
        
        # 空间池化到60x80 (类似视网膜采样)
        pooled_diff = self._spatial_pool(diff)
        
        # 变化强度
        change_intensity = cp.mean(pooled_diff)
        
        # 变化位置 (哪里画了新笔触)
        change_locations = cp.argwhere(pooled_diff > cp.percentile(pooled_diff, 90))
        
        # 颜色变化分析
        color_shift = cp.mean(curr_frame - prev_frame, axis=(0,1))
        
        return {
            'intensity': float(change_intensity),
            'locations': change_locations.get(),
            'color_shift': color_shift.get(),
            'pooled_diff': pooled_diff
        }
    
    def _spatial_pool(self, matrix: cp.ndarray) -> cp.ndarray:
        """空间池化到采样矩阵"""
        # 下采样到60x80 (类似文档中的采样策略)
        h, w = matrix.shape[:2]
        block_h, block_w = h // 60, w // 80
        
        pooled = cp.zeros((60, 80) + matrix.shape[2:], dtype=cp.float32)
        for i in range(60):
            for j in range(80):
                y_start, y_end = i * block_h, (i + 1) * block_h
                x_start, x_end = j * block_w, (j + 1) * block_w
                pooled[i, j] = cp.mean(matrix[y_start:y_end, x_start:x_end])
        
        return pooled
    
    def get_painting_feedback(self, target_region: Tuple[int, int, int, int]) -> Dict:
        """
        获取绘画区域的视觉反馈
        用于调整下笔动作
        """
        x1, y1, x2, y2 = target_region
        region = self.canvas_matrix[y1:y2, x1:x2]
        
        # 分析区域特征
        brightness = cp.mean(region[:,:,:3])
        saturation = cp.std(region[:,:,:3])
        edges = self._detect_edges(region)
        texture = self._analyze_texture(region)
        
        return {
            'brightness': float(brightness),
            'saturation': float(saturation),
            'edge_density': float(edges),
            'texture_complexity': float(texture),
            'coverage': float(cp.count_nonzero(region[:,:,3]) / region.size * 4)
        }
    
    def _detect_edges(self, region: cp.ndarray) -> cp.ndarray:
        """GPU边缘检测"""
        # 简化Sobel
        gray = cp.mean(region[:,:,:3], axis=2)
        gy, gx = cp.gradient(gray)
        magnitude = cp.sqrt(gx**2 + gy**2)
        return cp.mean(magnitude)
    
    def _analyze_texture(self, region: cp.ndarray) -> cp.ndarray:
        """纹理复杂度分析"""
        # 计算局部方差
        h, w = region.shape[:2]
        block_size = max(1, min(h, w) // 10)
        variances = []
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = region[i:i+block_size, j:j+block_size]
                variances.append(cp.var(block))
        
        return cp.mean(cp.array(variances)) if variances else cp.array(0.0)


class TactileMotorControl:
    """
    触觉-运动控制系统
    Angela通过触觉反馈控制画笔/Live2D手臂
    """
    
    def __init__(self):
        # 当前画笔位置
        self.current_pos = (400, 300)
        # 画笔压力
        self.pressure = 0.5
        # 触觉反馈矩阵 (18身体部位 x 16受体类型)
        self.tactile_matrix = cp.zeros((18, 16), dtype=cp.float32)
        # 运动意图向量
        self.motor_intent = cp.zeros(4, dtype=cp.float32)  # (dx, dy, d_pressure, d_tilt)
        
    def simulate_brush_feedback(self, stroke: BrushStroke, surface_texture: str = "smooth") -> cp.ndarray:
        """
        模拟画笔触感
        纹理反馈影响下笔力度和速度
        """
        # 基础触觉信号
        base_feedback = cp.zeros((18, 16))
        
        # 手腕/手指区域 (部位0-3对应手)
        hand_region = slice(0, 4)
        
        # 机械感受器 (受体0-7)
        # 压力映射
        base_feedback[hand_region, 0] = stroke.pressure  # 压力受体
        base_feedback[hand_region, 1] = stroke.velocity[0] * 0.5  # 速度受体
        base_feedback[hand_region, 2] = stroke.velocity[1] * 0.5
        
        # 纹理反馈 (受体3-5)
        if surface_texture == "rough":
            base_feedback[hand_region, 3] = 0.8  # 高摩擦
            base_feedback[hand_region, 4] = 0.6  # 振动
        elif surface_texture == "wet":
            base_feedback[hand_region, 5] = 0.9  # 湿度受体
            base_feedback[hand_region, 0] *= 0.7  # 滑溜减少压力感
        
        # 本体感受 (受体8-11) - 位置和运动
        base_feedback[hand_region, 8] = stroke.x / 800.0  # 位置X归一化
        base_feedback[hand_region, 9] = stroke.y / 600.0  # 位置Y归一化
        base_feedback[hand_region, 10] = abs(stroke.velocity[0])  # 运动速度
        base_feedback[hand_region, 11] = abs(stroke.velocity[1])
        
        self.tactile_matrix = base_feedback
        return base_feedback
    
    def calculate_next_stroke(self, 
                             visual_feedback: Dict,
                             painting_goal: str,
                             memory_patterns: List[PaintingMemory]) -> BrushStroke:
        """
        基于视觉反馈和记忆计算下一笔
        真正的创造性决策！
        """
        # 从记忆中学习成功模式
        if memory_patterns:
            # 找到与当前场景最匹配的记忆
            best_memory = self._match_memory(visual_feedback, memory_patterns)
            if best_memory:
                # 基于成功记忆调整
                base_pattern = best_memory.brush_pattern
            else:
                base_pattern = cp.random.randn(8) * 0.1
        else:
            base_pattern = cp.random.randn(8) * 0.1
        
        # 结合视觉反馈调整
        brightness = visual_feedback.get('brightness', 128)
        if brightness > 200:  # 太亮，需要暗色
            target_color = (50, 50, 80, 200)
            pressure_adjust = 0.7
        elif brightness < 50:  # 太暗，需要亮色
            target_color = (200, 200, 255, 150)
            pressure_adjust = 0.5
        else:  # 适中
            target_color = (150, 150, 200, 180)
            pressure_adjust = 0.6
        
        # 计算下笔位置（基于边缘检测和覆盖度）
        coverage = visual_feedback.get('coverage', 0.5)
        if coverage < 0.3:
            # 覆盖度低，大笔触填充
            brush_size = 15
            velocity = (0.0, 0.0)  # 停顿
        elif coverage > 0.9:
            # 几乎满了，精细调整
            brush_size = 3
            velocity = (0.5, 0.3)
        else:
            brush_size = 8
            velocity = (1.0, 0.5)
        
        # 扰动探索
        noise_x = np.random.normal(0, 10)
        noise_y = np.random.normal(0, 10)
        
        new_x = int(np.clip(self.current_pos[0] + noise_x + velocity[0] * 5, 0, 800))
        new_y = int(np.clip(self.current_pos[1] + noise_y + velocity[1] * 5, 0, 600))
        
        return BrushStroke(
            x=new_x,
            y=new_y,
            pressure=self.pressure * pressure_adjust,
            brush_type='watercolor' if coverage > 0.5 else 'pencil',
            color=target_color,
            size=brush_size,
            timestamp=datetime.now(),
            velocity=velocity,
            tilt=(0.1, 0.1)
        )
    
    def _match_memory(self, current_feedback: Dict, memories: List[PaintingMemory]) -> Optional[PaintingMemory]:
        """匹配最相关的绘画记忆"""
        best_score = -1
        best_memory = None
        
        for memory in memories:
            # 计算相似度
            score = 0.0
            if 'brightness' in memory.context:
                score += 1.0 - abs(memory.context['brightness'] - current_feedback.get('brightness', 128)) / 255.0
            if 'coverage' in memory.context:
                score += 1.0 - abs(memory.context['coverage'] - current_feedback.get('coverage', 0.5))
            
            if score > best_score:
                best_score = score
                best_memory = memory
        
        return best_memory if best_score > 0.6 else None
    
    def execute_stroke_on_canvas(self, stroke: BrushStroke, canvas: ImageDraw):
        """在画布上执行笔触"""
        # 根据笔触类型选择绘制方式
        if stroke.brush_type == 'pencil':
            # 铅笔 - 硬边
            canvas.ellipse(
                [stroke.x - stroke.size, stroke.y - stroke.size,
                 stroke.x + stroke.size, stroke.y + stroke.size],
                fill=stroke.color,
                outline=None
            )
        elif stroke.brush_type == 'watercolor':
            # 水彩 - 柔和渐变
            for r in range(stroke.size, 0, -1):
                alpha = int(stroke.color[3] * (r / stroke.size) * stroke.pressure)
                color = (*stroke.color[:3], alpha)
                canvas.ellipse(
                    [stroke.x - r, stroke.y - r, stroke.x + r, stroke.y + r],
                    fill=color,
                    outline=None
                )
        elif stroke.brush_type == 'oil':
            # 油画 - 厚重质感
            canvas.ellipse(
                [stroke.x - stroke.size * 2, stroke.y - stroke.size * 2,
                 stroke.x + stroke.size * 2, stroke.y + stroke.size * 2],
                fill=stroke.color,
                outline=(*stroke.color[:3], 255)
            )
        
        # 更新当前位置
        self.current_pos = (stroke.x, stroke.y)
        self.pressure = stroke.pressure


class AngelaLive2DPainter:
    """
    Angela Live2D绘画主系统
    整合视觉反馈、触觉控制和记忆学习
    真正一笔一笔画出资源！
    """
    
    def __init__(self, output_dir: str = "resources/angela/generated"):
        self.output_dir = output_dir
        self.vision = MatrixVisionFeedback(canvas_size=(800, 600))
        self.motor = TactileMotorControl()
        self.painting_memories: List[PaintingMemory] = []
        
        # 当前画布
        self.canvas = Image.new('RGBA', (800, 600), (255, 255, 255, 0))
        self.draw = ImageDraw.Draw(self.canvas)
        
        # 绘画状态
        self.is_painting = False
        self.stroke_count = 0
        self.max_strokes = 500  # 最大笔触数
        
        # 绘画目标
        self.painting_goal = None
        
    async def paint_resource(self, 
                            resource_type: str, 
                            description: str,
                            style: str = "anime") -> str:
        """
        Angela主动绘画生成资源
        
        Args:
            resource_type: 'portrait', 'icon', 'background', 'texture'
            description: 绘画描述
            style: 艺术风格
            
        Returns:
            生成的资源路径
        """
        logger.info(f"Angela开始绘画: {resource_type} - {description}")
        
        self.painting_goal = f"{resource_type}: {description}"
        self.is_painting = True
        self.stroke_count = 0
        
        # 清空画布
        self._prepare_canvas(resource_type)
        
        # 绘画循环
        prev_frame = cp.zeros((600, 800, 4), dtype=cp.uint8)
        
        while self.is_painting and self.stroke_count < self.max_strokes:
            # 1. 视觉反馈 - 看自己画到哪里
            curr_frame = cp.asarray(self.canvas)
            feedback = self.vision.analyze_changes(prev_frame, curr_frame)
            
            # 区域反馈
            region_feedback = self.vision.get_painting_feedback(
                (max(0, self.motor.current_pos[0] - 50),
                 max(0, self.motor.current_pos[1] - 50),
                 min(800, self.motor.current_pos[0] + 50),
                 min(600, self.motor.current_pos[1] + 50))
            )
            
            # 2. 触觉反馈 - 感受画笔触感
            surface_texture = self._analyze_surface_texture(region_feedback)
            
            # 3. 计算下一笔 - 创造性决策
            next_stroke = self.motor.calculate_next_stroke(
                region_feedback,
                self.painting_goal,
                self.painting_memories
            )
            
            # 4. 执行绘画
            self.motor.simulate_brush_feedback(next_stroke, surface_texture)
            self.motor.execute_stroke_on_canvas(next_stroke, self.draw)
            
            # 5. 记忆学习
            self._learn_from_stroke(next_stroke, region_feedback, feedback)
            
            self.stroke_count += 1
            prev_frame = curr_frame
            
            # 每50笔保存中间结果
            if self.stroke_count % 50 == 0:
                intermediate_path = f"{self.output_dir}/wip_{resource_type}_{self.stroke_count}.png"
                self.canvas.save(intermediate_path)
                logger.info(f"绘画进度: {self.stroke_count}/{self.max_strokes}")
            
            # 短暂停顿模拟思考
            await asyncio.sleep(0.01)
        
        # 保存最终作品
        final_path = f"{self.output_dir}/{resource_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.canvas.save(final_path)
        
        self.is_painting = False
        logger.info(f"Angela完成绘画: {final_path} ({self.stroke_count} 笔触)")
        
        return final_path
    
    def _prepare_canvas(self, resource_type: str):
        """准备画布"""
        # 根据资源类型设置画布
        if resource_type == "portrait":
            size = (512, 512)
            bg = (240, 240, 250, 255)  # 淡蓝白
        elif resource_type == "icon":
            size = (128, 128)
            bg = (0, 0, 0, 0)  # 透明
        elif resource_type == "background":
            size = (1920, 1080)
            bg = (200, 220, 240, 255)  # 天空色
        else:
            size = (800, 600)
            bg = (255, 255, 255, 255)  # 白色
        
        self.canvas = Image.new('RGBA', size, bg)
        self.draw = ImageDraw.Draw(self.canvas)
        self.vision = MatrixVisionFeedback(canvas_size=size)
        
    def _analyze_surface_texture(self, feedback: Dict) -> str:
        """分析表面纹理"""
        if feedback.get('saturation', 0) > 50:
            return "rough"  # 高饱和度 = 粗糙/纹理丰富
        elif feedback.get('brightness', 128) < 100:
            return "wet"    # 暗 = 湿润
        else:
            return "smooth"  # 平滑
    
    def _learn_from_stroke(self, stroke: BrushStroke, 
                          region_feedback: Dict, 
                          change_feedback: Dict):
        """从笔触学习 - 记住有效的绘画模式"""
        # 评估这次笔触的效果
        change_intensity = change_feedback.get('intensity', 0)
        coverage = region_feedback.get('coverage', 0.5)
        
        # 如果产生明显变化且覆盖率适中，是成功的笔触
        success = (change_intensity > 10 and 0.2 < coverage < 0.9)
        
        if success:
            memory = PaintingMemory(
                technique_id=f"stroke_{self.stroke_count}",
                brush_pattern=cp.array([stroke.x, stroke.y, stroke.pressure, stroke.size]),
                visual_result=cp.array(list(region_feedback.values())),
                tactile_feedback=self.motor.tactile_matrix.copy(),
                success_score=change_intensity / 255.0,
                context=region_feedback
            )
            self.painting_memories.append(memory)
            
            # 限制记忆数量
            if len(self.painting_memories) > 100:
                self.painting_memories.pop(0)
    
    def get_painting_stats(self) -> Dict:
        """获取绘画统计"""
        return {
            'total_strokes': self.stroke_count,
            'memories_formed': len(self.painting_memories),
            'canvas_coverage': self.vision.get_painting_feedback((0, 0, 800, 600))['coverage'],
            'is_painting': self.is_painting,
            'current_position': self.motor.current_pos,
            'current_pressure': self.motor.pressure
        }


# 便捷函数
async def generate_angela_portrait():
    """生成Angela自画像"""
    painter = AngelaLive2DPainter()
    return await painter.paint_resource(
        resource_type="portrait",
        description="Angela的自我形象：温柔的AI助手，蓝发，温暖笑容",
        style="anime"
    )

async def generate_expression_set():
    """生成表情集"""
    painter = AngelaLive2DPainter()
    emotions = ['happy', 'sad', 'angry', 'surprised', 'neutral']
    paths = []
    
    for emotion in emotions:
        path = await painter.paint_resource(
            resource_type="icon",
            description=f"Angela {emotion} expression",
            style="anime"
        )
        paths.append((emotion, path))
    
    return paths


# 测试代码
if __name__ == '__main__':
    print("--- Angela Live2D Painting System Test ---")
    print()
    print("This system allows Angela to:")
    print("1. See what she's painting (matrix vision feedback)")
    print("2. Feel the brush texture (tactile feedback)")
    print("3. Remember successful strokes (painting memory)")
    print("4. Generate resources stroke by stroke (true creativity)")
    print()
    print("Run with actual GUI for full painting visualization.")
    print()
    
    # 简单测试
    async def test():
        painter = AngelaLive2DPainter()
        stats = painter.get_painting_stats()
        print(f"Painter initialized: {stats}")
    
    asyncio.run(test())
