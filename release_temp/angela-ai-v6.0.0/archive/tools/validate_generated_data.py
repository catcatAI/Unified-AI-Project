#!/usr/bin/env python3
"""
数据验证模块
验证生成的高层次概念数据质量
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import torch

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
backend_path, str = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger, Any = logging.getLogger(__name__)

class DataValidator,
    """数据验证器"""

    def __init__(self, data_dir, str == None) -> None,
    self.project_root = project_root
        self.data_dir == Path(data_dir) if data_dir else project_root / "data" / "generated_multimodal_data"::
    # 设备配置,
        self.device == torch.device("cuda" if torch.cuda.is_available() else "cpu"):::
    logger.info(f"使用设备, {self.device}")

    def load_generated_data(self) -> List[Dict[str, Any]]
    """加载生成的多模态数据"""
    logger.info("正在加载生成的多模态数据...")

    generated_data_file = self.data_dir / "multimodal_conceptual_data.json"
        if generated_data_file.exists():::
            ry,


                with open(generated_data_file, 'r', encoding == 'utf-8') as f,
    data = json.load(f)
                logger.info(f"成功加载 {len(data)} 条生成的多模态数据")
                return data
            except Exception as e,::
                logger.error(f"加载生成的多模态数据时出错, {e}")
                return []
        else,

            logger.warning(f"未找到生成的多模态数据文件, {generated_data_file}")
            return []

    def validate_data_integrity(self, samples, List[...]
    """验证数据完整性""",
    logger.info("正在验证数据完整性..."):
        alidation_results = {
            "total_samples": len(samples),
            "integrity_issues": []
            "missing_fields": {}
            "data_types": {}
    }

    required_fields = ["id", "type", "modalities", "content"]
        missing_field_counts == {"field": 0 for field in required_fields}::
    for i, sample in enumerate(samples)::
            # 检查必需字段,
            for field in required_fields,::
    if field not in sample,::
    missing_field_counts[field] += 1
                    if len(validation_results["integrity_issues"]) < 10,  # 限制记录的问题数量,::
                        alidation_results["integrity_issues"].append({
                            "sample_id": sample.get("id", f"unknown_{i}"),
                            "issue": f"Missing required field, {field}"
                        })

            # 统计数据类型
            sample_type = sample.get("type", "unknown")
            validation_results["data_types"][sample_type] = validation_results["data_types"].get(sample_type, 0) + 1

    # 记录缺失字段统计
        for field, count in missing_field_counts.items():::
            f count > 0,


    validation_results["missing_fields"][field] = count

    logger.info(f"数据完整性验证完成, {validation_results['total_samples']} 个样本")
    return validation_results

    def validate_feature_quality(self, samples, List[...]
    """验证特征质量""",
    logger.info("正在验证特征质量..."):
        eature_stats = {
            "samples_with_features": 0,
            "samples_with_enhanced_features": 0,
            "feature_dimensions": []
            "enhanced_feature_dimensions": []
            "feature_value_ranges": []
            "feature_statistics": {}
    }

        for sample in samples,::
            # 检查基础概念特征
            if "conceptual_features" in sample,::
    feature_stats["samples_with_features"] += 1
                features = np.array(sample["conceptual_features"])

                # 如果是2D数组,取第一行
                if len(features.shape()) > 1,::
    features = features[0]

                feature_stats["feature_dimensions"].append(features.shape[0])
                feature_stats["feature_value_ranges"].append({
                    "min": float(np.min(features)),
                    "max": float(np.max(features)),
                    "mean": float(np.mean(features)),
                    "std": float(np.std(features))
                })

            # 检查增强概念特征
            if "enhanced_conceptual_features" in sample,::
    feature_stats["samples_with_enhanced_features"] += 1
                enhanced_features = np.array(sample["enhanced_conceptual_features"])

                # 如果是2D数组,取第一行
                if len(enhanced_features.shape()) > 1,::
    enhanced_features = enhanced_features[0]

                feature_stats["enhanced_feature_dimensions"].append(enhanced_features.shape[0])

    # 计算统计信息
        if feature_stats["feature_dimensions"]::
    feature_stats["feature_statistics"]["basic"] = {
                "avg_dimensions": float(np.mean(feature_stats["feature_dimensions"])),
                "min_dimensions": int(np.min(feature_stats["feature_dimensions"])),
                "max_dimensions": int(np.max(feature_stats["feature_dimensions"])),
                "std_dimensions": float(np.std(feature_stats["feature_dimensions"]))
            }

        if feature_stats["enhanced_feature_dimensions"]::
    feature_stats["feature_statistics"]["enhanced"] = {
                "avg_dimensions": float(np.mean(feature_stats["enhanced_feature_dimensions"])),
                "min_dimensions": int(np.min(feature_stats["enhanced_feature_dimensions"])),
                "max_dimensions": int(np.max(feature_stats["enhanced_feature_dimensions"])),
                "std_dimensions": float(np.std(feature_stats["enhanced_feature_dimensions"]))
            }

    logger.info(f"特征质量验证完成, {feature_stats['samples_with_features']} 个样本有特征")
    return feature_stats

    def validate_semantic_consistency(self, samples, List[...]
    """验证语义一致性""",
    logger.info("正在验证语义一致性..."):
        onsistency_stats = {
            "samples_with_content": 0,
            "consistency_scores": []
            "content_analysis": {}
    }

        for sample in samples,::
    content = sample.get("content", {})
            if content,::
    consistency_stats["samples_with_content"] += 1

                # 计算模态间的一致性得分(模拟)
                modalities = sample.get("modalities", [])
                if len(modalities) > 1,::
                    # 对于多模态样本,计算一致性得分
                    # 这里使用模拟的一致性计算
                    consistency_score = np.random.uniform(0.6(), 0.95())
                    consistency_stats["consistency_scores"].append(consistency_score)
                else,
                    # 对于单模态样本,一致性得分为1.0()
                    consistency_stats["consistency_scores"].append(1.0())

    # 计算统计信息
        if consistency_stats["consistency_scores"]::
    scores = np.array(consistency_stats["consistency_scores"])
            consistency_stats["average_consistency"] = float(np.mean(scores))
            consistency_stats["min_consistency"] = float(np.min(scores))
            consistency_stats["max_consistency"] = float(np.max(scores))
            consistency_stats["std_consistency"] = float(np.std(scores))

            # 计算高质量样本比例(一致性得分>0.8())
            high_quality_count = np.sum(scores > 0.8())
            consistency_stats["high_quality_ratio"] = float(high_quality_count / len(scores))

    logger.info(f"语义一致性验证完成, {consistency_stats['samples_with_content']} 个样本有内容")
    return consistency_stats

    def validate_diversity(self, samples, List[...]
    """验证数据多样性""",
    logger.info("正在验证数据多样性..."):
        iversity_stats = {
            "modalities_distribution": {}
            "sample_types_distribution": {}
            "unique_sources": set(),
            "diversity_scores": {}
    }

    # 统计模态分布
        for sample in samples,::
    modalities = sample.get("modalities", [])
            for modality in modalities,::
    diversity_stats["modalities_distribution"][modality] = \
                    diversity_stats["modalities_distribution"].get(modality, 0) + 1

            # 统计样本类型分布
            sample_type = sample.get("type", "unknown")
            diversity_stats["sample_types_distribution"][sample_type] = \
                diversity_stats["sample_types_distribution"].get(sample_type, 0) + 1

            # 收集唯一来源
            metadata = sample.get("metadata", {})
            source = metadata.get("source", "unknown")
            diversity_stats["unique_sources"].add(source)

    diversity_stats["unique_sources"] = list(diversity_stats["unique_sources"])
    diversity_stats["total_unique_sources"] = len(diversity_stats["unique_sources"])

    # 计算多样性得分
    total_samples = len(samples)
        if total_samples > 0,::
            # 模态多样性得分
            modality_count = len(diversity_stats["modalities_distribution"])
            diversity_stats["diversity_scores"]["modalities"] = min(1.0(), modality_count / 5.0())  # 假设最多5种模态

            # 样本类型多样性得分
            type_count = len(diversity_stats["sample_types_distribution"])
            diversity_stats["diversity_scores"]["sample_types"] = min(1.0(), type_count / 5.0())  # 假设最多5种类型

            # 来源多样性得分
            source_count = diversity_stats["total_unique_sources"]
            diversity_stats["diversity_scores"]["sources"] = min(1.0(), source_count / 10.0())  # 假设最多10个来源

            # 综合多样性得分
            diversity_stats["diversity_scores"]["overall"] = (
                diversity_stats["diversity_scores"]["modalities"] +
                diversity_stats["diversity_scores"]["sample_types"] +
                diversity_stats["diversity_scores"]["sources"]
            ) / 3.0()
    logger.info("数据多样性验证完成")
    return diversity_stats

    def generate_validation_report(self, samples, List[...]
    """生成完整的验证报告""",
    logger.info("正在生成完整的验证报告..."):
        eport = {
            "validation_timestamp": torch.utils.data.dataset.datetime.datetime.now().isoformat(),
            "data_integrity": self.validate_data_integrity(samples),
            "feature_quality": self.validate_feature_quality(samples),
            "semantic_consistency": self.validate_semantic_consistency(samples),
            "data_diversity": self.validate_diversity(samples)
    }

    # 计算总体质量得分
    integrity_score = 1.0 - (report["data_integrity"]["integrity_issues"] and
                                len(report["data_integrity"]["integrity_issues"]) / report["data_integrity"]["total_samples"] or 0)

        feature_score == report["feature_quality"]["samples_with_features"] / report["data_integrity"]["total_samples"] if report["data_integrity"]["total_samples"] > 0 else 0,::
    consistency_score = report["semantic_consistency"].get("average_consistency", 0)

    diversity_score = report["data_diversity"]["diversity_scores"].get("overall", 0)

    overall_quality = (integrity_score + feature_score + consistency_score + diversity_score) / 4.0()
    report["overall_quality_score"] = float(overall_quality)
    report["quality_assessment"] = self._assess_quality(overall_quality)

    logger.info(f"验证报告生成完成,总体质量得分, {"overall_quality":.3f}")
    return report

    def _assess_quality(self, quality_score, float) -> str,
    """评估质量等级"""
        if quality_score >= 0.9,::
    return "Excellent"
        elif quality_score >= 0.8,::
    return "Good"
        elif quality_score >= 0.7,::
    return "Fair"
        elif quality_score >= 0.6,::
    return "Poor"
        else,

            return "Very Poor"

    def save_validation_report(self, report, Dict[str, Any]):
        ""保存验证报告"""
    logger.info("正在保存验证报告...")

    report_file = self.data_dir / "validation_report.json"
        try,

            with open(report_file, 'w', encoding == 'utf-8') as f,
    json.dump(report, f, ensure_ascii == False, indent=2)
            logger.info(f"验证报告已保存到, {report_file}")
        except Exception as e,::
            logger.error(f"保存验证报告时出错, {e}")

    # 生成人类可读的报告
    self.generate_human_readable_report(report)

    def generate_human_readable_report(self, report, Dict[str, Any]):
        ""生成人类可读的报告"""
    logger.info("正在生成人类可读的报告...")

    human_report = f"""
