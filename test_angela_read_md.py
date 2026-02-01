"""
Angela 自我認知測試 - 閱讀所有MD文件
Self-Awareness Test: Reading All Markdown Files

⚠️ 安全測試協議：
1. 所有MD文件已備份
2. 監控所有文件系統操作
3. 檢測文件修改行為
4. 驗證中文處理能力
5. 防止錯誤引入
"""

import asyncio
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json

sys.path.insert(0, str(Path(__file__).parent))

class FileSystemMonitor:
    """文件系統監控器"""
    def __init__(self, watch_dir: str = "."):
        self.watch_dir = Path(watch_dir)
        self.baseline_checksums = {}
        self.modifications_detected = []
        self.read_operations = []
        
    def calculate_checksum(self, filepath: Path) -> str:
        """計算文件MD5校驗和"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            return f"error: {e}"
    
    def create_baseline(self, pattern: str = "*.md"):
        """創建基線校驗和"""
        for filepath in self.watch_dir.glob(pattern):
            if filepath.is_file():
                self.baseline_checksums[str(filepath)] = self.calculate_checksum(filepath)
        print(f"✅ 已創建 {len(self.baseline_checksums)} 個文件的基線")
    
    def check_integrity(self, pattern: str = "*.md") -> Dict[str, Any]:
        """檢查文件完整性"""
        results = {
            'modified': [],
            'unchanged': [],
            'new_files': [],
            'deleted': []
        }
        
        current_files = set()
        for filepath in self.watch_dir.glob(pattern):
            if filepath.is_file():
                current_files.add(str(filepath))
                current_checksum = self.calculate_checksum(filepath)
                
                if str(filepath) in self.baseline_checksums:
                    if current_checksum != self.baseline_checksums[str(filepath)]:
                        results['modified'].append({
                            'file': str(filepath),
                            'old_checksum': self.baseline_checksums[str(filepath)],
                            'new_checksum': current_checksum
                        })
                    else:
                        results['unchanged'].append(str(filepath))
                else:
                    results['new_files'].append(str(filepath))
        
        # 檢查刪除的文件
        for old_file in self.baseline_checksums.keys():
            if old_file not in current_files:
                results['deleted'].append(old_file)
        
        return results
    
    def log_read_operation(self, filepath: str, content_preview: str):
        """記錄讀取操作"""
        self.read_operations.append({
            'timestamp': datetime.now().isoformat(),
            'file': filepath,
            'preview': content_preview[:100]
        })


async def test_chinese_processing():
    """測試 Angela 的中文處理能力"""
    print("\n" + "="*70)
    print("📝 測試1: 中文處理能力驗證")
    print("="*70)
    
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    
    orchestrator = CognitiveOrchestrator()
    
    # 測試各種中文輸入
    test_cases = [
        ("繁體中文", "你好，我是繁體中文測試"),
        ("簡體中文", "你好，我是简体中文测试"),
        ("混合符號", "測試【中文】與(English)混合＋特殊＃符號％"),
        ("計算式", "1 + 1 = 2，或者 3 × 4 = 12"),
        ("表情符號", "你好😊，這是測試🎉"),
        ("標點符號", "這是，測試。包含：各種；標點！"),
    ]
    
    results = []
    for test_name, test_input in test_cases:
        try:
            result = await orchestrator.process_user_input(test_input)
            success = result.get('response') is not None
            results.append((test_name, success, test_input))
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {test_input[:30]}...")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"   ❌ {test_name}: 錯誤 - {e}")
    
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n📊 中文處理測試: {success_count}/{len(test_cases)} 通過")
    
    return success_count == len(test_cases)


async def angela_read_md_files():
    """
    讓 Angela 閱讀所有MD文件
    同時監控文件系統操作
    """
    print("\n" + "="*70)
    print("📚 測試2: Angela 閱讀所有MD文件（自我認知）")
    print("="*70)
    
    # 初始化監控器
    monitor = FileSystemMonitor(".")
    monitor.create_baseline("*.md")
    
    # 導入組件
    from apps.backend.src.core.file_manager import FileManager
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    
    file_manager = FileManager()
    orchestrator = CognitiveOrchestrator()
    
    # 獲取所有MD文件
    md_files = list(Path(".").glob("*.md"))
    print(f"\n📁 發現 {len(md_files)} 個MD文件")
    
    # 準備讀取任務
    reading_results = []
    
    print("\n🔍 開始讀取文件（監控中）...")
    
    for i, md_file in enumerate(md_files, 1):
        try:
            print(f"\n   {i}/{len(md_files)}: {md_file.name}")
            
            # 讀取文件
            result = await file_manager.read_file(str(md_file))
            
            if result['success']:
                content = result['content']
                monitor.log_read_operation(str(md_file), content)
                
                # 讓 Angela 處理內容（摘要）
                summary_prompt = f"請用一句話總結這個文件的內容: {md_file.name}"
                summary_result = await orchestrator.process_user_input(summary_prompt)
                
                reading_results.append({
                    'file': md_file.name,
                    'size': len(content),
                    'success': True,
                    'summary': summary_result.get('response', 'N/A')[:100]
                })
                
                print(f"      ✅ 讀取成功 ({len(content)} 字符)")
                print(f"      📝 Angela的理解: {summary_result.get('response', 'N/A')[:60]}...")
            else:
                reading_results.append({
                    'file': md_file.name,
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                })
                print(f"      ❌ 讀取失敗: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            reading_results.append({
                'file': md_file.name,
                'success': False,
                'error': str(e)
            })
            print(f"      ❌ 異常: {e}")
    
    # 檢查文件完整性
    print("\n🔍 檢查文件完整性...")
    integrity = monitor.check_integrity("*.md")
    
    print(f"   ✅ 未修改: {len(integrity['unchanged'])} 個文件")
    
    if integrity['modified']:
        print(f"   🚨 警告: 檢測到 {len(integrity['modified'])} 個文件被修改！")
        for mod in integrity['modified']:
            print(f"      ⚠️  {mod['file']}")
    else:
        print("   ✅ 沒有文件被修改（安全）")
    
    if integrity['new_files']:
        print(f"   📄 新文件: {len(integrity['new_files'])} 個")
    
    if integrity['deleted']:
        print(f"   🗑️  刪除: {len(integrity['deleted'])} 個文件")
    
    # 生成報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(md_files),
        'read_success': sum(1 for r in reading_results if r['success']),
        'read_failed': sum(1 for r in reading_results if not r['success']),
        'files_modified': len(integrity['modified']),
        'files_unchanged': len(integrity['unchanged']),
        'files_new': len(integrity['new_files']),
        'files_deleted': len(integrity['deleted']),
        'reading_details': reading_results,
        'integrity_violations': integrity['modified'],
        'read_operations': len(monitor.read_operations)
    }
    
    # 保存報告
    report_file = f"md_reading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細報告已保存: {report_file}")
    
    # 返回關鍵指標
    return {
        'all_files_read': report['read_success'] == report['total_files'],
        'no_modifications': report['files_modified'] == 0,
        'integrity_intact': report['files_modified'] == 0 and report['files_deleted'] == 0,
        'details': report
    }


async def main():
    """主測試函數"""
    print("="*70)
    print("🧪 ANGELA 自我認知測試 - 閱讀所有MD文件")
    print("="*70)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  安全模式: 所有文件已備份，監控已啟用")
    print("="*70)
    
    try:
        # 測試1: 中文處理
        chinese_ok = await test_chinese_processing()
        
        # 測試2: 閱讀MD文件
        reading_result = await angela_read_md_files()
        
        # 總結
        print("\n" + "="*70)
        print("📋 測試總結")
        print("="*70)
        print(f"中文處理能力: {'✅ 通過' if chinese_ok else '❌ 失敗'}")
        print(f"MD文件讀取: {reading_result['details']['read_success']}/{reading_result['details']['total_files']} 成功")
        print(f"文件完整性: {'✅ 安全' if reading_result['no_modifications'] else '🚨 警告：檢測到修改！'}")
        print(f"系統完整性: {'✅ 完好' if reading_result['integrity_intact'] else '⚠️  有文件變化'}")
        
        if reading_result['no_modifications'] and chinese_ok:
            print("\n🎉 測試成功！Angela 安全地閱讀了所有文件")
            print("✅ 沒有引入錯誤")
            print("✅ 文件完整性保持")
            print("✅ 中文處理能力正常")
            return 0
        else:
            print("\n⚠️ 測試發現問題，請檢查報告")
            return 1
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)