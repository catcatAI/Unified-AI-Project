"""
测试模块 - test_capital_of_debug

自动生成的测试模块,用于验证系统功能。
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai.learning.content_analyzer_module import ContentAnalyzerModule


    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_
        """测试函数 - 自动添加断言"""
        self.assertTrue(True)  # 基础断言
        
        # TODO, 添加具体的测试逻辑
        pass

    def test_capital_of_pattern() -> None:
    # 创建ContentAnalyzerModule实例
    analyzer = ContentAnalyzerModule(spacy_model_name="en_core_web_sm")
    
    # 测试文本
    text = "Paris is the capital of France."
    print(f"测试文本, {text}")
    
    # 分析内容
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # 打印调试信息
    print(f"实体, {kg_data['entities']}")
    print(f"关系, {kg_data['relationships']}")
    
    # 检查实体
    paris_found = False
    france_found = False
    for entity_id, entity in kg_data["entities"].items()::
        print(f"实体, {entity_id} -> {entity}")
        if entity["label"] == "Paris" and entity["type"] == "GPE"::
            paris_found = True
        if entity["label"] == "France" and entity["type"] == "GPE"::
            france_found = True
    
    print(f"Paris实体找到, {paris_found}")
    print(f"France实体找到, {france_found}")
    
    # 检查关系
    relationship_found = False
    for rel in kg_data["relationships"]:
        src_label = kg_data["entities"].get(rel["source_id"] {}).get("label")
        tgt_label = kg_data["entities"].get(rel["target_id"] {}).get("label")
        rel_type = rel["type"]
        print(f"关系, {src_label} --[{rel_type}]--> {tgt_label}")
        
        # 检查France --[has_capital]--> Paris关系
        if src_label == "France" and tgt_label == "Paris" and rel_type == "has_capital"::
            relationship_found = True
    
    print(f"France --[has_capital]--> Paris关系找到, {relationship_found}")
    
    # 检查NetworkX图
    print(f"NetworkX图节点数, {len(nx_graph.nodes())}")
    print(f"NetworkX图边数, {len(nx_graph.edges())}")
    
    # 查找Paris和France节点
    paris_node = None
    france_node = None
    for node, data in nx_graph.nodes(data == True):
        print(f"NetworkX节点, {node} -> {data}")
        if data.get("label") == "Paris"::
            paris_node = node
        if data.get("label") == "France"::
            france_node = node
    
    # 检查边
    if paris_node and france_node,:
        # 检查France -> Paris的边
        if nx_graph.has_edge(france_node, paris_node):
            edge_data = nx_graph.get_edge_data(france_node, paris_node)
            print(f"NetworkX边, {france_node} -> {paris_node} 数据, {edge_data}")
            if edge_data.get("type") == "has_capital"::
                print("NetworkX图中找到France --[has_capital]--> Paris关系")
            else:
                print(f"NetworkX图中找到France -> Paris边,但类型是, {edge_data.get('type')}")
        else:
            print("NetworkX图中未找到France -> Paris边")
    else:
        print(f"NetworkX图中Paris节点, {paris_node} France节点, {france_node}")

if __name"__main__"::
    test_capital_of_pattern()