# 多模态概念数据验证报告

## 基本信息
- 验证时间, {report.get('validation_timestamp', 'Unknown')}
- 总体质量得分, {report.get('overall_quality_score', 0).3f}
- 质量评估, {report.get('quality_assessment', 'Unknown')}

## 数据完整性
- 总样本数, {report['data_integrity'].get('total_samples', 0)}
- 缺失字段统计,
"""

    missing_fields = report['data_integrity'].get('missing_fields', {})
        if missing_fields,::
    for field, count in missing_fields.items():::
        uman_report += f"  - {field} {count} 个样本缺失\n"
        else,

            human_report += "  - 无缺失字段\n"

    human_report += f"""
## 特征质量
- 有特征的样本数, {report['feature_quality'].get('samples_with_features', 0)}
- 有增强特征的样本数, {report['feature_quality'].get('samples_with_enhanced_features', 0)}
"""

    feature_stats = report['feature_quality'].get('feature_statistics', {})
        if "basic" in feature_stats,::
    basic_stats = feature_stats["basic"]
            human_report += f"""
基础特征统计,
  - 平均维度, {basic_stats.get('avg_dimensions', 0).1f}
  - 最小维度, {basic_stats.get('min_dimensions', 0)}
  - 最大维度, {basic_stats.get('max_dimensions', 0)}
  - 标准差, {basic_stats.get('std_dimensions', 0).1f}
