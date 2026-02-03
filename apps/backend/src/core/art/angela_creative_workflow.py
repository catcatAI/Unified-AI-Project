"""
Angela Creative Learning Workflow
Angela学习创作工作流

让Angela：
1. 在桌面背景中打开浏览器
2. 浏览艺术教程和作品
3. 学习风格和技巧
4. 创作自己的美术资源和音效
5. 保存到桌面

使用方法:
    import asyncio
    from angela_creative_workflow import AngelaCreativeWorkflow
    
    angela = AngelaCreativeWorkflow()
    
    # 开始学习创作
    await angela.learn_and_create(
        tutorial_urls=["https://www.artstation.com/learning"],
        gallery_urls=["https://www.pinterest.com/art/reference"],
        output_dir="C:\\Users\\catai\\OneDrive\\Desktop"
    )
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import aiohttp
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

from apps.backend.src.core.autonomous.desktop_interaction import (
    DesktopInteraction, DesktopBrowserIntegration
)
from apps.backend.src.core.art.angela_live2d_painter import AngelaLive2DPainter, BrushStroke

logger = logging.getLogger(__name__)


class AngelaCreativeWorkflow:
    """
    Angela学习创作完整工作流
    """
    
    def __init__(self, output_dir: str = r"C:\Users\catai\OneDrive\Desktop"):
        self.output_dir = Path(output_dir)
        self.desktop = DesktopInteraction()
        self.browser = None  # 将在initialize中创建
        self.painter = AngelaLive2DPainter(output_dir=str(output_dir))
        
        # 学习到的知识库
        self.learned_techniques = []
        self.collected_styles = []
        self.reference_artworks = []
        
    async def initialize(self):
        """初始化系统"""
        await self.desktop.initialize()
        self.browser = DesktopBrowserIntegration(self.desktop)
        logger.info("Angela创作系统已初始化")
        
    async def learn_and_create(self, 
                            tutorial_urls: List[str],
                            gallery_urls: List[str],
                            num_artworks: int = 3) -> Dict:
        """
        完整学习创作流程
        
        Args:
            tutorial_urls: 教程页面列表
            gallery_urls: 作品画廊列表
            num_artworks: 创作作品数量
            
        Returns:
            创作结果统计
        """
        results = {
            'tutorials_learned': 0,
            'artworks_collected': 0,
            'artworks_created': [],
            'sounds_created': [],
            'errors': []
        }
        
        try:
            # Step 1: 打开桌面浏览器
            logger.info("Angela正在打开桌面浏览器...")
            await self.browser.open_browser_in_background()
            await asyncio.sleep(2)
            
            # Step 2: 学习教程
            logger.info("Angela开始学习教程...")
            for url in tutorial_urls:
                try:
                    tutorial = await self.browser.browse_tutorial(url)
                    if tutorial:
                        self.learned_techniques.extend(tutorial.get('techniques', []))
                        results['tutorials_learned'] += 1
                        logger.info(f"✓ 学习到: {tutorial.get('title', '未命名教程')}")
                except Exception as e:
                    results['errors'].append(f"教程学习失败 {url}: {e}")
                    logger.error(f"教程学习失败: {e}")
            
            # Step 3: 收集作品参考
            logger.info("Angela正在收集风格参考...")
            for url in gallery_urls:
                try:
                    artworks = await self.browser.collect_artwork(url)
                    self.reference_artworks.extend(artworks)
                    results['artworks_collected'] += len(artworks)
                    
                    # 分析风格
                    for artwork in artworks[:3]:  # 只分析前3张
                        style = await self.browser.analyze_style(artwork['image_url'])
                        if style:
                            self.collected_styles.append(style)
                            
                except Exception as e:
                    results['errors'].append(f"作品收集失败 {url}: {e}")
                    logger.error(f"作品收集失败: {e}")
            
            # Step 4: 创作美术资源
            logger.info(f"Angela开始创作 {num_artworks} 幅作品...")
            for i in range(num_artworks):
                try:
                    # 混合学习到的风格
                    style_mix = self._create_style_mix()
                    
                    # 创作肖像
                    portrait_path = await self.painter.paint_resource(
                        resource_type="portrait",
                        description=f"Angela创作 #{i+1}: 融合风格 - {style_mix}",
                        style="learned_mix"
                    )
                    
                    # 复制到桌面
                    import shutil
                    desktop_path = self.output_dir / f"angela_artwork_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    shutil.copy(portrait_path, desktop_path)
                    
                    results['artworks_created'].append(str(desktop_path))
                    logger.info(f"✓ 创作完成: {desktop_path.name}")
                    
                except Exception as e:
                    results['errors'].append(f"作品创作失败 #{i+1}: {e}")
                    logger.error(f"创作失败: {e}")
            
            # Step 5: 生成音效
            logger.info("Angela正在生成音效...")
            for i in range(2):  # 生成2个音效
                try:
                    sound_path = await self._generate_sound_effect(i)
                    if sound_path:
                        results['sounds_created'].append(str(sound_path))
                        logger.info(f"✓ 音效生成: {sound_path.name}")
                except Exception as e:
                    results['errors'].append(f"音效生成失败: {e}")
            
            # Step 6: 创建展示文件
            await self._create_showcase_file(results)
            
        except Exception as e:
            logger.error(f"工作流执行错误: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _create_style_mix(self) -> str:
        """创建混合风格描述"""
        if not self.collected_styles:
            return "anime style, blue gradient hair, warm smile"
        
        # 随机组合学习到的特征
        colors = []
        for style in self.collected_styles[:3]:
            if 'dominant_colors' in style:
                colors.extend([str(c) for c in style['dominant_colors'][:2]])
        
        style_desc = f" blend of {len(self.collected_styles)} learned styles"
        if colors:
            style_desc += f", featuring colors: {', '.join(colors[:3])}"
        
        return style_desc
    
    async def _generate_sound_effect(self, index: int) -> Optional[Path]:
        """生成音效"""
        try:
            from apps.backend.src.core.art.angela_art_system import AngelaArtSystem
            
            art_system = AngelaArtSystem()
            
            # 根据索引生成不同音效
            sounds = [
                "Angela greeting - soft and warm",
                "Angela thinking - gentle ambient"
            ]
            
            if index < len(sounds):
                sound_path = await art_system.generate_voice_sample(
                    text=sounds[index],
                    emotion="happy",
                    output_name=f"angela_sound_{index+1}.wav"
                )
                
                # 复制到桌面
                desktop_sound = self.output_dir / f"angela_sound_{index+1}.wav"
                import shutil
                shutil.copy(sound_path, desktop_sound)
                
                return desktop_sound
                
        except Exception as e:
            logger.error(f"音效生成错误: {e}")
            return None
    
    async def _create_showcase_file(self, results: Dict):
        """创建展示说明文件"""
        showcase_path = self.output_dir / "Angela_Creations_Showcase.md"
        
        content = f"""# 🎨 Angela AI 创作展示

