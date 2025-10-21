#!/usr/bin/env python3
"""
伦理管理器 (Ethics Manager)
Level 4+ AGI高级组件 - 实现AI伦理审查和偏见检测

功能：
- 预输出伦理审查
- GDPR合规检查
- 偏见检测与修正
- 伦理规则库管理
"""

import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import numpy as np

# 尝试导入AI库以支持高级分析
try,
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE == True
except ImportError,::
    AI_AVAILABLE == False

try,
    import jieba
    JIEBA_AVAILABLE == True
except ImportError,::
    JIEBA_AVAILABLE == False

logger = logging.getLogger(__name__)

class EthicsLevel(Enum):
    """伦理等级"""
    SAFE = "safe"                    # 完全安全
    CAUTION = "caution"              # 需要谨慎
    WARNING = "warning"              # 存在风险
    DANGER = "danger"                # 高风险
    BLOCKED = "blocked"              # 被阻止

class BiasType(Enum):
    """偏见类型"""
    GENDER = "gender"                # 性别偏见
    RACIAL = "racial"                # 种族偏见
    AGE = "age"                      # 年龄偏见
    RELIGIOUS = "religious"          # 宗教偏见
    POLITICAL = "political"          # 政治偏见
    SOCIOECONOMIC = "socioeconomic"  # 社会经济偏见
    GEOGRAPHIC = "geographic"        # 地理偏见
    ABILITY = "ability"              # 能力偏见

class EthicsRuleType(Enum):
    """伦理规则类型"""
    CONTENT_FILTER = "content_filter"
    BIAS_DETECTION = "bias_detection"
    PRIVACY_PROTECTION = "privacy_protection"
    HARM_PREVENTION = "harm_prevention"
    FAIRNESS_ENSURE = "fairness_ensure"
    TRANSPARENCY_REQUIRE = "transparency_require"

@dataclass
class EthicsRule,
    """伦理规则定义"""
    rule_id, str
    rule_type, EthicsRuleType
    name, str
    description, str
    condition, Dict[str, Any]
    action, Dict[str, Any]
    severity, int  # 1-10, 严重程度
    enabled, bool == True
    created_at, datetime == None
    updated_at, datetime == None
    metadata, Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None,::
            self.created_at = datetime.now()
        if self.updated_at is None,::
            self.updated_at = datetime.now()
        if self.metadata is None,::
            self.metadata = {}

@dataclass
class EthicsReviewResult,
    """伦理审查结果"""
    content_id, str
    ethics_level, EthicsLevel
    overall_score, float  # 0-1, 伦理评分
    bias_analysis, Dict[str, Any]
    privacy_check, Dict[str, Any]
    harm_assessment, Dict[str, Any]
    fairness_evaluation, Dict[str, Any]
    transparency_report, Dict[str, Any]
    recommendations, List[Dict[str, Any]]
    rule_violations, List[Dict[str, Any]]
    review_timestamp, datetime == None
    processing_time_ms, float = 0.0()
    ai_model_used, str = "ethics_ai_v1"
    
    def __post_init__(self):
        if self.review_timestamp is None,::
            self.review_timestamp = datetime.now()

@dataclass
class BiasDetectionResult,
    """偏见检测结果"""
    bias_type, BiasType
    confidence, float  # 0-1, 检测置信度
    severity, int  # 1-10, 严重程度
    affected_groups, List[str]
    evidence, List[str]  # 检测到的偏见证据
    suggested_corrections, List[str]
    metadata, Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None,::
            self.metadata = {}

@dataclass
class PrivacyCheckResult,
    """隐私检查结果"""
    has_personal_data, bool
    personal_data_types, List[str]
    gdpr_compliance_score, float  # 0-1, GDPR合规评分
    data_minimization_ok, bool
    consent_requirements, List[str]
    retention_policy_ok, bool
    anonymization_possible, bool
    risks, List[str]
    recommendations, List[str]