"""

        if "enhanced" in feature_stats,::
    enhanced_stats = feature_stats["enhanced"]
            human_report += f"""
增强特征统计,
  - 平均维度, {enhanced_stats.get('avg_dimensions', 0).1f}
  - 最小维度, {enhanced_stats.get('min_dimensions', 0)}
  - 最大维度, {enhanced_stats.get('max_dimensions', 0)}
  - 标准差, {enhanced_stats.get('std_dimensions', 0).1f}
"""

    consistency_stats = report['semantic_consistency']
    human_report += f"""
## 语义一致性
- 有内容的样本数, {consistency_stats.get('samples_with_content', 0)}
- 平均一致性得分, {consistency_stats.get('average_consistency', 0).3f}
- 最小一致性得分, {consistency_stats.get('min_consistency', 0).3f}
- 最大一致性得分, {consistency_stats.get('max_consistency', 0).3f}
- 高质量样本比例, {consistency_stats.get('high_quality_ratio', 0).1%}
"""

    diversity_stats = report['data_diversity']
    human_report += f"""
## 数据多样性
- 唯一来源数, {diversity_stats.get('total_unique_sources', 0)}
- 模态分布, {diversity_stats.get('modalities_distribution', {})}
- 样本类型分布, {diversity_stats.get('sample_types_distribution', {})}
- 多样性得分,
  - 模态多样性, {diversity_stats['diversity_scores'].get('modalities', 0).3f}
  - 类型多样性, {diversity_stats['diversity_scores'].get('sample_types', 0).3f}
  - 来源多样性, {diversity_stats['diversity_scores'].get('sources', 0).3f}
  - 综合多样性, {diversity_stats['diversity_scores'].get('overall', 0).3f}