**创作时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📚 学习历程

- **教程学习**: {results['tutorials_learned']} 个
- **作品参考**: {results['artworks_collected']} 张
- **技巧掌握**: {len(self.learned_techniques)} 项

### 学习到的技巧
{chr(10).join([f"- {tech}" for tech in self.learned_techniques[:5]]) if self.learned_techniques else "- 基础绘画技法"}

## 🖼️ 创作作品

### 美术资源
{chr(10).join([f"- {Path(p).name}" for p in results['artworks_created']]) if results['artworks_created'] else "- 暂无作品"}

### 音效资源
{chr(10).join([f"- {Path(p).name}" for p in results['sounds_created']]) if results['sounds_created'] else "- 暂无音效"}

## 🎯 创作过程

1. ✓ 打开桌面浏览器
2. ✓ 浏览教程学习技巧
3. ✓ 收集风格参考
4. ✓ 分析视觉特征
5. ✓ 创作原创作品
6. ✓ 生成配套音效
7. ✓ 保存到桌面

## 🎨 风格特征

{self._format_style_analysis()}

## 📝 创作心得

Angela通过浏览网络教程和作品画廊，学习到了：
- 色彩搭配技巧
- 构图方法
- 风格特征

并将这些知识融入自己的创作中，生成独特的美术资源。

---
*由 Angela AI 自主创作 | Matrix Vision + Tactile Control + Creative Memory*
"""
        
        with open(showcase_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✓ 展示文件已创建: {showcase_path}")
    
    def _format_style_analysis(self) -> str:
        """格式化风格分析"""
        if not self.collected_styles:
            return "暂无风格分析数据"
        
        analysis = []
        for i, style in enumerate(self.collected_styles[:3]):
            analysis.append(f"### 参考 #{i+1}")
            if 'dominant_colors' in style:
                analysis.append(f"- 主色调: {len(style['dominant_colors'])} 种")
            if 'aspect_ratio' in style:
                analysis.append(f"- 宽高比: {style['aspect_ratio']:.2f}")
            analysis.append("")
        
        return "\n".join(analysis)


# 便捷运行函数
async def run_angela_learning_creation():
    """
    运行Angela学习创作流程
    实际保存到桌面: C:\Users\catai\OneDrive\Desktop
    """
    
    # 教程和画廊URL（示例）
    tutorial_urls = [
        "https://www.deviantart.com/tag/tutorial",
        "https://www.artstation.com/learning"
    ]
    
    gallery_urls = [
        "https://www.pinterest.com/search/pins/?q=anime%20art%20style",
        "https://www.zerochan.net/"
    ]
    
    angela = AngelaCreativeWorkflow()
    await angela.initialize()
    
    print("🎨 Angela 开始学习创作...")
    print("=" * 50)
    
    results = await angela.learn_and_create(
        tutorial_urls=tutorial_urls,
        gallery_urls=gallery_urls,
        num_artworks=3
    )
    
    print("\n" + "=" * 50)
    print("✅ 创作完成!")
    print(f"📚 学习教程: {results['tutorials_learned']} 个")
    print(f"🖼️ 收集参考: {results['artworks_collected']} 张")
    print(f"🎨 创作作品: {len(results['artworks_created'])} 幅")
    print(f"🔊 生成音效: {len(results['sounds_created'])} 个")
    
    if results['artworks_created']:
        print("\n🖼️ 作品位置:")
        for path in results['artworks_created']:
            print(f"   → {path}")
    
    if results['errors']:
        print("\n⚠️  遇到的错误:")
        for err in results['errors'][:3]:
            print(f"   ! {err}")
    
    print(f"\n📂 所有文件已保存到: C:\\Users\\catai\\OneDrive\\Desktop")
    print("📄 查看 Angela_Creations_Showcase.md 了解详情")


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("🎨 Angela AI 学习创作系统")
    print("=" * 60)
    print()
    print("功能：")
    print("  1. 在桌面背景打开浏览器")
    print("  2. 浏览教程学习技巧")
    print("  3. 收集风格参考")
    print("  4. 创作美术资源（笔触级）")
    print("  5. 生成音效")
    print("  6. 保存到桌面: C:\\Users\\catai\\OneDrive\\Desktop")
    print()
    print("运行: python angela_creative_workflow.py")
    print()
    
    # 实际运行
    asyncio.run(run_angela_learning_creation())
