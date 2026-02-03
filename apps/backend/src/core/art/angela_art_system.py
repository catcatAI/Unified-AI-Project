"""
Angela Art Resource System - Self-Generating Asset Manager

让Angela能够自主生成和管理美术资源：
- 生成角色图像（使用AI绘画API或本地模型）
- 生成Live2D模型参数
- 生成语音样本（TTS）
- 生成字体和UI资源
- 管理资源版本和缓存

使用方法:
    from apps.backend.src.core.art.angela_art_system import AngelaArtSystem
    
    art_system = AngelaArtSystem()
    
    # 生成Angela形象
    await art_system.generate_character_portrait(
        style="anime",
        mood="happy",
        output_path="resources/angela/portrait.png"
    )
    
    # 生成Live2D参数
    await art_system.generate_live2d_parameters(
        character_description="cute AI assistant with blue hair"
    )
    
    # 生成语音
    await art_system.generate_voice_sample(
        text="Hello, I'm Angela!",
        emotion="joyful",
        output_path="resources/angela/voice_greeting.wav"
    )
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from apps.backend.src.core.services.multi_llm_service import MultiLLMService, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class ArtResourceConfig:
    """美术资源配置"""
    resources_base_path: str = "resources/angela"
    ai_generation_enabled: bool = True
    use_api_for_generation: bool = True  # True=使用API, False=使用本地模型
    
    # AI绘画API配置
    image_api_provider: str = "openai"  # openai, stability_ai, local_sd
    image_api_model: str = "dall-e-3"
    
    # TTS配置
    tts_provider: str = "edge_tts"  # edge_tts, openai_tts, local_piper
    tts_voice: str = "en-US-AnaNeural"  # Edge TTS voice
    
    # Live2D配置
    live2d_auto_rigging: bool = False  # 自动绑定（需要复杂算法）
    
    # 资源版本
    resource_version: str = "1.0.0"


@dataclass
class GeneratedAsset:
    """生成的资源记录"""
    asset_type: str  # image, audio, model, font
    path: str
    generation_prompt: str
    generation_params: Dict[str, Any]
    created_at: datetime
    version: str
    hash: str


class AngelaArtSystem:
    """
    Angela美术资源系统
    
    让Angela能够自主生成、管理和优化美术资源。
    """
    
    def __init__(self, llm_service: Optional[MultiLLMService] = None, 
                 config: Optional[ArtResourceConfig] = None):
        self.config = config or ArtResourceConfig()
        self.llm_service = llm_service
        
        # 初始化资源目录
        self._init_resource_directories()
        
        # 资源注册表
        self.asset_registry: Dict[str, List[GeneratedAsset]] = {}
        self._load_asset_registry()
        
        logger.info(f"AngelaArtSystem initialized. Resources path: {self.config.resources_base_path}")
    
    def _init_resource_directories(self):
        """初始化资源目录结构"""
        base = Path(self.config.resources_base_path)
        
        directories = [
            "images/portraits",
            "images/expressions",
            "images/backgrounds",
            "live2d/models",
            "live2d/textures",
            "live2d/motions",
            "audio/voices",
            "audio/sounds",
            "audio/music",
            "fonts",
            "icons",
            "cache"
        ]
        
        for dir_name in directories:
            (base / dir_name).mkdir(parents=True, exist_ok=True)
        
        logger.info("Resource directories initialized")
    
    def _load_asset_registry(self):
        """加载资源注册表"""
        registry_path = Path(self.config.resources_base_path) / "asset_registry.json"
        
        if registry_path.exists():
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert dict back to GeneratedAsset objects
                    for asset_type, assets in data.items():
                        self.asset_registry[asset_type] = [
                            GeneratedAsset(
                                asset_type=a['asset_type'],
                                path=a['path'],
                                generation_prompt=a['generation_prompt'],
                                generation_params=a['generation_params'],
                                created_at=datetime.fromisoformat(a['created_at']),
                                version=a['version'],
                                hash=a['hash']
                            )
                            for a in assets
                        ]
                logger.info(f"Loaded {sum(len(v) for v in self.asset_registry.values())} assets from registry")
            except Exception as e:
                logger.error(f"Error loading asset registry: {e}")
    
    def _save_asset_registry(self):
        """保存资源注册表"""
        registry_path = Path(self.config.resources_base_path) / "asset_registry.json"
        
        try:
            data = {}
            for asset_type, assets in self.asset_registry.items():
                data[asset_type] = [
                    {
                        'asset_type': a.asset_type,
                        'path': a.path,
                        'generation_prompt': a.generation_prompt,
                        'generation_params': a.generation_params,
                        'created_at': a.created_at.isoformat(),
                        'version': a.version,
                        'hash': a.hash
                    }
                    for a in assets
                ]
            
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving asset registry: {e}")
    
    async def generate_character_portrait(self, 
                                         style: str = "anime",
                                         mood: str = "neutral",
                                         outfit: str = "default",
                                         output_name: Optional[str] = None) -> str:
        """
        生成Angela角色肖像
        
        Args:
            style: 艺术风格 (anime, realistic, chibi, pixel_art)
            mood: 情绪状态 (happy, sad, angry, surprised, neutral)
            outfit: 服装风格 (default, casual, formal, fantasy)
            output_name: 输出文件名（可选）
            
        Returns:
            生成的图片路径
        """
        if not output_name:
            output_name = f"portrait_{style}_{mood}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path = Path(self.config.resources_base_path) / "images" / "portraits" / output_name
        
        # 构建生成提示词
        prompt = self._build_portrait_prompt(style, mood, outfit)
        
        logger.info(f"Generating character portrait: {prompt}")
        
        try:
            if self.config.use_api_for_generation and self.llm_service:
                # 使用AI绘画API
                image_url = await self._generate_image_with_api(prompt)
                if image_url:
                    await self._download_image(image_url, output_path)
            else:
                # 使用占位符或本地生成
                await self._generate_placeholder_portrait(output_path, style, mood)
            
            # 记录到注册表
            asset = GeneratedAsset(
                asset_type="image",
                path=str(output_path),
                generation_prompt=prompt,
                generation_params={"style": style, "mood": mood, "outfit": outfit},
                created_at=datetime.now(),
                version=self.config.resource_version,
                hash=""  # 可以计算文件hash
            )
            
            if "image" not in self.asset_registry:
                self.asset_registry["image"] = []
            self.asset_registry["image"].append(asset)
            self._save_asset_registry()
            
            logger.info(f"Character portrait generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating portrait: {e}")
            # 创建占位符
            await self._generate_placeholder_portrait(output_path, style, mood)
            return str(output_path)
    
    def _build_portrait_prompt(self, style: str, mood: str, outfit: str) -> str:
        """构建肖像生成提示词"""
        base_description = """
        Angela, a friendly AI digital assistant with a warm personality.
        She has soft blue-white gradient hair that flows gently.
        Her eyes are bright and expressive with a technological glow.
        She wears a modern, elegant outfit that blends technology and fashion.
        Clean background with soft lighting.
        High quality, detailed, professional artwork.
        """
        
        style_modifiers = {
            "anime": "anime style, manga, cel shading, vibrant colors",
            "realistic": "photorealistic, 3D render, detailed skin texture, professional photography",
            "chibi": "chibi style, super deformed, cute, kawaii, big head small body",
            "pixel_art": "pixel art, 16-bit, retro game style, crisp pixels"
        }
        
        mood_modifiers = {
            "happy": "smiling, cheerful, bright eyes, joyful expression",
            "sad": "gentle tears, melancholic, soft expression, comforting",
            "angry": "determined, fierce, powerful, intense gaze",
            "surprised": "wide eyes, open mouth, shocked, amazed",
            "neutral": "calm, composed, serene, gentle smile"
        }
        
        outfit_modifiers = {
            "default": "futuristic white and blue dress with holographic elements",
            "casual": "casual modern clothes, sweater, jeans, comfortable",
            "formal": "elegant gown, sophisticated, professional attire",
            "fantasy": "magical robes, ethereal, glowing runes, fantasy elements"
        }
        
        prompt = f"{base_description}, {style_modifiers.get(style, style)}, "
        prompt += f"{mood_modifiers.get(mood, mood)}, "
        prompt += f"{outfit_modifiers.get(outfit, outfit)}"
        
        return prompt.strip()
    
    async def _generate_image_with_api(self, prompt: str) -> Optional[str]:
        """使用API生成图片"""
        try:
            if self.config.image_api_provider == "openai":
                # OpenAI DALL-E
                # Note: 这需要实际的API调用代码
                logger.info("Would call OpenAI DALL-E API here")
                # Placeholder return
                return None
            else:
                logger.warning(f"Image API provider {self.config.image_api_provider} not implemented")
                return None
        except Exception as e:
            logger.error(f"Error calling image API: {e}")
            return None
    
    async def _download_image(self, url: str, output_path: Path):
        """下载图片"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        with open(output_path, 'wb') as f:
                            f.write(data)
                        logger.info(f"Image downloaded to {output_path}")
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            raise
    
    async def _generate_placeholder_portrait(self, output_path: Path, style: str, mood: str):
        """生成占位符肖像（当API不可用时）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建基础图像
            img = Image.new('RGB', (512, 512), color=(240, 240, 250))
            draw = ImageDraw.Draw(img)
            
            # 绘制简单图形表示Angela
            # 头部（圆形）
            draw.ellipse([156, 100, 356, 300], fill=(255, 220, 200), outline=(200, 160, 140), width=2)
            
            # 眼睛
            eye_color = (100, 150, 255) if mood == "happy" else (150, 150, 150)
            draw.ellipse([200, 180, 240, 220], fill=eye_color)  # 左眼
            draw.ellipse([272, 180, 312, 220], fill=eye_color)  # 右眼
            
            # 嘴巴（根据情绪）
            if mood == "happy":
                draw.arc([220, 240, 292, 280], start=0, end=180, fill=(200, 100, 100), width=3)
            elif mood == "sad":
                draw.arc([220, 260, 292, 300], start=180, end=360, fill=(200, 100, 100), width=3)
            else:
                draw.line([220, 260, 292, 260], fill=(200, 100, 100), width=3)
            
            # 头发（简化版）
            draw.ellipse([140, 80, 372, 200], fill=(200, 220, 255), outline=(180, 200, 240), width=2)
            
            # 添加文字标签
            text = f"Angela\n({style}, {mood})\n[Placeholder]"
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((20, 400), text, fill=(100, 100, 100), font=font)
            
            # 保存
            img.save(output_path)
            logger.info(f"Placeholder portrait created: {output_path}")
            
        except ImportError:
            logger.warning("PIL not available, creating text placeholder")
            # 创建文本占位符
            with open(output_path.with_suffix('.txt'), 'w') as f:
                f.write(f"Placeholder for Angela portrait\nStyle: {style}\nMood: {mood}\n")
        except Exception as e:
            logger.error(f"Error creating placeholder: {e}")
    
    async def generate_voice_sample(self,
                                   text: str,
                                   emotion: str = "neutral",
                                   output_name: Optional[str] = None) -> str:
        """
        生成Angela语音样本
        
        Args:
            text: 要说的文本
            emotion: 情绪 (neutral, happy, sad, excited, calm)
            output_name: 输出文件名
            
        Returns:
            生成的音频路径
        """
        if not output_name:
            output_name = f"voice_{emotion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        output_path = Path(self.config.resources_base_path) / "audio" / "voices" / output_name
        
        logger.info(f"Generating voice for: '{text}' with emotion: {emotion}")
        
        try:
            if self.config.tts_provider == "edge_tts":
                await self._generate_with_edge_tts(text, output_path)
            elif self.config.tts_provider == "openai_tts":
                await self._generate_with_openai_tts(text, output_path)
            else:
                await self._generate_placeholder_audio(output_path, text)
            
            # 记录到注册表
            asset = GeneratedAsset(
                asset_type="audio",
                path=str(output_path),
                generation_prompt=text,
                generation_params={"emotion": emotion, "provider": self.config.tts_provider},
                created_at=datetime.now(),
                version=self.config.resource_version,
                hash=""
            )
            
            if "audio" not in self.asset_registry:
                self.asset_registry["audio"] = []
            self.asset_registry["audio"].append(asset)
            self._save_asset_registry()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            await self._generate_placeholder_audio(output_path, text)
            return str(output_path)
    
    async def _generate_with_edge_tts(self, text: str, output_path: Path):
        """使用Edge TTS生成语音"""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(text, self.config.tts_voice)
            await communicate.save(str(output_path))
            logger.info(f"Voice generated with Edge TTS: {output_path}")
        except ImportError:
            logger.warning("edge_tts not available")
            await self._generate_placeholder_audio(output_path, text)
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            await self._generate_placeholder_audio(output_path, text)
    
    async def _generate_with_openai_tts(self, text: str, output_path: Path):
        """使用OpenAI TTS生成语音"""
        # Placeholder for OpenAI TTS
        logger.info("OpenAI TTS not yet implemented, using placeholder")
        await self._generate_placeholder_audio(output_path, text)
    
    async def _generate_placeholder_audio(self, output_path: Path, text: str):
        """生成占位符音频"""
        try:
            import wave
            import struct
            
            # 创建一个简单的空白WAV文件
            with wave.open(str(output_path), 'w') as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(16000)  # 16kHz
                
                # 1秒的静音
                for _ in range(16000):
                    wav.writeframes(struct.pack('h', 0))
            
            # 同时创建一个文本文件说明内容
            txt_path = output_path.with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Voice content: {text}\n")
                f.write("Note: This is a placeholder audio file\n")
                f.write("Install edge-tts or configure TTS provider for real audio\n")
            
            logger.info(f"Placeholder audio created: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creating placeholder audio: {e}")
    
    async def generate_expression_set(self, moods: List[str] = None) -> List[str]:
        """
        生成一套表情图像
        
        Args:
            moods: 要生成的情绪列表
            
        Returns:
            生成的图像路径列表
        """
        if moods is None:
            moods = ["neutral", "happy", "sad", "angry", "surprised", "embarrassed"]
        
        generated_paths = []
        
        for mood in moods:
            path = await self.generate_character_portrait(
                style="anime",
                mood=mood,
                output_name=f"expression_{mood}.png"
            )
            generated_paths.append(path)
        
        logger.info(f"Generated expression set with {len(generated_paths)} images")
        return generated_paths
    
    async def generate_live2d_parameters(self, 
                                        character_description: str,
                                        output_name: str = "angela") -> Dict[str, Any]:
        """
        生成Live2D模型参数
        
        创建Live2D模型所需的JSON参数文件，
        可以使用Cubism编辑器或程序化生成。
        
        Args:
            character_description: 角色描述
            output_name: 输出模型名称
            
        Returns:
            Live2D参数字典
        """
        logger.info(f"Generating Live2D parameters for: {character_description}")
        
        # 基础Live2D模型结构
        live2d_params = {
            "version": "1.0.0",
            "model_name": output_name,
            "description": character_description,
            "parameters": {
                "face": {
                    "eye_left": {"id": "ParamEyeLOpen", "default": 1.0, "min": 0.0, "max": 1.0},
                    "eye_right": {"id": "ParamEyeROpen", "default": 1.0, "min": 0.0, "max": 1.0},
                    "mouth": {"id": "ParamMouthOpenY", "default": 0.0, "min": 0.0, "max": 1.0},
                    "eyebrow_left": {"id": "ParamBrowLY", "default": 0.0, "min": -1.0, "max": 1.0},
                    "eyebrow_right": {"id": "ParamBrowRY", "default": 0.0, "min": -1.0, "max": 1.0},
                    "cheek": {"id": "ParamCheek", "default": 0.0, "min": 0.0, "max": 1.0}
                },
                "body": {
                    "breathing": {"id": "ParamBreath", "default": 0.0, "min": 0.0, "max": 1.0},
                    "body_angle": {"id": "ParamBodyAngle", "default": 0.0, "min": -1.0, "max": 1.0}
                },
                "hair": {
                    "front": {"id": "ParamHairFront", "default": 0.0, "min": -1.0, "max": 1.0},
                    "side": {"id": "ParamHairSide", "default": 0.0, "min": -1.0, "max": 1.0},
                    "back": {"id": "ParamHairBack", "default": 0.0, "min": -1.0, "max": 1.0}
                },
                "emotions": {
                    "joy": {"id": "ParamJoy", "default": 0.0, "min": 0.0, "max": 1.0},
                    "anger": {"id": "ParamAnger", "default": 0.0, "min": 0.0, "max": 1.0},
                    "sadness": {"id": "ParamSadness", "default": 0.0, "min": 0.0, "max": 1.0},
                    "surprise": {"id": "ParamSurprise", "default": 0.0, "min": 0.0, "max": 1.0}
                }
            },
            "textures": {
                "base": f"{output_name}_base.png",
                "expressions": {
                    "neutral": f"{output_name}_neutral.png",
                    "happy": f"{output_name}_happy.png",
                    "sad": f"{output_name}_sad.png"
                }
            },
            "motions": {
                "idle": {"file": "motion_idle.json", "loop": True},
                "tap": {"file": "motion_tap.json", "loop": False},
                "greeting": {"file": "motion_greeting.json", "loop": False}
            }
        }
        
        # 保存参数文件
        output_path = Path(self.config.resources_base_path) / "live2d" / f"{output_name}.model3.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(live2d_params, f, indent=2, ensure_ascii=False)
        
        # 记录到注册表
        asset = GeneratedAsset(
            asset_type="model",
            path=str(output_path),
            generation_prompt=character_description,
            generation_params={"type": "live2d_parameters"},
            created_at=datetime.now(),
            version=self.config.resource_version,
            hash=""
        )
        
        if "model" not in self.asset_registry:
            self.asset_registry["model"] = []
        self.asset_registry["model"].append(asset)
        self._save_asset_registry()
        
        logger.info(f"Live2D parameters generated: {output_path}")
        
        return live2d_params
    
    def get_resource_inventory(self) -> Dict[str, Any]:
        """
        获取当前资源清单
        
        Returns:
            资源统计信息
        """
        inventory = {
            "total_assets": 0,
            "by_type": {},
            "by_directory": {},
            "missing_essential": []
        }
        
        # 统计注册表中的资源
        for asset_type, assets in self.asset_registry.items():
            inventory["by_type"][asset_type] = len(assets)
            inventory["total_assets"] += len(assets)
        
        # 检查文件系统
        base_path = Path(self.config.resources_base_path)
        for subdir in ["images", "live2d", "audio", "fonts"]:
            dir_path = base_path / subdir
            if dir_path.exists():
                file_count = len(list(dir_path.rglob("*")))
                inventory["by_directory"][subdir] = file_count
        
        # 检查必需资源
        essential_files = [
            base_path / "images" / "portraits" / "angela_default.png",
            base_path / "live2d" / "angela.model3.json",
            base_path / "audio" / "voices" / "greeting.wav"
        ]
        
        for file_path in essential_files:
            if not file_path.exists():
                inventory["missing_essential"].append(str(file_path.relative_to(base_path)))
        
        return inventory
    
    async def initialize_default_resources(self):
        """
        初始化默认资源集
        
        生成Angela运行所需的基本资源。
        """
        logger.info("Initializing default Angela resources...")
        
        # 生成表情集
        await self.generate_expression_set()
        
        # 生成Live2D参数
        await self.generate_live2d_parameters(
            character_description="Angela, a friendly AI assistant with blue gradient hair and warm smile",
            output_name="angela"
        )
        
        # 生成基本语音
        await self.generate_voice_sample(
            text="Hello! I'm Angela, your AI companion. Nice to meet you!",
            emotion="happy",
            output_name="greeting.wav"
        )
        
        logger.info("Default resources initialization complete!")


# 便捷函数
async def quick_setup_angela_assets():
    """快速设置Angela基础资源"""
    art_system = AngelaArtSystem()
    await art_system.initialize_default_resources()
    
    inventory = art_system.get_resource_inventory()
    print(f"✅ Angela assets initialized!")
    print(f"   Total assets: {inventory['total_assets']}")
    print(f"   By type: {inventory['by_type']}")
    
    if inventory['missing_essential']:
        print(f"   ⚠️  Missing: {inventory['missing_essential']}")
    
    return art_system


# 测试代码
if __name__ == '__main__':
    print("--- Angela Art System Test ---")
    
    # 运行测试
    asyncio.run(quick_setup_angela_assets())
    
    print("\nArt system ready! Run with actual API keys for full generation.")