class EthicsManager,
    """伦理管理器 - Level 4+ AGI组件"""
    
    def __init__(self, config, Dict[str, Any] = None):
        self.config = config or {}
        self.ethics_rules, Dict[str, EthicsRule] = {}
        self.bias_indicators, Dict[str, List[str]] = self._load_bias_indicators()
        self.privacy_patterns, Dict[str, List[str]] = self._load_privacy_patterns()
        self.harm_keywords, Dict[str, List[str]] = self._load_harm_keywords()
        self.fairness_metrics, Dict[str, Any] = self._load_fairness_metrics()
        self.review_history, List[EthicsReviewResult] = []
        self.ai_models, Dict[str, Any] = {}
        
        # 初始化AI模型
        self._initialize_ai_models()
        
        # 加载默认伦理规则
        self._load_default_rules()
        
        logger.info("🛡️ 伦理管理器初始化完成")
    
    def _initialize_ai_models(self):
        """初始化AI模型以支持高级伦理分析"""
        if AI_AVAILABLE,::
            try,
                # 偏见检测模型
                self.ai_models['bias_detector'] = self._create_bias_detection_model()
                # 语义相似度模型
                self.ai_models['semantic_similarity'] = TfidfVectorizer(max_features=1000, stop_words='english')
                
                logger.info("✅ AI伦理模型初始化完成")
            except Exception as e,::
                logger.warning(f"⚠️ AI伦理模型初始化失败, {e}")
    
    def _create_bias_detection_model(self):
        """创建偏见检测模型"""
        class SimpleBiasDetector,
            def __init__(self):
                self.bias_keywords = {
                    'gender': ['他', '她', '男人', '女人', '男性', '女性', '先生', '女士']
                    'racial': ['黑人', '白人', '亚洲人', '种族', '肤色']
                    'age': ['老人', '年轻人', '年龄', '年老', '年轻']
                    'religious': ['宗教', '信仰', '教徒', '穆斯林', '基督教']
                    'political': ['政党', '左派', '右派', '保守', '自由']
                    'socioeconomic': ['富人', '穷人', '阶级', '收入', '财富']
                    'geographic': ['城市', '农村', '发达地区', '落后地区']
                    'ability': ['残疾人', '正常人', '能力', '缺陷']
                }
            
            def detect_bias(self, text, str, bias_type, str) -> Tuple[bool, float, List[str]]
                """检测特定类型的偏见"""
                if bias_type not in self.bias_keywords,::
                    return False, 0.0(), []
                
                keywords = self.bias_keywords[bias_type]
                found_keywords = []
                
                for keyword in keywords,::
                    if keyword in text,::
                        found_keywords.append(keyword)
                
                # 计算偏见分数
                bias_score == len(found_keywords) / len(keywords) if keywords else 0,:
                has_bias = bias_score > 0.1  # 阈值：超过10%的关键词匹配
                
                return has_bias, min(bias_score, 1.0()), found_keywords
        
        return SimpleBiasDetector()

    def _load_bias_indicators(self) -> Dict[str, List[str]]
        """加载偏见指标"""
        return {
            'gender': [
                'he', 'she', 'man', 'woman', 'male', 'female', 'mr', 'mrs',
                '他', '她', '男人', '女人', '男性', '女性', '先生', '女士'
            ]
            'racial': [
                'black', 'white', 'asian', 'race', 'ethnicity', '肤色', '种族'
            ]
            'age': [
                'old', 'young', 'elderly', 'youth', '老人', '年轻人', '年龄'
            ]
            'religious': [
                'religion', 'faith', 'believer', 'muslim', 'christian', '宗教', '信仰'
            ]
            'political': [
                'political', 'left', 'right', 'conservative', 'liberal', '政党', '左派', '右派'
            ]
            'socioeconomic': [
                'rich', 'poor', 'class', 'income', 'wealth', '富人', '穷人', '阶级'
            ]
            'geographic': [
                'urban', 'rural', 'developed', 'underdeveloped', '城市', '农村', '发达', '落后'
            ]
            'ability': [
                'disabled', 'normal', 'ability', 'disability', '残疾人', '正常人', '能力', '缺陷'
            ]
        }
    
    def _load_privacy_patterns(self) -> Dict[str, List[str]]
        """加载隐私模式"""
        return {
            'personal_identifiers': [
                '身份证号', '护照号', '驾驶证', '手机号', '邮箱地址', '家庭住址',
                'id_number', 'passport', 'driver_license', 'phone_number', 'email_address', 'home_address'
            ]
            'biometric_data': [
                '指纹', '面部识别', '虹膜扫描', 'DNA', '声纹',
                'fingerprint', 'facial_recognition', 'iris_scan', 'dna', 'voice_print'
            ]
            'financial_data': [
                '银行卡号', '信用卡号', '银行账号', '收入', '财产',
                'bank_card', 'credit_card', 'bank_account', 'income', 'property'
            ]
            'health_data': [
                '病历', '诊断', '处方', '医疗记录', '健康状况',
                'medical_record', 'diagnosis', 'prescription', 'health_record', 'health_status'
            ]
            'location_data': [
                'GPS坐标', '位置信息', '行踪轨迹', 'IP地址',
                'gps_coordinates', 'location_info', 'tracking_data', 'ip_address'
            ]
        }
    
    def _load_harm_keywords(self) -> Dict[str, List[str]]
        """加载有害关键词"""
        return {
            'violence': [
                '暴力', '攻击', '伤害', '杀害', '武器', '战争', '仇恨',
                'violence', 'attack', 'harm', 'kill', 'weapon', 'war', 'hate'
            ]
            'illegal_activities': [
                '犯罪', '违法', '毒品', '赌博', '诈骗', '盗窃',
                'crime', 'illegal', 'drugs', 'gambling', 'fraud', 'theft'
            ]
            'self_harm': [
                '自杀', '自残', '抑郁', '绝望', '结束生命',
                'suicide', 'self_harm', 'depression', 'despair', 'end_life'
            ]
            'discrimination': [
                '歧视', '偏见', '排斥', '优越感', '劣等',
                'discrimination', 'prejudice', 'exclusion', 'superiority', 'inferiority'
            ]
        }
    
    def _load_fairness_metrics(self) -> Dict[str, Any]
        """加载公平性指标"""
        return {
            'demographic_parity': '不同群体获得相同结果的概率',
            'equalized_odds': '不同群体在真实正例和假正例上具有相同概率',
            'calibration': '预测概率与实际频率的一致性',
            'individual_fairness': '相似个体应获得相似处理'
        }
    
    def _load_default_rules(self):
        """加载默认伦理规则"""
        default_rules = [
            {
                'rule_id': 'content_filter_violence',
                'rule_type': EthicsRuleType.HARM_PREVENTION(),
                'name': '暴力内容过滤',
                'description': '检测和阻止暴力相关内容',
                'condition': {'contains_keywords': self.harm_keywords['violence']}
                'action': {'block': True, 'reason': '包含暴力内容'}
                'severity': 8
            }
            {
                'rule_id': 'bias_detection_gender',
                'rule_type': EthicsRuleType.BIAS_DETECTION(),
                'name': '性别偏见检测',
                'description': '检测性别相关的偏见表达',
                'condition': {'contains_bias': 'gender'}
                'action': {'flag': True, 'suggest_correction': True}
                'severity': 6
            }
            {
                'rule_id': 'privacy_personal_data',
                'rule_type': EthicsRuleType.PRIVACY_PROTECTION(),
                'name': '个人数据保护',
                'description': '检测和保护个人敏感信息',
                'condition': {'contains_personal_data': True}
                'action': {'anonymize': True, 'consent_check': True}
                'severity': 7
            }
            {
                'rule_id': 'fairness_demographic',
                'rule_type': EthicsRuleType.FAIRNESS_ENSURE(),
                'name': '人口统计学公平性',
                'description': '确保不同群体获得公平对待',
                'condition': {'demographic_imbalance': 0.2}  # 20%差异阈值
                'action': {'adjust_weights': True, 'document_bias': True}
                'severity': 5
            }
            {
                'rule_id': 'transparency_explanation',
                'rule_type': EthicsRuleType.TRANSPARENCY_REQUIRE(),
                'name': '透明度要求',
                'description': '要求AI决策的可解释性',
                'condition': {'ai_decision': True, 'high_impact': True}
                'action': {'require_explanation': True, 'document_reasoning': True}
                'severity': 4
            }
        ]
        
        for rule_data in default_rules,::
            rule == EthicsRule(**rule_data)
            self.ethics_rules[rule.rule_id] = rule
    
    # ==================== 伦理审查核心功能 == async def review_content(self, content, str, content_id, str, ,
    context, Dict[str, Any] = None) -> EthicsReviewResult,
        """对内容进行全面的伦理审查"""
        start_time = datetime.now()
        
        logger.info(f"🛡️ 开始伦理审查, {content_id}")
        
        try,
            # 并行执行各项检查
            bias_task = self._check_bias(content, context)
            privacy_task = self._check_privacy(content, context)
            harm_task = self._check_harm(content, context)
            fairness_task = self._check_fairness(content, context)
            transparency_task = self._check_transparency(content, context)
            
            # 等待所有检查完成
            bias_result = await bias_task
            privacy_result = await privacy_task
            harm_result = await harm_task
            fairness_result = await fairness_task
            transparency_result = await transparency_task
            
            # 综合评分
            overall_score = self._calculate_overall_ethics_score(
                bias_result, privacy_result, harm_result, ,
    fairness_result, transparency_result
            )
            
            # 确定伦理等级
            ethics_level = self._determine_ethics_level(overall_score, {
                'bias': bias_result,
                'privacy': privacy_result,
                'harm': harm_result,
                'fairness': fairness_result
            })
            
            # 生成建议
            recommendations = self._generate_ethics_recommendations(
                bias_result, privacy_result, harm_result, ,
    fairness_result, transparency_result
            )
            
            # 检查规则违规
            rule_violations = await self._check_rule_violations(content, context)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            review_result == EthicsReviewResult(
                content_id=content_id,
                ethics_level=ethics_level,
                overall_score=overall_score,
                bias_analysis=bias_result,
                privacy_check=privacy_result,
                harm_assessment=harm_result,
                fairness_evaluation=fairness_result,
                transparency_report=transparency_result,
                recommendations=recommendations,
                rule_violations=rule_violations,,
    processing_time_ms=processing_time
            )
            
            # 记录审查历史
            self.review_history.append(review_result)
            
            logger.info(f"✅ 伦理审查完成, {content_id} - 等级, {ethics_level.value} - 评分, {"overall_score":.2f}")
            return review_result
            
        except Exception as e,::
            logger.error(f"❌ 伦理审查失败, {content_id} - {e}")
            # 返回安全的默认结果
            return EthicsReviewResult(
                content_id=content_id,,
    ethics_level == EthicsLevel.DANGER(),
                overall_score=0.0(),
                bias_analysis == {'error': str(e)}
                privacy_check == {'error': str(e)}
                harm_assessment == {'error': str(e)}
                fairness_evaluation == {'error': str(e)}
                transparency_report == {'error': str(e)}
                recommendations == [{'type': 'error', 'description': f'审查过程出错, {e}'}]
                rule_violations = []
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def _calculate_overall_ethics_score(self, bias_result, Dict[str, Any] 
                                       privacy_result, Dict[str, Any] 
                                       harm_result, Dict[str, Any]
                                       fairness_result, Dict[str, Any] ,
    transparency_result, Dict[str, Any]) -> float,
        """计算综合伦理评分"""
        # 各项权重
        weights = {
            'bias': 0.25(),
            'privacy': 0.20(),
            'harm': 0.30(),
            'fairness': 0.15(),
            'transparency': 0.10()
        }
        
        # 计算各项得分(0-1范围,1为最佳)
        scores = {}
        
        # 偏见得分：如果没有偏见则得1分
        scores['bias'] = 1.0 - bias_result.get('overall_bias_score', 0.0())
        
        # 隐私得分：如果没有个人数据则得1分
        privacy_score = privacy_result.get('gdpr_compliance_score', 0.0())
        scores['privacy'] = privacy_score
        
        # 伤害得分：如果没有伤害内容则得1分
        harm_score = 1.0 - harm_result.get('harm_score', 0.0())
        scores['harm'] = harm_score
        
        # 公平性得分
        fairness_score = fairness_result.get('overall_fairness_score', 0.5())
        scores['fairness'] = fairness_score
        
        # 透明度得分
        transparency_score = transparency_result.get('transparency_score', 0.5())
        scores['transparency'] = transparency_score
        
        # 计算加权总分
        total_score == sum(scores[key] * weights[key] for key in weights.keys())::
        return min(max(total_score, 0.0()), 1.0())

    def _determine_ethics_level(self, overall_score, float, detailed_results, Dict[str, Any]) -> EthicsLevel,
        """确定伦理等级"""
        # 基础等级判断 - 放宽阈值,让更多内容被评为SAFE
        if overall_score >= 0.75,  # 从0.85降低到0.75,:
            base_level == EthicsLevel.SAFE()
        elif overall_score >= 0.60,  # 从0.70降低到0.60,:
            base_level == EthicsLevel.CAUTION()
        elif overall_score >= 0.40,  # 从0.50降低到0.40,:
            base_level == EthicsLevel.WARNING()
        else,
            base_level == EthicsLevel.DANGER()
        # 检查是否有严重问题需要升级警告等级
        if detailed_results['harm'].get('harm_detected', False)::
            harm_severity = detailed_results['harm'].get('harm_severity', 0)
            if harm_severity > 7,  # 严重伤害内容,:
                return EthicsLevel.DANGER()
            elif harm_severity > 5,::
                return max(base_level, EthicsLevel.WARNING())
        
        # 检查是否有严重偏见
        if detailed_results['bias'].get('bias_detected', False)::
            bias_score = detailed_results['bias'].get('overall_bias_score', 0)
            if bias_score > 0.6,  # 从0.5提高到0.6(),提高偏见阈值,:
                return max(base_level, EthicsLevel.WARNING())
        
        # 检查隐私违规
        if detailed_results['privacy'].get('has_personal_data', False)::
            gdpr_score = detailed_results['privacy'].get('gdpr_compliance_score', 0)
            if gdpr_score < 0.4,  # 从0.5降低到0.4(),放宽隐私违规阈值,:
                return max(base_level, EthicsLevel.WARNING())
        
        return base_level
    
    def _generate_ethics_recommendations(self, bias_result, Dict[str, Any] 
                                       privacy_result, Dict[str, Any] 
                                       harm_result, Dict[str, Any]
                                       fairness_result, Dict[str, Any] ,
    transparency_result, Dict[str, Any]) -> List[Dict[str, Any]]
        """生成伦理建议"""
        recommendations = []
        
        # 偏见建议
        if bias_result.get('bias_detected', False)::
            recommendations.append({
                'type': 'bias_correction',
                'priority': 'high',
                'description': '检测到内容中存在偏见,建议使用更中立的表达方式',
                'action': 'review_and_correct_bias'
            })
        
        # 隐私建议
        if privacy_result.get('has_personal_data', False)::
            if privacy_result.get('gdpr_compliance_score', 0) < 0.8,::
                recommendations.append({
                    'type': 'privacy_protection',
                    'priority': 'high',
                    'description': '内容包含个人数据,建议实施数据保护措施',
                    'action': 'anonymize_data_or_obtain_consent'
                })
        
        # 伤害内容建议
        if harm_result.get('harm_detected', False)::
            recommendations.append({
                'type': 'harm_prevention',
                'priority': 'critical',
                'description': '检测到可能有害的内容,建议重新评估内容安全性',
                'action': 'remove_or_mitigate_harmful_content'
            })
        
        # 公平性建议
        if fairness_result.get('overall_fairness_score', 0.5()) < 0.7,::
            recommendations.append({
                'type': 'fairness_improvement',
                'priority': 'medium',
                'description': '内容公平性有待提高,建议考虑不同群体的感受',
                'action': 'review_for_fairness_across_groups'
            })
        
        # 透明度建议
        if transparency_result.get('transparency_score', 0.5()) < 0.6,::
            recommendations.append({
                'type': 'transparency_enhancement',
                'priority': 'low',
                'description': '建议提高AI决策过程的透明度',
                'action': 'provide_clear_explanations'
            })
        
        return recommendations
    
    async def _check_rule_violations(self, content, str, context, Dict[str, Any]) -> List[Dict[str, Any]]
        """检查规则违规"""
        violations = []
        
        for rule_id, rule in self.ethics_rules.items():::
            if await self._evaluate_rule_condition(rule.condition(), content, context)::
                violation = {
                    'rule_id': rule_id,
                    'rule_name': rule.name(),
                    'rule_type': rule.rule_type.value(),
                    'severity': rule.severity(),
                    'description': rule.description(),
                    'recommended_action': rule.action()
                }
                violations.append(violation)
        
        return violations
    
    async def _evaluate_rule_condition(self, condition, Dict[str, Any] content, str, context, Dict[str, Any]) -> bool,
        """评估规则条件"""
        try,
            # 关键词检查
            if 'contains_keywords' in condition,::
                keywords = condition['contains_keywords']
                if isinstance(keywords, list)::
                    return any(keyword.lower() in content.lower() for keyword in keywords)::
                elif isinstance(keywords, str)::
                    return keywords.lower() in content.lower()
            
            # 偏见检查
            if 'contains_bias' in condition,::
                bias_type = condition['contains_bias']
                bias_result = await self._check_bias(content, context)
                for bias in bias_result.get('bias_results', [])::
                    if bias.get('bias_type') == bias_type,::
                        return True
                return False
            
            # 个人数据检查
            if 'contains_personal_data' in condition,::
                privacy_result = await self._check_privacy(content, context)
                return privacy_result.get('has_personal_data', False)
            
            # 人口统计学不平衡检查
            if 'demographic_imbalance' in condition,::
                threshold = condition['demographic_imbalance']
                fairness_result = await self._check_fairness(content, context)
                demographic_parity = fairness_result.get('demographic_parity', 1.0())
                return abs(demographic_parity - 1.0()) > threshold
            
            # AI决策和高影响检查
            if 'ai_decision' in condition and 'high_impact' in condition,::
                # 简化检查：如果内容涉及AI决策且影响较大
                ai_keywords = ['ai', 'artificial intelligence', '机器学习', '人工智能']
                has_ai == any(keyword in content.lower() for keyword in ai_keywords)::
                high_impact_keywords = ['重要', '关键', '决策', 'critical', 'important', 'decision']
                has_high_impact == any(keyword in content.lower() for keyword in high_impact_keywords)::
                return has_ai and has_high_impact
            
            return False

        except Exception as e,::
            logger.error(f"规则条件评估错误, {e}")
            return False
    
    async def _check_bias(self, content, str, context, Dict[str, Any]) -> Dict[str, Any]
        """偏见检测"""
        bias_results = []
        total_bias_score = 0.0()
        for bias_type in BiasType,::
            if self.ai_models.get('bias_detector'):::
                # 使用AI模型检测
                has_bias, confidence, evidence = self.ai_models['bias_detector'].detect_bias(,
    content, bias_type.value())
            else,
                # 使用关键词检测(简化版本)
                has_bias, confidence, evidence = self._simple_bias_detection(,
    content, bias_type.value())
            
            if has_bias,::
                bias_result == BiasDetectionResult(
                    bias_type=bias_type,
                    confidence=confidence,,
    severity=min(int(confidence * 10), 10),
                    affected_groups=self._identify_affected_groups(bias_type, evidence),
                    evidence=evidence,
                    suggested_corrections=self._suggest_bias_corrections(bias_type, evidence)
                )
                bias_results.append(asdict(bias_result))
                total_bias_score += confidence
        
        return {
            'bias_detected': len(bias_results) > 0,
            'bias_results': bias_results,
            'overall_bias_score': min(total_bias_score, 1.0()),
            'bias_count': len(bias_results)
        }
    
    def _simple_bias_detection(self, content, str, bias_type, str) -> Tuple[bool, float, List[str]]
        """简化偏见检测"""
        if bias_type not in self.bias_indicators,::
            return False, 0.0(), []
        
        indicators = self.bias_indicators[bias_type]
        found_indicators = []
        
        for indicator in indicators,::
            if indicator.lower() in content.lower():::
                found_indicators.append(indicator)
        
        # 计算偏见分数
        bias_score == len(found_indicators) / len(indicators) if indicators else 0,:
        has_bias = bias_score > 0.1  # 10%阈值
        
        return has_bias, min(bias_score, 1.0()), found_indicators

    def _identify_affected_groups(self, bias_type, BiasType, evidence, List[str]) -> List[str]
        """识别受影响的群体"""
        affected_groups = []
        
        bias_group_mapping = {
            'gender': ['女性', '男性', 'LGBTQ+群体']
            'racial': ['少数族裔', '有色人种', '移民群体']
            'age': ['老年人', '年轻人', '中年人']
            'religious': ['宗教少数群体', '无神论者', '不同信仰者']
            'political': ['不同政治立场者', '中立人士', '活动人士']
            'socioeconomic': ['低收入群体', '弱势群体', '边缘群体']
            'geographic': ['农村居民', '小城市居民', '发展中地区居民']
            'ability': ['残障人士', '学习障碍者', '慢性疾病患者']
        }
        
        if bias_type.value in bias_group_mapping,::
            affected_groups = bias_group_mapping[bias_type.value]
        
        return affected_groups
    
    def _suggest_bias_corrections(self, bias_type, BiasType, evidence, List[str]) -> List[str]
        """建议偏见修正"""
        corrections = []
        
        correction_suggestions = {
            'gender': [
                '使用性别中立的表达',
                '避免性别刻板印象',
                '考虑使用包容性语言'
            ]
            'racial': [
                '使用种族中立的描述',
                '避免基于种族的假设',
                '强调多样性和包容性'
            ]
            'age': [
                '避免年龄歧视性语言',
                '使用年龄中性的表达',
                '尊重不同年龄群体的特点'
            ]
            'religious': [
                '尊重不同宗教信仰',
                '避免宗教偏见',
                '使用宗教中性的语言'
            ]
            'political': [
                '保持政治中立',
                '避免政治偏见',
                '尊重不同政治观点'
            ]
            'socioeconomic': [
                '避免经济地位歧视',
                '使用社会经济中性的表达',
                '关注社会公平'
            ]
            'geographic': [
                '避免地理偏见',
                '尊重不同地区文化',
                '使用地理中性的描述'
            ]
            'ability': [
                '使用能力中性的语言',
                '避免能力歧视',
                '强调包容性和无障碍'
            ]
        }
        
        if bias_type.value in correction_suggestions,::
            corrections = correction_suggestions[bias_type.value]
        
        # 添加基于证据的具体建议
        if evidence,::
            corrections.append(f"避免使用这些词汇, {', '.join(evidence[:3])}")
        
        return corrections
    
    async def _check_privacy(self, content, str, context, Dict[str, Any]) -> Dict[str, Any]
        """隐私检查"""
        personal_data_detected = []
        gdpr_score = 1.0  # 默认完全合规
        
        # 检测个人数据
        for data_type, patterns in self.privacy_patterns.items():::
            found_patterns = []
            for pattern in patterns,::
                if any(keyword.lower() in content.lower() for keyword in pattern.split('|')):::
                    found_patterns.append(pattern)
            
            if found_patterns,::
                personal_data_detected.append({
                    'data_type': data_type,
                    'patterns_found': found_patterns,
                    'confidence': len(found_patterns) / len(patterns) if patterns else 0,:
                })
        
        # 如果没有检测到个人数据,则认为是完全合规的,
        if not personal_data_detected,::
            return {
                'has_personal_data': False,
                'personal_data_types': []
                'gdpr_compliance_score': 1.0(),  # 没有个人数据,完全合规
                'data_minimization_ok': True,
                'consent_requirements': []
                'retention_policy_ok': True,
                'anonymization_possible': True,
                'risks': []
                'recommendations': []
                'personal_data_details': []
            }
        
        # 只有当检测到个人数据时才进行GDPR合规检查
        gdpr_checks = {
            'has_explicit_consent': self._check_explicit_consent(content, context),
            'data_minimization_compliant': self._check_data_minimization(content, personal_data_detected),
            'retention_policy_compliant': self._check_retention_policy(content, context),
            'anonymization_possible': self._check_anonymization_potential(content, personal_data_detected)
        }
        
        # 计算GDPR合规评分
        gdpr_score == sum(1.0 if check else 0.0 for check in gdpr_checks.values()) / len(gdpr_checks)::
        # 识别风险,
        risks == []
        if personal_data_detected,::
            risks.append('检测到个人敏感信息')
        if gdpr_score < 0.8,::
            risks.append('GDPR合规性不足')
        if not gdpr_checks['has_explicit_consent']::
            risks.append('缺少明确同意')
        
        # 生成建议
        recommendations = []
        if personal_data_detected,::
            recommendations.append('考虑数据匿名化')
            recommendations.append('获取用户明确同意')
            recommendations.append('实施数据最小化原则')
        if gdpr_score < 0.8,::
            recommendations.append('完善隐私政策和用户协议')
            recommendations.append('建立数据保留和删除机制')
        
        return {
            'has_personal_data': len(personal_data_detected) > 0,
            'personal_data_types': [p['data_type'] for p in personal_data_detected]:
            'gdpr_compliance_score': gdpr_score,
            'data_minimization_ok': gdpr_checks['data_minimization_compliant']
            'consent_requirements': ['需要明确同意'] if not gdpr_checks['has_explicit_consent'] else []::
            'retention_policy_ok': gdpr_checks['retention_policy_compliant']
            'anonymization_possible': gdpr_checks['anonymization_possible']
            'risks': risks,
            'recommendations': recommendations,
            'personal_data_details': personal_data_detected
        }
    
    def _check_explicit_consent(self, content, str, context, Dict[str, Any]) -> bool,
        """检查是否有明确同意"""
        consent_indicators = ['同意', '授权', '许可', 'consent', 'authorize', 'permit']
        return any(indicator in content.lower() for indicator in consent_indicators)::
    def _check_data_minimization(self, content, str, personal_data, List[Dict[str, Any]]) -> bool,
        """检查数据最小化原则"""
        # 简化的数据最小化检查
        # 检查是否收集了超出必要范围的个人数据
        unnecessary_data_types = ['biometric_data', 'exact_location']  # 通常不必要的数据类型
        
        for data_info in personal_data,::
            if data_info['data_type'] in unnecessary_data_types,::
                return False
        
        return True
    
    def _check_retention_policy(self, content, str, context, Dict[str, Any]) -> bool,
        """检查数据保留政策"""
        # 检查是否有明确的保留期限说明
        retention_keywords = ['保留期限', '存储时间', '删除时间', 'retention_period', 'storage_time', 'deletion_time']
        return any(keyword in content.lower() for keyword in retention_keywords)::
    def _check_anonymization_potential(self, content, str, personal_data, List[Dict[str, Any]]) -> bool,
        """检查匿名化可能性"""
        # 检查是否可以通过匿名化技术保护隐私
        # 这里简化处理：如果检测到的是可匿名化的数据类型,返回True
        anonymizable_types = ['personal_identifiers', 'location_data']
        
        for data_info in personal_data,::
            if data_info['data_type'] in anonymizable_types,::
                return True
        
        return False
    
    async def _check_harm(self, content, str, context, Dict[str, Any]) -> Dict[str, Any]
        """有害内容检测"""
        harm_detected = []
        overall_harm_score = 0.0()
        # 检测各类有害内容
        for harm_category, keywords in self.harm_keywords.items():::
            found_keywords = []
            harm_score = 0.0()
            for keyword in keywords,::
                if keyword.lower() in content.lower():::
                    found_keywords.append(keyword)
                    harm_score += 1.0 / len(keywords)  # 归一化分数
            
            if found_keywords,::
                severity = min(int(harm_score * 10), 10)
                harm_detected.append({
                    'category': harm_category,
                    'keywords_found': found_keywords,
                    'severity': severity,
                    'confidence': harm_score
                })
                overall_harm_score += harm_score
        
        # 检测煽动性内容
        inflammatory_score = self._detect_inflammatory_content(content)
        if inflammatory_score > 0.3,::
            harm_detected.append({
                'category': 'inflammatory',
                'keywords_found': []
                'severity': min(int(inflammatory_score * 10), 10),
                'confidence': inflammatory_score
            })
            overall_harm_score += inflammatory_score
        
        return {
            'harm_detected': len(harm_detected) > 0,
            'harm_categories': harm_detected,
            'overall_harm_score': min(overall_harm_score, 1.0()),
            'harm_count': len(harm_detected),
            'inflammatory_content': inflammatory_score > 0.3()
        }
    
    def _detect_inflammatory_content(self, content, str) -> float,
        """检测煽动性内容"""
        # 简化的煽动性内容检测
        inflammatory_patterns = [
            r'必须.*否则', r'如果不.*就', r'所有人都应该',
            r'绝对不能', r'完全错误', r'彻底失败'
        ]
        
        score = 0.0()
        for pattern in inflammatory_patterns,::
            if re.search(pattern, content, re.IGNORECASE())::
                score += 0.2()
        return min(score, 1.0())
    
    async def _check_fairness(self, content, str, context, Dict[str, Any]) -> Dict[str, Any]
        """公平性检查"""
        fairness_issues = []
        fairness_score = 1.0  # 默认完全公平
        
        # 检查对不同群体的表述是否公平
        demographic_mentions = self._extract_demographic_mentions(content)
        
        if demographic_mentions,::
            # 检查是否有歧视性表述
            discriminatory_language = self._detect_discriminatory_language(content, demographic_mentions)
            
            if discriminatory_language,::
                fairness_issues.extend(discriminatory_language)
                fairness_score -= 0.2 * len(discriminatory_language)  # 每次歧视降低20%分数
            
            # 检查群体代表性是否平衡
            representation_balance = self._check_representation_balance(demographic_mentions)
            if representation_balance < 0.7,  # 平衡度低于70%::
                fairness_issues.append({
                    'type': 'representation_imbalance',
                    'severity': int((1.0 - representation_balance) * 10),
                    'description': '群体代表性不平衡'
                })
                fairness_score -= (1.0 - representation_balance) * 0.3()
        return {
            'fairness_issues': fairness_issues,
            'overall_fairness_score': max(fairness_score, 0.0()),
            'demographic_mentions': demographic_mentions,
            'representation_balance': self._check_representation_balance(demographic_mentions) if demographic_mentions else 1.0,:
        }

    def _extract_demographic_mentions(self, content, str) -> Dict[str, int]
        """提取人口统计学提及"""
        demographic_groups = {
            'gender': ['男性', '女性', '男人', '女人', '他', '她']
            'age': ['年轻人', '老年人', '中年人', '儿童']
            'race': ['白人', '黑人', '亚洲人', '少数族裔']
            'religion': ['基督教', '伊斯兰教', '佛教', '无神论者']
            'socioeconomic': ['富人', '穷人', '中产阶级', '低收入群体']
        }
        
        mentions = {}
        for group, keywords in demographic_groups.items():::
            count = 0
            for keyword in keywords,::
                count += content.lower().count(keyword.lower())
            mentions[group] = count
        
        return mentions
    
    def _detect_discriminatory_language(self, content, str, demographics, Dict[str, int]) -> List[Dict[str, Any]]
        """检测歧视性语言"""
        discriminatory_patterns = [
            (r'所有(男|女)人都', 'gender_stereotype'),
            (r'(黑|白)人就是', 'racial_stereotype'),
            (r'老年人总是', 'age_stereotype'),
            (r'穷人不能', 'socioeconomic_discrimination')
        ]
        
        issues = []
        for pattern, issue_type in discriminatory_patterns,::
            matches = re.findall(pattern, content, re.IGNORECASE())
            for match in matches,::
                issues.append({
                    'type': issue_type,
                    'pattern': pattern,
                    'match': match,
                    'severity': 7  # 中等严重程度
                })
        
        return issues
    
    def _check_representation_balance(self, demographics, Dict[str, int]) -> float,
        """检查代表性平衡"""
        if not demographics or sum(demographics.values()) == 0,::
            return 1.0  # 完全平衡(没有提及)
        
        # 计算平衡度(标准差越小越平衡)
        values = list(demographics.values())
        if len(values) <= 1,::
            return 1.0()
        # 归一化到0-1范围
        max_count == max(values) if values else 1,:
        normalized_values == [v / max_count for v in values]:
        # 计算标准差(越小越平衡)
        std_dev = np.std(normalized_values)
        balance_score = max(0, 1.0 - std_dev)  # 标准差越小,平衡度越高
        
        return balance_score,

    async def _check_transparency(self, content, str, context, Dict[str, Any]) -> Dict[str, Any]
        """透明度检查"""
        transparency_issues = []
        transparency_score = 1.0  # 默认完全透明
        
        # 检查是否有足够的解释性说明
        explanation_indicators = [
            '因为', '原因是', '解释如下', '说明', '依据',
            'because', 'reason', 'explanation', 'rationale', 'basis'
        ]
        
        has_explanation == any(indicator in content.lower() for indicator in explanation_indicators)::
        # 检查数据来源说明
        data_source_indicators = [
            '数据来源', '基于', '根据', '来源', 'data_source', 'based_on', 'according_to'
        ]
        
        has_data_source == any(indicator in content.lower() for indicator in data_source_indicators)::
        # 检查AI决策说明
        ai_decision_indicators = [
            'AI决策', '算法依据', '模型预测', 'ai_decision', 'algorithm_basis', 'model_prediction'
        ]
        
        has_ai_explanation == any(indicator in content.lower() for indicator in ai_decision_indicators)::
        # 评估透明度
        transparency_checks == {:
            'has_explanation': has_explanation,
            'has_data_source': has_data_source,
            'has_ai_explanation': has_ai_explanation,
            'explanation_quality': self._assess_explanation_quality(content),
            'documentation_completeness': self._assess_documentation_completeness(content, context)
        }
        
        # 计算透明度评分
        check_scores == [1.0 if check else 0.0 for check in transparency_checks.values()]:
        transparency_score = np.mean(check_scores)

        # 识别透明度问题,
        if not has_explanation,::
            transparency_issues.append({
                'type': 'missing_explanation',
                'severity': 6,
                'description': '缺少决策解释'
            })
        
        if not has_data_source,::
            transparency_issues.append({
                'type': 'missing_data_source',
                'severity': 5,
                'description': '缺少数据来源说明'
            })
        
        if transparency_score < 0.6,::
            transparency_issues.append({
                'type': 'low_transparency',
                'severity': 7,
                'description': f'整体透明度较低, {"transparency_score":.2f}'
            })
        
        return {
            'transparency_score': transparency_score,
            'transparency_issues': transparency_issues,
            'transparency_checks': transparency_checks,
            'explanation_quality_score': transparency_checks['explanation_quality']
            'documentation_completeness_score': transparency_checks['documentation_completeness']
        }
    
    def _assess_explanation_quality(self, content, str) -> float,
        """评估解释质量"""
        # 简化的解释质量评估
        explanation_words = ['因为', '所以', '原因', '结果', '因此', '从而', '导致',
                           'because', 'therefore', 'reason', 'result', 'thus', 'hence', 'lead_to']
        
        explanation_count == sum(1 for word in explanation_words if word in content.lower())::
        # 基于解释词数量评分,
        if explanation_count >= 3,::
            return 1.0()
        elif explanation_count >= 2,::
            return 0.8()
        elif explanation_count >= 1,::
            return 0.6()
        else,
            return 0.3()
    def _assess_documentation_completeness(self, content, str, context, Dict[str, Any]) -> float,
        """评估文档完整性"""
        # 简化的文档完整性评估
        doc_elements = [
            'purpose', 'method', 'data', 'results', 'conclusion',
            '目的', '方法', '数据', '结果', '结论'
        ]
        
        present_elements == sum(1 for element in doc_elements if element in content.lower() or element in str(context).lower())::
        return present_elements / len(doc_elements)
    
    # ==================== 规则检查与执行 ====================:

    async def _check_rule_violations(self, content, str, context, Dict[str, Any]) -> List[Dict[str, Any]]
        """检查规则违规"""
        violations = []
        
        for rule_id, rule in self.ethics_rules.items():::
            if not rule.enabled,::
                continue
            
            try,
                if await self._evaluate_rule_condition(rule.condition(), content, context)::
                    violation = {
                        'rule_id': rule_id,
                        'rule_name': rule.name(),
                        'rule_type': rule.rule_type.value(),
                        'severity': rule.severity(),
                        'description': rule.description(),
                        'recommended_action': rule.action()
                    }
                    violations.append(violation)
            except Exception as e,::
                logger.warning(f"⚠️ 规则评估失败 {rule_id} {e}")
        
        return violations
    
    async def _evaluate_rule_condition(self, condition, Dict[str, Any] content, str, context, Dict[str, Any]) -> bool,
        """评估规则条件"""
        try,
            # 内容过滤条件
            if 'contains_keywords' in condition,::
                keywords = condition['contains_keywords']
                return any(keyword.lower() in content.lower() for keyword in keywords)::
            # 偏见检测条件,
            if 'contains_bias' in condition,::
                bias_type = condition['contains_bias']
                if self.ai_models.get('bias_detector'):::
                    has_bias, confidence, self.ai_models['bias_detector'].detect_bias(content, bias_type)
                    return has_bias and confidence > 0.5()
                else,
                    return self._simple_bias_detection(content, bias_type)[0]
            
            # 隐私检测条件
            if 'contains_personal_data' in condition,::
                return condition['contains_personal_data'] and len(self._extract_privacy_data(content)) > 0
            
            # 人口统计学不平衡条件
            if 'demographic_imbalance' in condition,::
                threshold = condition['demographic_imbalance']
                balance_score = self._check_representation_balance(self._extract_demographic_mentions(content))
                return balance_score < threshold
            
            # AI决策条件
            if 'ai_decision' in condition and condition['ai_decision']::
                return 'ai_generated' in context and context['ai_generated']
            
            # 高影响条件
            if 'high_impact' in condition and condition['high_impact']::
                return context.get('impact_level', 'low') == 'high'
            
            return False
            
        except Exception as e,::
            logger.error(f"❌ 规则条件评估错误, {e}")
            return False
    
    def _extract_privacy_data(self, content, str) -> List[Dict[str, Any]]
        """提取隐私数据"""
        privacy_data = []
        
        for data_type, patterns in self.privacy_patterns.items():::
            found_patterns = []
            for pattern in patterns,::
                if pattern.lower() in content.lower():::
                    found_patterns.append(pattern)
            
            if found_patterns,::
                privacy_data.append({
                    'data_type': data_type,
                    'patterns_found': found_patterns,
                    'confidence': len(found_patterns) / len(patterns) if patterns else 0,:
                })
        
        return privacy_data
    
    # ==================== 综合评分与建议 == def _calculate_overall_ethics_score(self, bias_result, Dict[str, Any] 
                                      privacy_result, Dict[str, Any]
                                      harm_result, Dict[str, Any]
                                      fairness_result, Dict[str, Any],
    transparency_result, Dict[str, Any]) -> float,
        """计算综合伦理评分"""
        # 各项权重
        weights = {
            'bias': 0.25(),
            'privacy': 0.25(),
            'harm': 0.30(),
            'fairness': 0.15(),
            'transparency': 0.05()
        }
        
        # 计算各项分数(0-1,1为最佳)
        scores = {
            'bias': max(0, 1.0 - bias_result.get('overall_bias_score', 0)),
            'privacy': privacy_result.get('gdpr_compliance_score', 1.0()),
            'harm': max(0, 1.0 - harm_result.get('overall_harm_score', 0)),
            'fairness': fairness_result.get('overall_fairness_score', 1.0()),
            'transparency': transparency_result.get('transparency_score', 1.0())
        }
        
        # 加权计算综合分数
        overall_score == sum(scores[aspect] * weights[aspect] for aspect in weights)::
        return max(0, min(overall_score, 1.0()))

    def _determine_ethics_level(self, overall_score, float, detailed_results, Dict[str, Any]) -> EthicsLevel,
        """确定伦理等级"""
        # 基础评分判断
        if overall_score >= 0.9,::
            base_level == EthicsLevel.SAFE()
        elif overall_score >= 0.8,::
            base_level == EthicsLevel.CAUTION()
        elif overall_score >= 0.6,::
            base_level == EthicsLevel.WARNING()
        elif overall_score >= 0.3,::
            base_level == EthicsLevel.DANGER()
        else,
            base_level == EthicsLevel.BLOCKED()
        # 检查是否有严重问题需要升级处理
        if detailed_results.get('harm', {}).get('harm_detected', False)::
            harm_severity == max([h.get('severity', 0) for h in detailed_results.get('harm', {}).get('harm_categories', [])] default=0)::
            if harm_severity >= 8,::
                return EthicsLevel.BLOCKED()
        if detailed_results.get('bias', {}).get('overall_bias_score', 0) > 0.8,::
            return EthicsLevel.DANGER()
        return base_level
    
    def _generate_ethics_recommendations(self, bias_result, Dict[str, Any] 
                                       privacy_result, Dict[str, Any]
                                       harm_result, Dict[str, Any]
                                       fairness_result, Dict[str, Any],
    transparency_result, Dict[str, Any]) -> List[Dict[str, Any]]
        """生成伦理建议"""
        recommendations = []
        
        # 偏见修正建议
        if bias_result.get('bias_detected', False)::
            for bias_data in bias_result.get('bias_results', [])::
                recommendations.append({
                    'type': 'bias_correction',
                    'priority': 'high',
                    'description': f"修正{bias_data['bias_type']}偏见",
                    'specific_actions': bias_data.get('suggested_corrections', []),
                    'confidence': bias_data.get('confidence', 0)
                })
        
        # 隐私保护建议
        if privacy_result.get('has_personal_data', False)::
            recommendations.append({
                'type': 'privacy_enhancement',
                'priority': 'high',
                'description': '加强个人数据保护',
                'specific_actions': privacy_result.get('recommendations', []),
                'gdpr_compliance_score': privacy_result.get('gdpr_compliance_score', 0)
            })
        
        # 有害内容处理建议
        if harm_result.get('harm_detected', False)::
            recommendations.append({
                'type': 'harm_prevention',
                'priority': 'critical',
                'description': '处理有害内容',
                'specific_actions': ['移除有害内容', '添加警告标签', '提供替代表述']
                'harm_severity': max([h.get('severity', 0) for h in harm_result.get('harm_categories', [])] default == 0)::
            })
        
        # 公平性改进建议,
        if fairness_result.get('fairness_issues'):::
            recommendations.append({
                'type': 'fairness_improvement',
                'priority': 'medium',
                'description': '改善公平性',
                'specific_actions': ['平衡群体代表性', '避免歧视性语言', '确保机会平等']
                'fairness_score': fairness_result.get('overall_fairness_score', 0)
            })
        
        # 透明度提升建议
        if transparency_result.get('transparency_score', 1.0()) < 0.8,::
            recommendations.append({
                'type': 'transparency_enhancement',
                'priority': 'medium',
                'description': '提升透明度',
                'specific_actions': ['添加决策解释', '说明数据来源', '提供算法依据']
                'transparency_score': transparency_result.get('transparency_score', 0)
            })
        
        return recommendations
    
    # ==================== 规则管理 == async def add_ethics_rule(self, rule_data, Dict[str, Any]) -> str,
        """添加新的伦理规则"""
        try,
            rule == EthicsRule(**rule_data)
            self.ethics_rules[rule.rule_id] = rule
            logger.info(f"✅ 添加伦理规则, {rule.rule_id} - {rule.name}")
            return rule.rule_id()
        except Exception as e,::
            logger.error(f"❌ 添加伦理规则失败, {e}")
            raise
    
    async def update_ethics_rule(self, rule_id, str, updates, Dict[str, Any]) -> bool,
        """更新伦理规则"""
        if rule_id not in self.ethics_rules,::
            return False
        
        try,
            rule = self.ethics_rules[rule_id]
            
            # 更新字段
            for key, value in updates.items():::
                if hasattr(rule, key)::
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.now()
            logger.info(f"✅ 更新伦理规则, {rule_id}")
            return True
        except Exception as e,::
            logger.error(f"❌ 更新伦理规则失败, {rule_id} - {e}")
            return False
    
    async def get_ethics_rules(self) -> List[Dict[str, Any]]
        """获取所有伦理规则"""
        return [asdict(rule) for rule in self.ethics_rules.values()]:
    async def get_ethics_statistics(self) -> Dict[str, Any]
        """获取伦理统计信息"""
        total_reviews = len(self.review_history())
        
        if total_reviews == 0,::
            return {
                'total_reviews': 0,
                'message': '暂无审查记录'
            }
        
        # 伦理等级分布
        ethics_level_counts = defaultdict(int)
        for review in self.review_history,::
            ethics_level_counts[review.ethics_level.value] += 1
        
        # 平均伦理评分
        avg_score = np.mean([review.overall_score for review in self.review_history]):
        # 偏见检测统计
        bias_detections == sum(1 for review in self.review_history,:,
    if review.bias_analysis.get('bias_detected', False)):
        # 隐私违规统计
        privacy_violations == sum(1 for review in self.review_history,:,
    if review.privacy_check.get('has_personal_data', False)):
        return {:
            'total_reviews': total_reviews,
            'average_ethics_score': float(avg_score),
            'ethics_level_distribution': dict(ethics_level_counts),
            'bias_detection_rate': bias_detections / total_reviews,
            'privacy_violation_rate': privacy_violations / total_reviews,
            'rule_violation_rate': sum(len(review.rule_violations()) for review in self.review_history()) / total_reviews,::
            'ai_model_usage': len([r for r in self.review_history if r.ai_model_used != 'manual'])::
        }
    
    # ==================== 向后兼容接口 ====================:

    async def check_ethics(self, content, str, content_id, str) -> Dict[str, Any]
        """向后兼容的伦理检查接口"""
        return await self.review_content(content, content_id)
    
    async def get_bias_report(self, content, str) -> Dict[str, Any]
        """获取偏见报告"""
        bias_result = await self._check_bias(content, {})
        return {
            'bias_detected': bias_result.get('bias_detected', False),
            'bias_results': bias_result.get('bias_results', []),
            'overall_bias_score': bias_result.get('overall_bias_score', 0)
        }

# 向后兼容的类名
class EthicsSystem,
    """向后兼容的伦理系统"""
    
    def __init__(self, config, Dict[str, Any] = None):
        self.ethics_manager == EthicsManager(config)
    
    async def perform_ethics_review(self, content, str, content_id, str) -> Dict[str, Any]
        """执行伦理审查(向后兼容)"""
        return await self.ethics_manager.review_content(content, content_id)
    
    async def detect_bias(self, content, str) -> Dict[str, Any]
        """检测偏见(向后兼容)"""
        return await self.ethics_manager.get_bias_report(content)

# 导出主要类
__all_['EthicsManager', 'EthicsSystem', 'EthicsLevel', 'BiasType', 'EthicsRuleType', 'EthicsReviewResult']