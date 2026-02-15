"""
Angela Real Image Generator - ComfyUI API Integration
真实AI绘画模块 - 使用 ComfyUI API

使用前确保：
1. ComfyUI 运行在 http://127.0.0.1:8188
2. 安装了必要的模型 (SDXL/SD1.5)
"""

import asyncio
import aiohttp
import base64
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI API 客户端"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8188"):
        self.server_url = server_url.rstrip('/')
        self.client_id = "angela_ai_" + str(time.time())
        
    async def get_models(self) -> List[str]:
        """获取可用模型列表"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/object_info") as resp:
                data = await resp.json()
                models = []
                if "checkpointloader" in data.get("class_type_map", {}):
                    models = list(data.get("class_type_map", {}).keys())
                return models
    
    async def get_history(self, prompt_id: str) -> Dict:
        """获取生成历史"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/history/{prompt_id}") as resp:
                return await resp.json()
    
    async def get_images(self, node_id: str, prompt_id: str) -> List[str]:
        """获取生成的图片"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_url}/view",
                params={"filename": node_id, "type": "output", "prompt_id": prompt_id}
            ) as resp:
                data = await resp.json()
                return data.get("images", [])
    
    async def generate(
        self,
        prompt_text: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "euler_a",
        scheduler: str = "normal",
        model_name: str = "sd_xl_base_1.0.safetensors",
        seed: int = -1,
    ) -> Optional[Image.Image]:
        """
        使用 ComfyUI 生成图片
        
        Args:
            prompt_text: 英文提示词
            width: 图片宽度
            height: 图片高度
            steps: 采样步数
            cfg_scale: CFG 比例
            sampler: 采样器
            scheduler: 调度器
            model_name: 模型名称
            seed: 随机种子 (-1 随机)
            
        Returns:
            PIL Image 或 None
        """
        if seed == -1:
            seed = int(time.time() % 2147483647)
        
        workflow = self._create_workflow(
            prompt=prompt_text,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            sampler_name=sampler_name,
            scheduler=scheduler,
            model_name=model_name,
            seed=seed,
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/prompt",
                json={"prompt": workflow, "client_id": self.client_id}
            ) as resp:
                if resp.status != 200:
                    logger.error(f"ComfyUI API 错误: {await resp.text()}")
                    return None
                data = await resp.json()
                prompt_id = data.get("prompt_id")
                if not prompt_id:
                    logger.error("无法获取 prompt_id")
                    return None
            
            output_images = []
            for _ in range(100):
                await asyncio.sleep(0.5)
                history = await self.get_history(prompt_id)
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            for img_data in node_output["images"]:
                                output_images.append(img_data)
                    if output_images:
                        break
            
            if not output_images:
                logger.error("未找到生成的图片")
                return None
            
            for img_info in output_images:
                filename = img_info.get("filename")
                if filename:
                    images_data = await self.get_images(filename, prompt_id)
                    for img_b64 in images_data:
                        img_bytes = base64.b64decode(img_b64)
                        return Image.open(io.BytesIO(img_bytes))
        
        return None
    
    def _create_workflow(
        self,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg_scale: float,
        sampler_name: str,
        scheduler: str,
        model_name: str,
        seed: int,
    ) -> Dict:
        """创建 ComfyUI 工作流"""
        return {
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "positive": f"(best quality, detailed), {prompt}",
                    "negative": "(worst quality, low quality), blurry, deformed",
                    "model": ["4", 0],
                    "clip": ["4", 1],
                    "vae": ["4", 2],
                    "sampler": ["5", 0],
                    "latent_image": ["6", 0],
                },
                "class_type": "KSampler",
                "_class_type": "KSampler",
            },
            "4": {
                "inputs": {
                    "model_name": model_name,
                },
                "class_type": "CheckpointLoaderSimple",
                "_class_type": "CheckpointLoaderSimple",
            },
            "5": {
                "inputs": {
                    "sampler_name": sampler_name,
                },
                "class_type": "SamplerCustom",
                "_class_type": "SamplerCustom",
            },
            "6": {
                "inputs": {
                    "width": width,
                    "height": height,
                },
                "class_type": "EmptyLatentImage",
                "_class_type": "EmptyLatentImage",
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2],
                },
                "class_type": "VAEDecode",
                "_class_type": "VAEDecode",
            },
            "9": {
                "inputs": {
                    "images": ["8", 0],
                },
                "class_type": "SaveImage",
                "_class_type": "SaveImage",
            },
        }


class AngelaRealPainter:
    """
    Angela 真实绘画系统
    使用 ComfyUI API 进行真正的 AI 绘画
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "Desktop"
        self.comfyui = ComfyUIClient()
        
    async def paint_portrait(
        self,
        description: str,
        style: str = "anime",
        size: tuple = (512, 512),
    ) -> Optional[Path]:
        """
        绘制 Angela 肖像
        
        Args:
            description: 描述 (会被翻译成英文)
            style: 风格 (anime/realistic/cartoon)
            size: 图片尺寸
            
        Returns:
            保存的文件路径 或 None
        """
        prompts = {
            "anime": f"beautiful anime girl, blue gradient hair, expressive eyes, detailed illustration style, soft lighting, {description}",
            "realistic": f"beautiful woman, natural features, soft makeup, professional photography, cinematic lighting, {description}",
            "cartoon": f"cute cartoon character, bold colors, clean lines, playful expression, {description}",
        }
        
        prompt = prompts.get(style, prompts["anime"])
        
        image = await self.comfyui.generate(
            prompt_text=prompt,
            width=size[0],
            height=size[1],
        )
        
        if image:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"Angela_Portrait_{style}_{timestamp}.png"
            save_path = self.output_dir / filename
            image.save(save_path)
            logger.info(f"✅ 肖像已保存: {save_path}")
            return save_path
        
        logger.error("❌ 肖像生成失败")
        return None
    
    async def paint_background(
        self,
        scene: str = "blue sky with clouds",
        style: str = "anime landscape",
    ) -> Optional[Path]:
        """
        绘制背景图
        
        Args:
            scene: 场景描述
            style: 风格
            
        Returns:
            保存的文件路径 或 None
        """
        prompt = f"{style}, {scene}, detailed environment art, beautiful lighting"
        
        image = await self.comfyui.generate(
            prompt_text=prompt,
            width=1920,
            height=1080,
            steps=30,
        )
        
        if image:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"Angela_Background_{timestamp}.png"
            save_path = self.output_dir / filename
            image.save(save_path)
            logger.info(f"✅ 背景已保存: {save_path}")
            return save_path
        
        logger.error("❌ 背景生成失败")
        return None
    
    async def paint_expression(
        self,
        emotion: str = "happy",
        style: str = "anime icon",
    ) -> Optional[Path]:
        """
        绘制表情图标
        
        Args:
            emotion: 情绪 (happy/sad/surprised/angry)
            style: 风格
            
        Returns:
            保存的文件路径 或 None
        """
        emotion_prompts = {
            "happy": "happy smile, closed eyes, rosy cheeks",
            "sad": "sad expression, tears, frowning",
            "surprised": "surprised, open mouth, wide eyes",
            "angry": "angry expression, furrowed brows",
        }
        
        prompt = f"{style}, character face, {emotion_prompts.get(emotion, emotion)}"
        
        image = await self.comfyui.generate(
            prompt_text=prompt,
            width=256,
            height=256,
            steps=15,
        )
        
        if image:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"Angela_{emotion.capitalize()}_{timestamp}.png"
            save_path = self.output_dir / filename
            image.save(save_path)
            logger.info(f"✅ 表情已保存: {save_path}")
            return save_path
        
        logger.error("❌ 表情生成失败")
        return None


async def test_comfyui():
    """测试 ComfyUI 连接"""
    logger.info("🧪 测试 ComfyUI API...")
    client = ComfyUIClient()
    
    try:
        models = await client.get_models()
        logger.info(f"✅ ComfyUI 连接成功!")
        logger.info(f"📦 可用模型: {len(models)} 个")
        
        painter = AngelaRealPainter()
        logger.info("\n🎨 测试生成...")
        
        result = await painter.paint_expression("happy")
        if result:
            logger.info(f"✅ 测试图片已保存: {result}")
        
    except Exception as e:
        logger.info(f"❌ ComfyUI 连接失败: {e}")
        logger.info("请确保 ComfyUI 运行在 http://127.0.0.1:8188")


if __name__ == "__main__":
    import sys
    asyncio.run(test_comfyui())
