#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主修復腳本
整合所有修復步驟，按順序執行各個修復腳本

使用方法:
    python run_all_repairs.py [--check] [--fix] [--backup] [--verbose]
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('run_all_repairs')

# 項目根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 修復腳本列表，按執行順序排列
REPAIR_SCRIPTS = [
    'syntax_repair.py',    # 語法錯誤修復
    'path_repair.py',      # 路徑計算問題修復
    'structure_repair.py', # 文件結構修復
    'duplicate_fix.py',    # 重複開發問題修復
    'implementation_fix.py', # 未實作功能修復
    'config_repair.py',    # 配置文件修復
]

def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='執行所有修復腳本')
    parser.add_argument('--check', action='store_true', help='只檢查問題，不修復')
    parser.add_argument('--fix', action='store_true', help='修復發現的問題')
    parser.add_argument('--backup', action='store_true', help='修復前備份文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    parser.add_argument('--skip', type=str, help='跳過指定的修復腳本，用逗號分隔')
    
    args = parser.parse_args()
    
    # 如果沒有指定--check或--fix，默認為--check
    if not (args.check or args.fix):
        args.check = True
    
    return args

def setup_logging(verbose):
    """設置日誌級別"""
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def create_summary_report(results):
    """創建修復摘要報告"""
    summary_dir = PROJECT_ROOT / 'summaries'
    os.makedirs(summary_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = summary_dir / f'repair_summary_{timestamp}.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== 項目修復摘要報告 ===\n")
        f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("執行的修復腳本:\n")
        for script, result in results.items():
            status = "成功" if result['success'] else "失敗"
            f.write(f"- {script}: {status}\n")
            if 'issues_found' in result:
                f.write(f"  發現問題: {result['issues_found']}\n")
            if 'issues_fixed' in result:
                f.write(f"  修復問題: {result['issues_fixed']}\n")
        
        f.write("\n總結:\n")
        success_count = sum(1 for r in results.values() if r['success'])
        f.write(f"- 成功執行: {success_count}/{len(results)}\n")
        
        total_issues_found = sum(r.get('issues_found', 0) for r in results.values())
        total_issues_fixed = sum(r.get('issues_fixed', 0) for r in results.values())
        f.write(f"- 發現問題總數: {total_issues_found}\n")
        f.write(f"- 修復問題總數: {total_issues_fixed}\n")
    
    logger.info(f"修復摘要報告已保存至: {report_path}")
    return report_path

def run_repair_script(script_name, args):
    """執行單個修復腳本"""
    script_path = PROJECT_ROOT / 'repair_scripts' / script_name
    
    if not os.path.exists(script_path):
        logger.error(f"修復腳本不存在: {script_path}")
        return {
            'success': False,
            'error': f"腳本不存在: {script_path}"
        }
    
    cmd = [sys.executable, str(script_path)]
    
    if args.check:
        cmd.append('--check')
    if args.fix:
        cmd.append('--fix')
    if args.backup:
        cmd.append('--backup')
    if args.verbose:
        cmd.append('--verbose')
    
    logger.info(f"執行修復腳本: {script_name}")
    logger.debug(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 解析輸出以獲取問題數量
        stdout = result.stdout
        issues_found = 0
        issues_fixed = 0
        
        for line in stdout.split('\n'):
            if '發現' in line and '問題' in line:
                try:
                    issues_found = int(''.join(filter(str.isdigit, line.split('發現')[1].split('問題')[0])))
                except:
                    pass
            if '修復' in line and '問題' in line:
                try:
                    issues_fixed = int(''.join(filter(str.isdigit, line.split('修復')[1].split('問題')[0])))
                except:
                    pass
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'issues_found': issues_found,
            'issues_fixed': issues_fixed
        }
    except Exception as e:
        logger.error(f"執行腳本時出錯: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """主函數"""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger.info("開始執行項目修復...")
    
    # 解析要跳過的腳本
    skip_scripts = []
    if args.skip:
        skip_scripts = [s.strip() for s in args.skip.split(',')]
    
    # 執行所有修復腳本
    results = {}
    for script in REPAIR_SCRIPTS:
        if script in skip_scripts:
            logger.info(f"跳過修復腳本: {script}")
            continue
        
        result = run_repair_script(script, args)
        results[script] = result
        
        if result['success']:
            logger.info(f"成功執行修復腳本: {script}")
            if 'issues_found' in result:
                logger.info(f"發現 {result['issues_found']} 個問題")
            if 'issues_fixed' in result:
                logger.info(f"修復 {result['issues_fixed']} 個問題")
        else:
            logger.error(f"執行修復腳本失敗: {script}")
            if 'stderr' in result:
                logger.error(f"錯誤信息: {result['stderr']}")
    
    # 創建摘要報告
    report_path = create_summary_report(results)
    
    # 輸出總結
    success_count = sum(1 for r in results.values() if r['success'])
    logger.info(f"修復完成: {success_count}/{len(results)} 個腳本成功執行")
    
    if args.fix:
        logger.info("所有修復已應用到項目中")
    else:
        logger.info("僅執行了檢查模式，沒有應用任何修復")
        logger.info("使用 --fix 參數來應用修復")
    
    logger.info(f"詳細報告已保存至: {report_path}")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())