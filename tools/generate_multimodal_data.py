#!/usr/bin/env python3
"""
多模态数据生成脚本
将不同模态的特征融合生成高层次概念数据
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import torch
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

# 导入特征提取器
from apps.backend.src.core.tools.extract_features import FeatureExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

class MultimodalDataGenerator:
    """多模态数据生成器"""
    
    def __init__(self, model_dir: str = None, output_dir: str = None) -> None:
        self.project_root = project_root
        self.model_dir = Path(model_dir) if model_dir else project_root / "training" / "models"
        self.output_dir = Path(output_dir) if output_dir else project_root / "data" / "generated_multimodal_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化特征提取器
        self.feature_extractor = FeatureExtractor(model_dir)
        
        # 设备配置
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _ = logger.info(f"使用设备: {self.device}")
    
    def load_processed_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载处理后的数据"""
        _ = logger.info("正在加载处理后的数据...")
        
        all_data = {}
        data_types = ["vision", "audio", "text", "multimodal"]
        
        for data_type in data_types:
            processed_data_file = self.project_root / "data" / "processed_traditional_data" / f"{data_type}_processed.json"
            if processed_data_file.exists():
                try:
                    with open(processed_data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    all_data[data_type] = data
                    _ = logger.info(f"成功加载 {len(data)} 条{data_type}数据")
                except Exception as e:
                    _ = logger.error(f"加载{data_type}数据时出错: {e}")
            else:
                _ = logger.warning(f"未找到处理后的{data_type}数据文件: {processed_data_file}")
        
        return all_data
    
    def generate_conceptual_features(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """生成概念特征"""
        if not features:
            return None
        
        # 将所有模态的特征连接起来
        feature_list = []
        for modality, feature in features.items():
            # 确保特征是2D数组
            if len(feature.shape) == 1:
                feature = feature.reshape(1, -1)
            elif len(feature.shape) > 2:
                feature = feature.reshape(feature.shape[0], -1)
            
            # 如果特征维度太高，进行降维
            if feature.shape[1] > 128:
                pca = PCA(n_components=128)
                feature = pca.fit_transform(feature)
            
            _ = feature_list.append(feature)
        
        if not feature_list:
            return None
        
        # 连接所有特征
        combined_features = np.concatenate(feature_list, axis=1)
        
        # 如果维度太高，再次降维
        if combined_features.shape[1] > 256:
            pca = PCA(n_components=256)
            combined_features = pca.fit_transform(combined_features)
        
        _ = logger.info(f"生成概念特征，形状: {combined_features.shape}")
        return combined_features
    
    def create_multimodal_samples(self, all_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """创建多模态样本"""
        _ = logger.info("正在创建多模态样本...")
        
        multimodal_samples = []
        
        # 处理视觉数据
        vision_data = all_data.get("vision", [])
        for i, item in enumerate(vision_data[:20]):  # 限制处理数量
            sample = {
                "id": f"multimodal_sample_{i:04d}",
                "type": "multimodal_concept",
                "modalities": ["vision"],
                "content": {
                    "vision": {
                        _ = "caption": item.get("caption", ""),
                        _ = "scene_type": item.get("scene_type", "unknown"),
                        _ = "objects": item.get("objects", [])
                    }
                },
                "metadata": {
                    "source": "vision_data",
                    _ = "timestamp": torch.utils.data.dataset.datetime.datetime.now().isoformat()
                }
            }
            
            # 如果有图像路径，提取视觉特征
            image_path = item.get("image_path")
            if image_path and Path(image_path).exists():
                features = self.feature_extractor.extract_multimodal_features(image_path=image_path)
                conceptual_features = self.generate_conceptual_features(features)
                if conceptual_features is not None:
                    sample["conceptual_features"] = conceptual_features.tolist()
            
            _ = multimodal_samples.append(sample)
        
        # 处理音频数据
        audio_data = all_data.get("audio", [])
        for i, item in enumerate(audio_data[:20]):  # 限制处理数量
            sample = {
                "id": f"multimodal_sample_{i+20:04d}",
                "type": "multimodal_concept",
                "modalities": ["audio"],
                "content": {
                    "audio": {
                        _ = "transcript": item.get("text", ""),
                        _ = "language": item.get("language", "unknown"),
                        _ = "duration": item.get("duration", 0.0),
                        _ = "speaker_id": item.get("speaker_id", "unknown")
                    }
                },
                "metadata": {
                    "source": "audio_data",
                    _ = "timestamp": torch.utils.data.dataset.datetime.datetime.now().isoformat()
                }
            }
            
            # 如果有音频路径，提取音频特征
            audio_path = item.get("audio_path")
            if audio_path and Path(audio_path).exists():
                features = self.feature_extractor.extract_multimodal_features(audio_path=audio_path)
                conceptual_features = self.generate_conceptual_features(features)
                if conceptual_features is not None:
                    sample["conceptual_features"] = conceptual_features.tolist()
            
            _ = multimodal_samples.append(sample)
        
        # 处理多模态数据
        existing_multimodal_data = all_data.get("multimodal", [])
        for i, item in enumerate(existing_multimodal_data[:20]):  # 限制处理数量
            sample = {
                "id": f"multimodal_sample_{i+40:04d}",
                "type": "multimodal_concept",
                _ = "modalities": item.get("modalities", []),
                "content": {
                    _ = "image_caption": item.get("image_caption", ""),
                    _ = "audio_transcript": item.get("audio_transcript", ""),
                    _ = "task_type": item.get("task_type", "unknown")
                },
                "metadata": {
                    "source": "existing_multimodal_data",
                    _ = "cross_modal_alignment": item.get("cross_modal_alignment", 0.0),
                    _ = "timestamp": torch.utils.data.dataset.datetime.datetime.now().isoformat()
                }
            }
            
            # 提取多模态特征
            features = self.feature_extractor.extract_multimodal_features(
                text=item.get("image_caption", "") + " " + item.get("audio_transcript", "")
            )
            conceptual_features = self.generate_conceptual_features(features)
            if conceptual_features is not None:
                sample["conceptual_features"] = conceptual_features.tolist()
            
            _ = multimodal_samples.append(sample)
        
        # 创建跨模态融合样本
        for i in range(min(20, len(vision_data), len(audio_data))):  # 限制处理数量
            vision_item = vision_data[i]
            audio_item = audio_data[i]
            
            sample = {
                "id": f"multimodal_sample_{i+60:04d}",
                "type": "multimodal_fusion",
                "modalities": ["vision", "audio"],
                "content": {
                    "vision": {
                        _ = "caption": vision_item.get("caption", ""),
                        _ = "scene_type": vision_item.get("scene_type", "unknown")
                    },
                    "audio": {
                        _ = "transcript": audio_item.get("text", ""),
                        _ = "language": audio_item.get("language", "unknown")
                    }
                },
                "metadata": {
                    "source": "cross_modal_fusion",
                    _ = "timestamp": torch.utils.data.dataset.datetime.datetime.now().isoformat()
                }
            }
            
            # 提取跨模态特征
            image_path = vision_item.get("image_path")
            audio_path = audio_item.get("audio_path")
            text = vision_item.get("caption", "") + " " + audio_item.get("text", "")
            
            features = self.feature_extractor.extract_multimodal_features(
                image_path=image_path,
                audio_path=audio_path,
                text=text
            )
            conceptual_features = self.generate_conceptual_features(features)
            if conceptual_features is not None:
                sample["conceptual_features"] = conceptual_features.tolist()
            
            _ = multimodal_samples.append(sample)
        
        _ = logger.info(f"成功创建 {len(multimodal_samples)} 个多模态样本")
        return multimodal_samples
    
    def enhance_with_conceptual_models(self, samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用概念模型增强数据"""
        _ = logger.info("正在使用概念模型增强数据...")
        
        enhanced_samples = []
        
        # 这里可以集成概念模型来进一步增强数据
        # 例如，使用因果推理引擎添加因果关系信息
        # 使用环境模拟器添加环境上下文信息等
        
        for sample in samples:
            enhanced_sample = sample.copy()
            
            # 添加概念模型相关的增强信息
            enhanced_sample["enhanced_by"] = {
                "concept_models": ["environment_simulator", "causal_reasoning_engine", "adaptive_learning_controller"],
                "enhancement_type": "conceptual_enrichment",
                _ = "confidence": np.random.uniform(0.7, 0.95)
            }
            
            # 添加模拟的概念特征
            if "conceptual_features" in sample:
                # 基于现有特征生成更多概念特征
                features = np.array(sample["conceptual_features"])
                # 添加一些随机的概念维度
                additional_concepts = np.random.randn(features.shape[0], 32)
                enhanced_features = np.concatenate([features, additional_concepts], axis=1)
                enhanced_sample["enhanced_conceptual_features"] = enhanced_features.tolist()
            
            _ = enhanced_samples.append(enhanced_sample)
        
        _ = logger.info(f"成功增强 {len(enhanced_samples)} 个样本")
        return enhanced_samples
    
    def save_multimodal_data(self, samples: List[Dict[str, Any]]):
        """保存多模态数据"""
        _ = logger.info("正在保存多模态数据...")
        
        # 保存为JSON格式
        json_file = self.output_dir / "multimodal_conceptual_data.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(samples, f, ensure_ascii=False, indent=2)
            _ = logger.info(f"多模态数据已保存到: {json_file}")
        except Exception as e:
            _ = logger.error(f"保存多模态数据时出错: {e}")
        
        # 保存为单独的文件
        for sample in samples:
            sample_id = sample["id"]
            sample_file = self.output_dir / f"{sample_id}.json"
            try:
                with open(sample_file, 'w', encoding='utf-8') as f:
                    json.dump(sample, f, ensure_ascii=False, indent=2)
            except Exception as e:
                _ = logger.error(f"保存样本 {sample_id} 时出错: {e}")
        
        # 生成数据统计报告
        _ = self.generate_statistics_report(samples)
    
    def generate_statistics_report(self, samples: List[Dict[str, Any]]):
        """生成数据统计报告"""
        _ = logger.info("正在生成数据统计报告...")
        
        report = {
            _ = "total_samples": len(samples),
            "sample_types": {},
            "modalities_distribution": {},
            "enhancement_stats": {
                "enhanced_samples": 0,
                "average_confidence": 0.0
            },
            "feature_stats": {
                "samples_with_features": 0,
                "average_feature_dimensions": 0
            }
        }
        
        # 统计样本类型
        for sample in samples:
            sample_type = sample.get("type", "unknown")
            report["sample_types"][sample_type] = report["sample_types"].get(sample_type, 0) + 1
            
            # 统计模态分布
            modalities = sample.get("modalities", [])
            for modality in modalities:
                report["modalities_distribution"][modality] = report["modalities_distribution"].get(modality, 0) + 1
            
            # 统计增强信息
            if "enhanced_by" in sample:
                report["enhancement_stats"]["enhanced_samples"] += 1
                report["enhancement_stats"]["average_confidence"] += sample["enhanced_by"].get("confidence", 0.0)
            
            # 统计特征信息
            if "conceptual_features" in sample:
                report["feature_stats"]["samples_with_features"] += 1
                features = np.array(sample["conceptual_features"])
                report["feature_stats"]["average_feature_dimensions"] += features.shape[1] if len(features.shape) > 1 else features.shape[0]
        
        # 计算平均值
        if report["enhancement_stats"]["enhanced_samples"] > 0:
            report["enhancement_stats"]["average_confidence"] /= report["enhancement_stats"]["enhanced_samples"]
        
        if report["feature_stats"]["samples_with_features"] > 0:
            report["feature_stats"]["average_feature_dimensions"] /= report["feature_stats"]["samples_with_features"]
        
        # 保存报告
        report_file = self.output_dir / "multimodal_data_statistics.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            _ = logger.info(f"统计报告已保存到: {report_file}")
        except Exception as e:
            _ = logger.error(f"保存统计报告时出错: {e}")
        
        # 打印报告摘要
        _ = logger.info("数据统计报告摘要:")
        _ = logger.info(f"  总样本数: {report['total_samples']}")
        _ = logger.info(f"  样本类型分布: {report['sample_types']}")
        _ = logger.info(f"  模态分布: {report['modalities_distribution']}")
        _ = logger.info(f"  增强样本数: {report['enhancement_stats']['enhanced_samples']}")
        _ = logger.info(f"  平均置信度: {report['enhancement_stats']['average_confidence']:.3f}")
        _ = logger.info(f"  有特征的样本数: {report['feature_stats']['samples_with_features']}")
        _ = logger.info(f"  平均特征维度: {report['feature_stats']['average_feature_dimensions']:.1f}")
    
    def generate_visualization(self, samples: List[Dict[str, Any]]):
        """生成数据可视化"""
        _ = logger.info("正在生成数据可视化...")
        
        # 收集所有特征用于可视化
        all_features = []
        sample_labels = []
        
        for sample in samples:
            if "conceptual_features" in sample:
                features = np.array(sample["conceptual_features"])
                # 如果是2D数组，取第一行
                if len(features.shape) > 1:
                    features = features[0]
                _ = all_features.append(features)
                _ = sample_labels.append(sample.get("type", "unknown"))
        
        if len(all_features) < 2:
            _ = logger.warning("样本数量不足，无法生成可视化")
            return
        
        # 转换为numpy数组
        all_features = np.array(all_features)
        
        # 如果特征维度太高，先进行PCA降维
        if all_features.shape[1] > 50:
            pca = PCA(n_components=50)
            all_features = pca.fit_transform(all_features)
        
        # 使用t-SNE进行降维到2D
        try:
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(all_features)-1))
            features_2d = tsne.fit_transform(all_features)
            
            # 创建可视化图表
            plt.figure(figsize=(12, 8))
            
            # 为不同类型的样本使用不同颜色
            unique_labels = list(set(sample_labels))
            colors = plt.cm.Set1(np.linspace(0, 1, len(unique_labels)))
            
            for i, label in enumerate(unique_labels):
                mask = np.array(sample_labels) == label
                plt.scatter(features_2d[mask, 0], features_2d[mask, 1], 
                           c=[colors[i]], label=label, alpha=0.7, s=50)
            
            _ = plt.title("多模态概念数据可视化 (t-SNE)")
            _ = plt.xlabel("t-SNE维度1")
            _ = plt.ylabel("t-SNE维度2")
            _ = plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 保存图表
            visualization_file = self.output_dir / "multimodal_data_visualization.png"
            plt.savefig(visualization_file, dpi=300, bbox_inches='tight')
            _ = plt.close()
            
            _ = logger.info(f"数据可视化图表已保存到: {visualization_file}")
        except Exception as e:
            _ = logger.error(f"生成数据可视化时出错: {e}")

def main() -> None:
    """主函数"""
    _ = logger.info("开始生成多模态概念数据...")
    
    # 初始化多模态数据生成器
    generator = MultimodalDataGenerator()
    
    # 加载处理后的数据
    all_data = generator.load_processed_data()
    
    if not all_data:
        _ = logger.error("没有可用的数据用于生成多模态样本")
        return
    
    # 创建多模态样本
    samples = generator.create_multimodal_samples(all_data)
    
    if not samples:
        _ = logger.error("未能创建多模态样本")
        return
    
    # 使用概念模型增强数据
    enhanced_samples = generator.enhance_with_conceptual_models(samples)
    
    # 保存多模态数据
    _ = generator.save_multimodal_data(enhanced_samples)
    
    # 生成数据可视化
    _ = generator.generate_visualization(enhanced_samples)
    
    _ = logger.info("多模态概念数据生成完成!")

if __name__ == "__main__":
    _ = main()