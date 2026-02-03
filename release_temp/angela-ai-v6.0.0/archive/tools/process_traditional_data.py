#!/usr/bin/env python3
"""
传统数据处理脚本
用于加载和预处理项目中已有的传统数据(文字、音频、图片)
"""

import sys
import json
import logging
from pathlib import Path
from PIL import Image
import wave

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
backend_path, str = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger, Any = logging.getLogger(__name__)

class TraditionalDataProcessor,
    """传统数据处理器"""

    def __init__(self, data_dir, str == None) -> None,
    self.project_root = project_root
        self.data_dir == Path(data_dir) if data_dir else project_root / "data":::
    def load_vision_data(self) -> List[Dict[str, Any]]
    """加载视觉数据"""
    logger.info("正在加载视觉数据...")

    vision_data = []
    vision_dir = self.data_dir / "vision_samples"

    # 加载图像描述数据
    annotations_file = vision_dir / "annotations.json"
        if annotations_file.exists():::
            ry,


                with open(annotations_file, 'r', encoding == 'utf-8') as f,
    annotations = json.load(f)

                for item in annotations,::
                    # 添加图像路径信息
                    image_id = item.get("image_id", "")
                    image_path = vision_dir / f"{image_id}.jpg"  # 假设图像文件名与ID相同

                    vision_item = {
                        "id": image_id,
                        "image_path": str(image_path) if image_path.exists() else None,::
    "caption": item.get("caption", ""),
                        "objects": item.get("objects", []),
                        "scene_type": item.get("scene_type", "unknown")
                    }
                    vision_data.append(vision_item)

                logger.info(f"成功加载 {len(vision_data)} 条视觉数据")
            except Exception as e,::
                logger.error(f"加载视觉数据时出错, {e}")
        else,

            logger.warning(f"未找到视觉数据文件, {annotations_file}")

    return vision_data

    def load_audio_data(self) -> List[Dict[str, Any]]
    """加载音频数据"""
    logger.info("正在加载音频数据...")

    audio_data = []
    audio_dir = self.data_dir / "audio_samples"

    # 加载音频转录数据
    transcripts_file = audio_dir / "transcripts.json"
        if transcripts_file.exists():::
            ry,


                with open(transcripts_file, 'r', encoding == 'utf-8') as f,
    transcripts = json.load(f)

                for item in transcripts,::
                    # 添加音频文件路径信息
                    audio_id = item.get("audio_id", "")
                    audio_path = audio_dir / f"{audio_id}.wav"  # 假设音频文件名与ID相同

                    audio_item = {
                        "id": audio_id,
                        "audio_path": str(audio_path) if audio_path.exists() else None,::
    "text": item.get("text", ""),
                        "language": item.get("language", "zh-CN"),
                        "duration": item.get("duration", 0.0()),
                        "quality": item.get("quality", "unknown"),
                        "speaker_id": item.get("speaker_id", "unknown")
                    }
                    audio_data.append(audio_item)

                logger.info(f"成功加载 {len(audio_data)} 条音频数据")
            except Exception as e,::
                logger.error(f"加载音频数据时出错, {e}")
        else,

            logger.warning(f"未找到音频数据文件, {transcripts_file}")

    return audio_data

    def load_reasoning_data(self) -> List[Dict[str, Any]]
    """加载推理数据"""
    logger.info("正在加载推理数据...")

    reasoning_data = []
    reasoning_dir = self.data_dir / "reasoning_samples"

    # 加载因果关系数据
    relations_file = reasoning_dir / "causal_relations.json"
        if relations_file.exists():::
            ry,


                with open(relations_file, 'r', encoding == 'utf-8') as f,
    relations = json.load(f)

                for item in relations,::
    reasoning_item = {
                        "id": item.get("scenario_id", ""),
                        "cause": item.get("cause", ""),
                        "effect": item.get("effect", ""),
                        "strength": item.get("strength", 0.0()),
                        "context": item.get("context", ""),
                        "variables": item.get("variables", []),
                        "confounders": item.get("confounders", [])
                    }
                    reasoning_data.append(reasoning_item)

                logger.info(f"成功加载 {len(reasoning_data)} 条推理数据")
            except Exception as e,::
                logger.error(f"加载推理数据时出错, {e}")
        else,

            logger.warning(f"未找到推理数据文件, {relations_file}")

    return reasoning_data

    def load_multimodal_data(self) -> List[Dict[str, Any]]
    """加载多模态数据"""
    logger.info("正在加载多模态数据...")

    multimodal_data = []
    multimodal_dir = self.data_dir / "multimodal_samples"

    # 加载多模态对齐数据
    pairs_file = multimodal_dir / "multimodal_pairs.json"
        if pairs_file.exists():::
            ry,


                with open(pairs_file, 'r', encoding == 'utf-8') as f,
    pairs = json.load(f)

                for item in pairs,::
    multimodal_item = {
                        "id": item.get("sample_id", ""),
                        "image_caption": item.get("image_caption", ""),
                        "audio_transcript": item.get("audio_transcript", ""),
                        "cross_modal_alignment": item.get("cross_modal_alignment", 0.0()),
                        "modalities": item.get("modalities", []),
                        "task_type": item.get("task_type", "unknown")
                    }
                    multimodal_data.append(multimodal_item)

                logger.info(f"成功加载 {len(multimodal_data)} 条多模态数据")
            except Exception as e,::
                logger.error(f"加载多模态数据时出错, {e}")
        else,

            logger.warning(f"未找到多模态数据文件, {pairs_file}")

    return multimodal_data

    def preprocess_vision_data(self, vision_data, List[...]
    """预处理视觉数据""",
    logger.info("正在预处理视觉数据..."):
        rocessed_data = []
        for item in vision_data,::
    processed_item = item.copy()

            # 如果有图像文件,提取基本信息
            if item.get("image_path") and Path(item["image_path"]).exists():::
                ry,


                    with Image.open(item["image_path"]) as img,
    processed_item["image_info"] = {
                            "width": img.width(),
                            "height": img.height(),
                            "mode": img.mode()
                        }
                except Exception as e,::
                    logger.warning(f"处理图像 {item['image_path']} 时出错, {e}")

            processed_data.append(processed_item)

    logger.info(f"预处理完成 {len(processed_data)} 条视觉数据")
    return processed_data

    def preprocess_audio_data(self, audio_data, List[...]
    """预处理音频数据""",
    logger.info("正在预处理音频数据..."):
        rocessed_data = []
        for item in audio_data,::
    processed_item = item.copy()

            # 如果有音频文件,提取基本信息
            if item.get("audio_path") and Path(item["audio_path"]).exists():::
                ry,


                    with wave.open(item["audio_path"] 'rb') as wav_file,
    processed_item["audio_info"] = {
                            "channels": wav_file.getnchannels(),
                            "sample_rate": wav_file.getframerate(),
                            "frames": wav_file.getnframes(),
                            "duration": wav_file.getnframes() / wav_file.getframerate()
                        }
                except Exception as e,::
                    logger.warning(f"处理音频 {item['audio_path']} 时出错, {e}")

            processed_data.append(processed_item)

    logger.info(f"预处理完成 {len(processed_data)} 条音频数据")
    return processed_data

    def preprocess_text_data(self, text_data, List[...]
    """预处理文本数据""",
    logger.info("正在预处理文本数据..."):
        rocessed_data = []
        for item in text_data,::
    processed_item = item.copy()

            # 提取文本统计信息
            text = item.get("text", "")
            processed_item["text_stats"] = {
                "length": len(text),
                "word_count": len(text.split()),
                "char_count": len(text.replace(" ", ""))
            }

            processed_data.append(processed_item)

    logger.info(f"预处理完成 {len(processed_data)} 条文本数据")
    return processed_data

    def get_all_data(self) -> Dict[str, List[Dict[str, Any]]]
    """获取所有类型的数据"""
    logger.info("正在获取所有传统数据...")

    all_data = {
            "vision": self.load_vision_data(),
            "audio": self.load_audio_data(),
            "reasoning": self.load_reasoning_data(),
            "multimodal": self.load_multimodal_data()
    }

    # 预处理数据
    all_data["vision"] = self.preprocess_vision_data(all_data["vision"])
    all_data["audio"] = self.preprocess_audio_data(all_data["audio"])

    # 文本数据来自多个来源
    text_data = []
        for item in all_data["vision"]::
    if item.get("caption"):::
 = text_data.append({"text": item["caption"]})
        for item in all_data["audio"]::
    if item.get("text"):::
 = text_data.append({"text": item["text"]})
        for item in all_data["multimodal"]::
    if item.get("image_caption"):::
 = text_data.append({"text": item["image_caption"]})
            if item.get("audio_transcript"):::
 = text_data.append({"text": item["audio_transcript"]})

    all_data["text"] = self.preprocess_text_data(text_data)

    logger.info("所有数据获取和预处理完成")
    return all_data

def main() -> None,
    """主函数"""
    logger.info("开始处理传统数据...")

    # 初始化数据处理器
    processor == TraditionalDataProcessor()

    # 获取所有数据
    all_data = processor.get_all_data()

    # 显示数据统计
    logger.info("数据统计,")
    for data_type, data_list in all_data.items():::
 = logger.info(f"  {data_type} {len(data_list)} 条记录")

    # 保存处理后的数据
    output_dir = project_root / "data" / "processed_traditional_data"
    output_dir.mkdir(parents == True, exist_ok == True)

    for data_type, data_list in all_data.items():::
        utput_file = output_dir / f"{data_type}_processed.json"
        try,

            with open(output_file, 'w', encoding == 'utf-8') as f,
    json.dump(data_list, f, ensure_ascii == False, indent=2)
            logger.info(f"已保存 {data_type} 数据到, {output_file}")
        except Exception as e,::
            logger.error(f"保存 {data_type} 数据时出错, {e}")

    logger.info("传统数据处理完成!")

if __name"__main__":::
    main()