#!/usr/bin/env python3
"""
文档链接验证脚本
检查所有 Markdown 文件中的内部链接是否有效
"""

import os
import re
import argparse
import json
from pathlib import Path
from typing import List, Tuple, Dict

# 默认忽略目录（不参与扫描）
IGNORE_PARTS = {"node_modules", ".git", "backup", "archives", "__pycache__", "venv", ".venv", "dist", "build"}
VERBOSE = os.environ.get('DOC_LINK_CHECK_VERBOSE') == '1'

# 兼容性重定位映射：当旧文档路径已更名/迁移时，使用此表将其判定为有效
# Key 为 Markdown 中出现的原始相对链接（去除锚点后），Value 为新的相对链接（可包含 ..）
RELOCATED_LINKS: Dict[str, str] = {
    # 1) 训练配置文件说明（原：TRAINING_CONFIG_REFERENCE.md → 新：项目根 README 的训练配置章节）
    "TRAINING_CONFIG_REFERENCE.md": "../README.md",
    # 2) 多模型 LLM 配置指南（原：../configuration/llm-config.md → 新：核心服务 ConfigLoader 说明）
    "../configuration/llm-config.md": "../core-services/config-loader.md",
    # 3) 多模型 LLM 部署指南（原：../deployment/llm-deployment.md → 新：统一部署指南）
    "../deployment/llm-deployment.md": "../../05-development/DEPLOYMENT_GUIDE.md",
    # 4) HAM 设计规范（原：./HAM_design_spec.md → 新：./ham-design.md）
    "./HAM_design_spec.md": "./ham-design.md",
    "HAM_design_spec.md": "ham-design.md",
    # 5) MQTT 替代方案分析（原：../../../../07-research/experimental/mqtt-broker-analysis.md → 新：消息传输机制总览）
    "../../../../07-research/experimental/mqtt-broker-analysis.md": "../message-transport.md",
    # 6) HSP 规范（原：../technical_design/HSP_SPECIFICATION.md → 新：HSP 规范目录 README）
    "../technical_design/HSP_SPECIFICATION.md": "../../03-technical-architecture/communication/hsp-specification/README.md",
    # 7) HAM 设计（原：../technical_design/architecture/HAM_design_spec.md → 新：ham-design.md）
    "../technical_design/architecture/HAM_design_spec.md": "../../03-technical-architecture/memory-systems/ham-design.md",
    # 8) 代理协作（原：../technical_design/architecture/AGENT_COLLABORATION_FRAMEWORK.md → 新：agent-collaboration.md）
    "../technical_design/architecture/AGENT_COLLABORATION_FRAMEWORK.md": "../../04-advanced-concepts/agent-collaboration.md",
}


def _should_ignore(path: Path) -> bool:
    lower = str(path).lower()
    # 兼容 Windows 和 *nix 分隔符
    return any((f"{os.sep}{part}{os.sep}" in lower) or (f"/{part}/" in lower) or (f"\\{part}\\" in lower) for part in IGNORE_PARTS)
    def find_markdown_files(root_dir: str) -> List[Path]:
    """查找所有 Markdown 文件"""
    root_path = Path(root_dir)
    return [p for p in root_path.rglob("*.md") if not _should_ignore(p)]
    def extract_links(file_path: Path) -> List[Tuple[str, str]]:
    """从 Markdown 文件中提取链接"""
    try:

    with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 匹配 [text](link) 格式的链接
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    return matches
    except Exception as e:

    _ = print(f"❌ 读取文件失败: {file_path} - {e}")
    return []


def _normalize_link_path(link: str) -> str:
    """归一化链接路径（去除两端空格、尖括号、锚点、前置的./）"""
    link = (link or '').strip()
    # 去除尖括号包裹
    if link.startswith('<') and link.endswith('>')

    link = link[1:-1].strip()
    # 去除 fragment（#锚点）部分，仅验证路径存在性
    if '#' in link

    link = link.split('#', 1)[0].strip()
    # 规范化相对路径
    if link.startswith('./')

    link = link[2:]
    return link


