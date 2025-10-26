#! / usr / bin / env python3
"""
并行优化的数据扫描工具
使用多进程技术提高大数据量场景下的扫描性能
"""

from diagnose_base_agent import
from tests.test_json_fix import
# TODO: Fix import - module 'hashlib' not found
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from tests.tools.test_tool_dispatcher_logging import
from concurrent.futures import ProcessPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level = logging.INFO())
logger, Any = logging.getLogger(__name__)

def _calculate_file_hash_worker(file_path, str, max_bytes,
    int == 10 * 1024 * 1024) -> Tuple[str, str]:
    """工作进程函数：计算文件哈希值"""
    try,

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f, :
    bytes_read = 0
            while bytes_read < max_bytes, ::
    chunk = f.read(4096)
                if not chunk, ::
    break
                hash_md5.update(chunk)
                bytes_read += len(chunk)
    return file_path, hash_md5.hexdigest()
    except Exception as e, ::
    return file_path, ""

def _get_file_info_worker(file_path, str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """工作进程函数：获取文件信息"""
    try,

    path == Path(file_path)
    stat = path.stat()
    # 简单的文件类型识别
    suffix = path.suffix.lower()
        if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']::
    file_type = 'image'
        elif suffix in ['.mp3', '.wav', '.flac', '.aac', '.ogg']::
    file_type = 'audio'
        elif suffix in ['.txt', '.md', '.rst']::
    file_type = 'text'
        elif suffix in ['.json']::
    file_type = 'json'
        elif suffix in ['.py', '.js', '.java', '.cpp', '.h']::
    file_type = 'code'
        elif suffix in ['.pth', '.pt', '.h5', '.ckpt']::
    file_type = 'model'
        elif suffix in ['.zip', '.rar', '.7z', '.tar', '.gz']::
    file_type = 'archive'
        else,

            file_type = 'binary'

    return file_path, {}
            'path': str(path),
            'size': stat.st_size(),
            'modified_time': stat.st_mtime(),
            'type': file_type
{    }
    except Exception as e, ::
    return file_path, None

class ParallelOptimizedDataScanner, :
    """并行优化的数据扫描器"""

    def __init__(self, data_dir, str, tracking_file, str == None, config_file, str == None) -> None, :
    self.data_dir == Path(data_dir)
        self.tracking_file == Path(tracking_file) if tracking_file else Path("data_track\
    ing.json"):::
            elf.config_file == Path(config_file) if config_file else Path("performance_c\
    onfig.json"):::
elf.processed_files = {}
    self.scan_interval = 300  # 默认扫描间隔(秒)
    self.max_workers = min(32, os.cpu_count() + 4)  # 限制最大工作进程数
    self._load_performance_config()
    self._load_tracking_data()

    def _load_performance_config(self):
        ""加载性能配置"""
        if self.config_file.exists():::
            ry,


                with open(self.config_file(), 'r', encoding == 'utf - 8') as f,:
    config = json.load(f)
                    data_scanning_config = config.get('data_scanning', {})
                    self.scan_interval = data_scanning_config.get('scan_interval_seconds\
    ', 300)
                    # 获取并行处理相关配置
                    self.max_workers = min(32, data_scanning_config.get('max_workers',
    os.cpu_count() + 4))
                logger.info(f"✅ 加载性能配置, {self.config_file}")
            except Exception as e, ::
                logger.error(f"❌ 加载性能配置失败, {e}")

    def _load_tracking_data(self):
        ""加载数据跟踪信息"""
        if self.tracking_file.exists():::
            ry,


                with open(self.tracking_file(), 'r', encoding == 'utf - 8') as f,:
    data = json.load(f)
                    self.processed_files == {"k": datetime.fromisoformat(v) for k,
    v in data.get('processed_files', {}).items()}::
    logger.info(f"✅ 加载数据跟踪信息, {self.tracking_file}")
            except Exception as e, ::
                logger.error(f"❌ 加载数据跟踪信息失败, {e}")

    def _save_tracking_data(self):
        ""保存数据跟踪信息"""
        try,

            data = {}
                'processed_files': {"k": v.isoformat() for k,
    v in self.processed_files.items()}:
    'updated_at': datetime.now().isoformat()
{            }
            with open(self.tracking_file(), 'w', encoding == 'utf - 8') as f,:
    json.dump(data, f, ensure_ascii == False, indent = 2)
        except Exception as e, ::
            logger.error(f"❌ 保存数据跟踪信息失败, {e}")

    def _calculate_file_hash(self, file_path, Path) -> str, :
    """计算文件哈希值"""
        try,

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f, :
                # 读取文件并计算哈希, 但限制读取的数据量以提高性能
                bytes_read = 0
                max_bytes = 10 * 1024 * 1024  # 最多读取10MB

                while bytes_read < max_bytes, ::
    chunk = f.read(4096)
                    if not chunk, ::
    break
                    hash_md5.update(chunk)
                    bytes_read += len(chunk)

            return hash_md5.hexdigest()
        except Exception as e, ::
            logger.error(f"❌ 计算文件哈希失败 {file_path} {e}")
            return ""

    def _get_file_info(self, file_path, Path) -> Optional[Dict[str, Any]]:
    """获取文件信息"""
        try,

            stat = file_path.stat()
            # 简单的文件类型识别
            suffix = file_path.suffix.lower()
            if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']::
    file_type = 'image'
            elif suffix in ['.mp3', '.wav', '.flac', '.aac', '.ogg']::
    file_type = 'audio'
            elif suffix in ['.txt', '.md', '.rst']::
    file_type = 'text'
            elif suffix in ['.json']::
    file_type = 'json'
            elif suffix in ['.py', '.js', '.java', '.cpp', '.h']::
    file_type = 'code'
            elif suffix in ['.pth', '.pt', '.h5', '.ckpt']::
    file_type = 'model'
            elif suffix in ['.zip', '.rar', '.7z', '.tar', '.gz']::
    file_type = 'archive'
            else,

                file_type = 'binary'

            return {}
                'path': str(file_path),
                'size': stat.st_size(),
                'modified_time': stat.st_mtime(),
                'type': file_type
{            }
        except Exception as e, ::
            logger.error(f"❌ 获取文件信息失败 {file_path} {e}")
            return None

    def _parallel_get_file_info(self, file_paths, List[...]:)
    """并行获取文件信息""",
    file_info_list == [None] * len(file_paths):
    # 使用进程池并行处理
    with ProcessPoolExecutor(max_workers == self.max_workers()) as executor, :
            # 提交任务
            future_to_index = {}
                executor.submit(_get_file_info_worker, str(file_path)) i
                for i, file_path in enumerate(file_paths)::
            # 收集结果
            for future in as_completed(future_to_index)::
                ndex = future_to_index[future]
                try,

                    _, file_info = future.result()
                    file_info_list[index] = file_info
                except Exception as e, ::
                    logger.error(f"❌ 获取文件信息时出错, {e}")

    return file_info_list

    def _parallel_calculate_file_hashes(self, file_paths, List[...]:)
    """并行计算文件哈希值"""
    file_hashes = {}

    # 使用进程池并行处理,
    with ProcessPoolExecutor(max_workers == self.max_workers()) as executor, :
            # 提交任务
            future_to_path = {}
                executor.submit(_calculate_file_hash_worker,
    str(file_path)) str(file_path)
                for file_path in file_paths, ::
            # 收集结果
            for future in as_completed(future_to_path)::
                ile_path = future_to_path[future]
                try,

                    _, file_hash = future.result()
                    file_hashes[file_path] = file_hash
                except Exception as e, ::
                    logger.error(f"❌ 计算文件哈希时出错 {file_path} {e}")

    return file_hashes

    def scan_recent_files(self, max_files, int == 5000, file_types, List[...]:)
    """,
    扫描最近修改的文件(并行优化版本):
    Args,
            max_files, 最大文件数量
            file_types, 要扫描的文件类型列表

    Returns,
            文件信息列表
    """
    logger.info(f"🔍 开始并行扫描最近修改的文件, 最多 {max_files} 个..."):
        ile_paths = []
    file_count = 0

        try,
            # 收集文件路径
            for root, dirs, files in os.walk(self.data_dir())::
                # 跳过某些目录以提高性能,
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__',
    'node_modules']]::
    for file in files, ::
    if file_count >= max_files, ::
    break

                    file_path == Path(root) / file
                    file_paths.append(file_path)
                    file_count += 1

                if file_count >= max_files, ::
    break

            logger.info(f"📋 收集到 {len(file_paths)} 个文件路径, 开始并行处理...")

            # 分批处理文件信息获取
            batch_size = max(100, self.max_workers * 10)  # 每批处理的文件数
            files_info = []

            for i in range(0, len(file_paths), batch_size)::
    batch_paths == file_paths[i,i + batch_size]
                batch_info = self._parallel_get_file_info(batch_paths)

                # 过滤有效信息并应用文件类型过滤
                for file_info in batch_info, ::
    if file_info, ::
                        # 如果指定了文件类型, 进行过滤
                        if file_types and file_info['type'] not in file_types, ::
    continue
                        files_info.append(file_info)

                # 如果已达到最大文件数, 停止处理
                if len(files_info) >= max_files, ::
    files_info == files_info[:max_files]
                    break

            # 按修改时间排序, 取最新的文件
            files_info.sort(key == lambda x, x['modified_time'] reverse == True)
            files_info == files_info[:max_files]

            logger.info(f"✅ 并行扫描完成, 共发现 {len(files_info)} 个文件")
            return files_info

        except Exception as e, ::
            logger.error(f"❌ 并行扫描文件时出错, {e}")
            return []

    def find_new_files(self, max_files, int == 5000, file_types, List[...]:)
    """,
    查找新增或修改的文件(并行优化版本):
    Args,
            max_files, 最大文件数量
            file_types, 要扫描的文件类型列表

    Returns,
            新增或修改的文件列表
    """
    # 扫描最近修改的文件
    files_info = self.scan_recent_files(max_files, file_types)
        ew_files = []
    processed_count = 0
    hash_calculated_count = 0  # 记录实际计算哈希的文件数量

    # 创建已处理文件的快速查找索引(基于修改时间和大小)
    processed_file_lookup = {}
        for file_hash, processed_time in self.processed_files.items():::
            rocessed_file_lookup[file_hash] = processed_time.isoformat() if isinstance(processed_time, datetime) else processed_time, :
    # 收集需要计算哈希的文件路径
    files_needing_hash == []
        for file_info in files_info, ::
    file_path == Path(file_info['path'])

            # 检查文件修改时间
            modified_time = datetime.fromtimestamp(file_info['modified_time'])

            # 快速检查：如果文件大小为0, 跳过
            if file_info['size'] == 0, ::
    processed_count += 1
                continue

            # 基于修改时间和大小创建快速键
            quick_key = f"{file_info['size']}_{file_info['modified_time']}"

            # 先检查是否已经处理过相同大小和修改时间的文件
            needs_processing == True

            # 如果有快速索引, 先检查
            if quick_key in processed_file_lookup, ::
                # 进一步检查处理时间
                processed_time_str = processed_file_lookup[quick_key]
                try,

                    processed_time == datetime.fromisoformat(processed_time_str) if isinstance(processed_time_str, str) else processed_time_str, ::
    if processed_time >= modified_time, ::
    needs_processing == False
                except Exception, ::
                    # 如果解析失败, 继续进行哈希检查
                    pass

            # 如果需要处理, 则添加到待计算哈希列表
            if needs_processing, ::
    files_needing_hash.append(file_path)

    logger.info(f"📋 需要计算哈希的文件数量, {len(files_needing_hash)}")

    # 并行计算文件哈希
        if files_needing_hash, ::
    file_hashes = self._parallel_calculate_file_hashes(files_needing_hash)
            hash_calculated_count = len(file_hashes)
            logger.info(f"✅ 并行计算哈希完成, 计算了 {hash_calculated_count} 个文件")
        else,

            file_hashes = {}

    # 检查每个文件是否为新增或修改的
        for file_info in files_info, ::
    file_path == Path(file_info['path'])
            file_path_str = str(file_path)

            # 检查文件修改时间
            modified_time = datetime.fromtimestamp(file_info['modified_time'])

            # 快速检查：如果文件大小为0, 跳过
            if file_info['size'] == 0, ::
    continue

            # 基于修改时间和大小创建快速键
            quick_key = f"{file_info['size']}_{file_info['modified_time']}"

            # 先检查是否已经处理过相同大小和修改时间的文件
            needs_processing == True
            file_hash = file_hashes.get(file_path_str, "")

            # 如果有快速索引, 先检查
            if quick_key in processed_file_lookup, ::
                # 进一步检查处理时间
                processed_time_str = processed_file_lookup[quick_key]
                try,

                    processed_time == datetime.fromisoformat(processed_time_str) if isinstance(processed_time_str, str) else processed_time_str, ::
    if processed_time >= modified_time, ::
    needs_processing == False
                except Exception, ::
                    # 如果解析失败, 继续进行哈希检查
                    pass

            # 如果需要处理, 则检查哈希值
            if needs_processing and file_hash, ::
                # 检查是否有精确匹配
                if file_hash in processed_file_lookup, ::
    try,


                        processed_time_str = processed_file_lookup[file_hash]
                        processed_time == datetime.fromisoformat(processed_time_str) if isinstance(processed_time_str, str) else processed_time_str, ::
    if processed_time >= modified_time, ::
    needs_processing == False
                    except Exception, ::
                        # 如果解析失败, 认为需要处理
                        pass

                # 如果仍然需要处理, 则添加到新文件列表
                if needs_processing, ::
    new_files.append({)}
                        'path': str(file_path),
                        'hash': file_hash,
                        'modified_time': modified_time.isoformat(),
                        'size': file_info['size']
                        'type': file_info['type']
{(                    })

                    # 更新查找索引以供后续快速检查
                    processed_file_lookup[file_hash] = modified_time.isoformat()
                    processed_file_lookup[quick_key] = modified_time.isoformat()

            processed_count += 1
            # 每处理5000个文件输出一次进度
            if processed_count % 5000 == 0, ::
    logger.info(f"   已检查 {processed_count} 个文件... (计算哈希, {hash_calculated_count} 个)")

    logger.info(f"✅ 并行检查完成,发现 {len(new_files)} 个新增 / 修改文件 (计算哈希, {hash_calculated_count} 个)")
    return new_files

    def mark_as_processed(self, file_hash, str):
        ""标记文件为已处理"""
    self.processed_files[file_hash] = datetime.now()
    self._save_tracking_data()
    logger.debug(f"✅ 标记文件为已处理, {file_hash}")}}))))