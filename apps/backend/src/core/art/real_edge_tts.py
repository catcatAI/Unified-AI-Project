"""
Angela Real Voice Generator - Edge TTS Integration
真实语音生成模块 - 使用 edge-tts

使用前确保：
1. pip install edge-tts
2. Windows 系统 (edge-tts 使用 Edge 浏览器的 TTS)
"""

import asyncio
import edge_tts
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class AngelaRealVoice:
    """
    Angela 真实语音系统
    使用 Microsoft Edge TTS (免费、高质量)
    """
    
    # 可用声音列表
    VOICES = {
        "en": {
            "female": "en-US-AriaNeural",
            "male": "en-US-GuyNeural",
            "casual": "en-US-JennyNeural",
        },
        "zh": {
            "female": "zh-CN-XiaoxiaoNeural",
            "male": "zh-CN-YunxiNeural",
            "young": "zh-CN-XiaoyouNeural",
        },
        "ja": {
            "female": "ja-JP-NanamiNeural",
            "male": "ja-JP-KeitaNeural",
        },
    }
    
    # 情绪映射
    EMOTIONS = {
        "happy": "+10%",
        "sad": "-10%",
        "angry": "+15%",
        "surprised": "+5%",
        "calm": "+0%",
    }
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "Desktop"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def _generate_audio(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
    ) -> Optional[Path]:
        """
        生成语音文件
        
        Args:
            text: 要朗读的文本
            voice: 声音名称
            rate: 语速 (+/-%)
            pitch: 音调 (+/-Hz)
            volume: 音量 (+/-%)
            
        Returns:
            保存的文件路径 或 None
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Angela_Voice_{timestamp}.wav"
            save_path = self.output_dir / filename
            
            await communicate.save(str(save_path))
            
            if save_path.exists():
                logger.info(f"✅ 语音已保存: {save_path}")
                return save_path
            else:
                logger.error("❌ 语音文件未生成")
                return None
                
        except Exception as e:
            logger.error(f"❌ 语音生成失败: {e}")
            return None
    
    async def greet(self, name: str = "friend") -> Optional[Path]:
        """
        生成问候语音
        
        Args:
            name: 被问候者的名字
            
        Returns:
            语音文件路径
        """
        text = f"Hello {name}! I'm Angela. I'm happy to see you! How can I help you today?"
        
        return await self._generate_audio(
            text=text,
            voice=self.VOICES["en"]["female"],
            rate="+5%",
            pitch="+2Hz",
        )
    
    async def introduce(self) -> Optional[Path]:
        """
        生成自我介绍语音
        
        Returns:
            语音文件路径
        """
        text = """
        Hi there! I'm Angela, an AI assistant created to help you with creative tasks.
        I can generate images using AI, browse the web to learn new things,
        and have conversations with you.
        What would you like to create together today?
        """
        
        return await self._generate_audio(
            text=text.strip(),
            voice=self.VOICES["en"]["casual"],
            rate="+0%",
            pitch="+0Hz",
        )
    
    async def express_emotion(
        self,
        emotion: str,
        custom_text: str = None,
    ) -> Optional[Path]:
        """
        生成带情绪的语音
        
        Args:
            emotion: 情绪 (happy/sad/angry/surprised/calm)
            custom_text: 自定义文本
            
        Returns:
            语音文件路径
        """
        emotion_texts = {
            "happy": "I'm so happy to see you! Today is a wonderful day!",
            "sad": "I understand. Sometimes things can be difficult.",
            "angry": "That really frustrates me! It shouldn't be this way.",
            "surprised": "Oh! That's surprising! I didn't expect that!",
            "calm": "Take a deep breath. Everything will be okay.",
        }
        
        text = custom_text or emotion_texts.get(emotion, "I'm feeling great!")
        
        rate_map = {"happy": "+10%", "sad": "-5%", "angry": "+5%", "surprised": "+10%", "calm": "-5%"}
        pitch_map = {"happy": "+5Hz", "sad": "-5Hz", "angry": "+5Hz", "surprised": "+10Hz", "calm": "-2Hz"}
        
        return await self._generate_audio(
            text=text,
            voice=self.VOICES["en"]["female"],
            rate=rate_map.get(emotion, "+0%"),
            pitch=pitch_map.get(emotion, "+0Hz"),
        )
    
    async def narration(
        self,
        story_text: str,
        voice_name: str = None,
    ) -> Optional[Path]:
        """
        生成叙述语音
        
        Args:
            story_text: 故事文本
            voice_name: 指定声音 (可选)
            
        Returns:
            语音文件路径
        """
        voice = voice_name or self.VOICES["en"]["female"]
        
        return await self._generate_audio(
            text=story_text,
            voice=voice,
            rate="+0%",
            pitch="+0Hz",
        )
    
    async def list_voices(self) -> dict:
        """
        获取所有可用声音
        
        Returns:
            按语言分组的声音列表
        """
        try:
            voices = await edge_tts.list_voices()
            result = {}
            for voice in voices:
                lang = voice["Locale"].split("-")[0]
                if lang not in result:
                    result[lang] = []
                result[lang].append({
                    "name": voice["Name"],
                    "gender": voice["Gender"],
                    "locale": voice["Locale"],
                })
            return result
        except Exception as e:
            logger.error(f"获取声音列表失败: {e}")
            return {}


async def test_voice():
    """测试语音生成"""
    print("🧪 测试 Edge TTS...")
    
    voice = AngelaRealVoice()
    
    try:
        print("📋 获取可用声音...")
        voices = await voice.list_voices()
        print(f"✅ 获取到 {sum(len(v) for v in voices.values())} 个声音")
        
        print("\n🎤 测试问候...")
        result = await voice.greet("User")
        if result:
            print(f"✅ 语音已保存: {result}")
        else:
            print("❌ 语音生成失败")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("提示: 确保已安装 edge-tts: pip install edge-tts")


if __name__ == "__main__":
    import sys
    asyncio.run(test_voice())