def validate_link(base_path: Path, link: str) -> bool:
    """验证链接是否有效（支持重定位映射）"""
    # 跳过外部链接与纯锚点
    if link.startswith(('http://', 'https://', 'mailto:')):

    return True
    if not link or link.strip().startswith('#')

    return True

    # 归一化后得到用于匹配/拼接的路径
    link_path = _normalize_link_path(link)

    # 首先直接验证原路径
    target_path = (base_path.parent / link_path)
    try:

    target_resolved = target_path.resolve()
    except Exception:

    target_resolved = target_path  # 解析失败时，保持相对路径
    if target_resolved.exists()

    return True

    # 尝试重定位映射
    relocated = RELOCATED_LINKS.get(link_path)
    if relocated:

    relocated_path = (base_path.parent / relocated)
        try:

            relocated_resolved = relocated_path.resolve()
        except Exception:

            relocated_resolved = relocated_path
        if relocated_resolved.exists()

    if VERBOSE:
    _ = print(f"  🔁 路径重定位: '{link_path}' → '{relocated}' → 存在 ✅")
            return True
        else:

            if VERBOSE:


    _ = print(f"  🔁 路径重定位失败: '{link_path}' → '{relocated}' → 不存在 ❌")

    # 均未通过 → 无效
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 Markdown 文档中的内部链接")
    parser.add_argument('--root', default='.', help='扫描根目录（默认当前目录）')
    parser.add_argument('--ignore', default='', help='以逗号分隔的忽略目录名称（追加到默认忽略列表）')
    parser.add_argument('-v', '--verbose', action='store_true', help='打印有效链接的详细信息')
    # 新增：错误报告输出位置
    parser.add_argument('--report-json', default='docs_link_check_errors.json', help='输出无效链接 JSON 报告路径')
    parser.add_argument('--report-text', default='docs_link_check_errors.txt', help='输出无效链接纯文本报告路径')
    return parser.parse_args()


def main() -> None:
    """主函数"""
    global IGNORE_PARTS, VERBOSE
    args = parse_args()
    VERBOSE = VERBOSE or args.verbose
    # 合并忽略目录
    extra_ignores = {part.strip() for part in args.ignore.split(',') if part.strip()}:
    IGNORE_PARTS = set(IGNORE_PARTS) | extra_ignores

    _ = print("🔍 开始验证文档链接...")

    root_dir = args.root
    markdown_files = find_markdown_files(root_dir)

    broken_links: List[Tuple[Path, str, str]] = []
    total_links = 0

    for md_file in markdown_files:


    _ = print(f"\n📄 检查文件: {md_file}")
    links = extract_links(md_file)

        for text, link in links:


    total_links += 1
            if not validate_link(md_file, link)

    _ = broken_links.append((md_file, text, link))
                _ = print(f"  ❌ 无效链接: [{text}]({link})")
            else:

                if VERBOSE:


    _ = print(f"  ✅ 有效链接: [{text}]({link})")

    _ = print(f"\n📊 验证结果:")
    _ = print(f"总链接数: {total_links}")
    _ = print(f"无效链接数: {len(broken_links)}")

    # 生成报告文件，便于外部工具解析
    try:

    json_report = {
            _ = 'root': str(Path(root_dir).resolve()),
            'total_links': total_links,
            _ = 'broken_count': len(broken_links),
            'broken': [
                {
                    _ = 'file': str(p),
                    'text': t,
                    'link': l
                } for (p, t, l) in broken_links
            ]
    }
    Path(args.report_json).write_text(json.dumps(json_report, ensure_ascii=False, indent=2), encoding='utf-8')
    # 文本报告（更易於人工瀏覽）
    lines = [
            f"Root: {json_report['root']}",
            f"Total: {total_links}",
            _ = f"Broken: {len(broken_links)}",
            "",
    ]
        for p, t, l in broken_links[:1000]:

            _ = lines.append(f"{p}: [{t}]({l})")
    Path(args.report_text).write_text("\n".join(lines), encoding='utf-8')
    _ = print(f"📝 报告已生成: {args.report_json}, {args.report_text}")
    except Exception as e:

    _ = print(f"⚠️ 生成报告失败: {e}")

    if broken_links:


    _ = print(f"\n❌ 发现 {len(broken_links)} 个无效链接")
    return 1
    else:

    _ = print("✅ 所有链接都有效!")
    return 0


if __name__ == "__main__":



    _ = exit(main())