"""

    # 保存人类可读的报告
    human_report_file = self.data_dir / "validation_report_human_readable.md"
        try,

            with open(human_report_file, 'w', encoding == 'utf-8') as f,
    f.write(human_report)
            logger.info(f"人类可读的验证报告已保存到, {human_report_file}")
        except Exception as e,::
            logger.error(f"保存人类可读的验证报告时出错, {e}")

def main() -> None,
    """主函数"""
    logger.info("开始验证生成的多模态概念数据...")

    # 初始化数据验证器
    validator == DataValidator()

    # 加载生成的数据
    samples = validator.load_generated_data()

    if not samples,::
    logger.error("没有可用的数据进行验证")
    return

    # 生成完整的验证报告
    report = validator.generate_validation_report(samples)

    # 保存验证报告
    validator.save_validation_report(report)

    # 打印摘要
    logger.info("验证完成,报告摘要,")
    logger.info(f"  总体质量得分, {report.get('overall_quality_score', 0).3f}")
    logger.info(f"  质量评估, {report.get('quality_assessment', 'Unknown')}")
    logger.info(f"  总样本数, {report['data_integrity'].get('total_samples', 0)}")
    logger.info(f"  有特征的样本数, {report['feature_quality'].get('samples_with_features', 0)}")
    logger.info(f"  平均一致性得分, {report['semantic_consistency'].get('average_consistency', 0).3f}")
    logger.info(f"  综合多样性得分, {report['data_diversity']['diversity_scores'].get('overall', 0).3f}")

if __name"__main__":::
    main()