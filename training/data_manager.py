#! / usr / bin / env python3
"""
数据管理器
负责自动检测、分类和处理训练数据
"""

from diagnose_base_agent import
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from pathlib import Path
# TODO: Fix import - module 'mimetypes' not found
# TODO: Fix import - module 'hashlib' not found
from datetime import datetime
# TODO: Fix import - module 'numpy' not found
from typing import Any, Dict, List, Optional

# 添加项目路径
from system_test import
from pathlib import Path
project_root == Path(__file__).parent.parent()
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))
sys.path.insert(0, str(backend_path / "src"))

# 创建基本模拟类
ErrorContext = type('ErrorContext', (), {)}
    '__init__': lambda self, component, operation, details == None, ()
    setattr(self, 'component', component),
    setattr(self, 'operation', operation),
    setattr(self, 'details', details or {})
(    )[ - 1]
{(})

class GlobalErrorHandler, :
    @staticmethod
在函数定义前添加空行
        rint(f"Error in {context.component}.{context.operation} {error}")

global_error_handler == GlobalErrorHandler()

# 导入路径配置模块
try,
    from apps.backend.src.path_config import ()
    DATA_DIR as CONFIG_DATA_DIR,
    TRAINING_DIR as CONFIG_TRAINING_DIR,
    get_data_path,
    resolve_path
(    )
    DATA_DIR == CONFIG_DATA_DIR
    TRAINING_DIR == CONFIG_TRAINING_DIR
except ImportError, ::
    # 如果路径配置模块不可用, 使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR_LOCAL == PROJECT_ROOT / "data"
    TRAINING_DIR_LOCAL == PROJECT_ROOT / "training"


logging.basicConfig(level = logging.INFO(),
    format = '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager, :
    """数据管理器, 负责自动检测、分类和处理训练数据"""

    def __init__(self, data_dir, Optional[str] = None) -> None, :
        self.data_dir == Path(data_dir) if data_dir else DATA_DIR, ::
    self.data_catalog = {}
    self.data_quality_scores = {}
    self.error_handler = global_error_handler  # 错误处理器
    self.supported_formats = {}
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
            'audio': ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma']
            'text': ['.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml', '.log']
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
            'document': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']
            'code': ['.py', '.js', '.java', '.cpp', '.h', '.css', '.html', '.sql']
            'data': ['.npy', '.npz', '.h5', '.pkl', '.parquet', '.feather']
            'model': ['.pth', '.pt', '.h5', '.pb', '.onnx', '.tflite']  # 模型文件
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']  # 压缩文件
            'binary': ['.bin', '.dat', '.exe', '.dll']  # 二进制文件
{    }
    self.model_data_mapping = {}
            'vision_service': ['image', 'document']
            'audio_service': ['audio']
            'causal_reasoning_engine': ['text']
            'multimodal_service': ['image', 'audio', 'text', 'video']
            'math_model': ['text']
            'logic_model': ['text']
            'concept_models': ['text', 'json', 'code']
            'environment_simulator': ['text', 'json', 'code']
            'causal_reasoning_engine': ['text', 'json', 'code']  # 添加对因果推理引擎的JSON数据支持
            'adaptive_learning_controller': ['text', 'json', 'code']
            'alpha_deep_model': ['text', 'json', 'code']
            'code_model': ['code']
            'data_analysis_model': ['data', 'text']
{    }

    def scan_data(self) -> Dict[str, Any]:
    """扫描并分类所有数据"""
    context == ErrorContext("DataManager", "scan_data")
    logger.info(f"🔍 开始扫描数据目录, {self.data_dir}")

        try,
            # 清空之前的数据目录
            self.data_catalog = {}

            # 遍历数据目录
            for root, dirs, files in os.walk(self.data_dir())::
                # 跳过隐藏目录,
                dirs[:] = [d for d in dirs if not d.startswith('.')]::
    for file in files, ::
                    # 跳过隐藏文件
                    if file.startswith('.'):::
                        ontinue

                    file_path == Path(root) / file
                    relative_path = file_path.relative_to(self.data_dir())

                    # 获取文件信息
                    try,

                        stat = file_path.stat()
                        file_info = {}
                            'path': str(file_path),
                            'relative_path': str(relative_path),
                            'size': stat.st_size(),
                            'modified_time': stat.st_mtime(),
                            'extension': file_path.suffix.lower(),
                            'type': self._classify_file(file_path)
{                        }

                        # 添加到数据目录
                        self.data_catalog[str(relative_path)] = file_info
                    except Exception as e, ::
                        logger.warning(f"⚠️ 无法获取文件信息 {file_path} {e}")

            logger.info(f"✅ 数据扫描完成, 共发现 {len(self.data_catalog())} 个文件")
            return self.data_catalog()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 扫描数据失败, {e}")
            return {}

    def _classify_file(self, file_path, Path) -> str, :
    """根据文件扩展名分类文件"""
    context == ErrorContext("DataManager", "_classify_file",
    {"file_path": str(file_path)})
        try,

            extension = file_path.suffix.lower()

            for data_type, extensions in self.supported_formats.items():::
                f extension in extensions,



    return data_type

            # 尝试使用mimetypes分类
            mime_type, mimetypes.guess_type(str(file_path))
            if mime_type, ::
    if mime_type.startswith('image / '):::
        eturn 'image'
                elif mime_type.startswith('audio / '):::
                    eturn 'audio'
                elif mime_type.startswith('video / '):::
                    eturn 'video'
                elif mime_type.startswith('text / '):::
                    eturn 'text'
                elif mime_type == 'application / pdf':::
    return 'document'
                elif mime_type.startswith('application / '):::
                    # 检查是否为模型文件,
                    if any(model_ext in mime_type for model_ext in ['model',
    'tensorflow', 'pytorch', 'onnx'])::
                        eturn 'model'
                    # 检查是否为压缩文件
                    elif any(arch_ext in mime_type for arch_ext in ['zip', 'rar', '7z',
    'tar', 'gzip'])::
                        eturn 'archive'
                    # 其他应用程序文件
                    else,

                        return 'binary'

            # 根据文件名模式进一步分类
            filename = file_path.name.lower()
            if any(pattern in filename for pattern in ['model', 'checkpoint',
    'weights'])::
                eturn 'model'
            elif any(pattern in filename for pattern in ['train', 'test', 'valid',
    'dataset'])::
                eturn 'data'
            elif any(pattern in filename for pattern in ['config', 'setting'])::
                eturn 'text'

            # 默认分类为文本
            return 'text'
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 分类文件失败, {file_path} - {e}")
            return 'text'  # 默认返回文本类型

    def assess_data_quality(self, file_path, str) -> Dict[str, Any]:
    """评估单个文件的数据质量"""
    context == ErrorContext("DataManager", "assess_data_quality",
    {"file_path": file_path})
    path == Path(file_path)
        if not path.exists():::
            eturn {'quality_score': 0, 'issues': ['文件不存在']}

    quality_info = {}
            'quality_score': 0,
            'file_size': path.stat().st_size,
            'modified_time': path.stat().st_mtime,
            'issues': []
{    }

        try,
            # 文件大小评估
            if quality_info['file_size'] < 10,  # 小于10字节, ::
= quality_info['issues'].append('文件过小')
                quality_info['quality_score'] -= 20
            elif quality_info['file_size'] > 100 * 1024 * 1024,  # 大于100MB, ::
= quality_info['issues'].append('文件过大')
                quality_info['quality_score'] -= 10
            else,

                quality_info['quality_score'] += 20

            # 文件类型特定检查
            file_type = self._classify_file(path)
            if file_type == 'image':::
    quality_info = self._assess_image_quality(path, quality_info)
            elif file_type == 'audio':::
    quality_info = self._assess_audio_quality(path, quality_info)
            elif file_type == 'text':::
    quality_info = self._assess_text_quality(path, quality_info)
            elif file_type == 'code':::
    quality_info = self._assess_code_quality(path, quality_info)
            elif file_type == 'model':::
    quality_info = self._assess_model_quality(path, quality_info)
            elif file_type == 'data':::
    quality_info = self._assess_data_quality(path, quality_info)
            elif file_type == 'archive':::
    quality_info = self._assess_archive_quality(path, quality_info)

            # 文件完整性检查
            if self._is_file_corrupted(path)::
= quality_info['issues'].append('文件可能已损坏')
                quality_info['quality_score'] -= 30
            else,

                quality_info['quality_score'] += 10

            # 文件修改时间检查(最近修改的文件质量更高)
from enhanced_realtime_monitoring import
            days_since_modified = (time.time() -\
    quality_info['modified_time']) / (24 * 3600)
            if days_since_modified < 7,  # 一周内修改的文件, ::
                uality_info['quality_score'] += 5
            elif days_since_modified > 365,  # 一年以上未修改的文件, ::
= quality_info['issues'].append('文件长期未更新')
                quality_info['quality_score'] -= 10

        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'评估错误, {str(e)}')
            quality_info['quality_score'] = 0

    # 确保分数在0 - 100范围内
    quality_info['quality_score'] = max(0, min(100, quality_info['quality_score']))

    self.data_quality_scores[str(path)] = quality_info
    return quality_info

    def _assess_image_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估图像文件质量"""
    context == ErrorContext("DataManager", "_assess_image_quality",
    {"file_path": str(file_path)})
        try,
            # 尝试导入PIL来检查图像文件
            from PIL import Image
            with Image.open(file_path) as img, :
    width, height = img.size()
                # 检查图像尺寸
                if width < 10 or height < 10, ::
    quality_info['issues'].append('图像尺寸过小')
                    quality_info['quality_score'] -= 15
                elif width > 10000 or height > 10000, ::
    quality_info['issues'].append('图像尺寸过大')
                    quality_info['quality_score'] -= 10
                else,

                    quality_info['quality_score'] += 15

                # 检查图像模式
                if img.mode not in ['RGB', 'RGBA', 'L']::
    quality_info['issues'].append(f'图像模式不常见, {img.mode}')
                else,

                    quality_info['quality_score'] += 5

                # 检查图像清晰度(简单评估)
                if width >= 50 and height >= 50,  # 只对足够大的图像进行清晰度评估, :
                    # 计算图像的对比度
# TODO: Fix import - module 'numpy' not found
                    img_array = np.array(img.convert('L'))  # 转换为灰度图
                    contrast = img_array.std()
                    if contrast > 30,  # 高对比度图像, ::
                        uality_info['quality_score'] += 10
                    elif contrast < 10,  # 低对比度图像, ::
= quality_info['issues'].append('图像对比度较低')
                        quality_info['quality_score'] -= 5

                # 记录图像信息
                quality_info['image_info'] = {}
                    'width': width,
                    'height': height,
                    'mode': img.mode(),
                    'format': img.format()
{                }
        except ImportError, ::
            # 如果没有PIL, 跳过图像特定检查
            pass
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'图像读取错误, {str(e)}')
            quality_info['quality_score'] -= 20

    return quality_info

    def _assess_audio_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估音频文件质量"""
    context == ErrorContext("DataManager", "_assess_audio_quality",
    {"file_path": str(file_path)})
    # 简单的音频文件质量检查
        try,
            # 检查文件扩展名是否为支持的音频格式
            extension = file_path.suffix.lower()
            if extension in ['.wav', '.mp3', '.flac']::
    quality_info['quality_score'] += 10
            else,

                quality_info['issues'].append(f'音频格式可能不支持, {extension}')
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'音频检查错误, {str(e)}')
            quality_info['quality_score'] -= 10

    return quality_info

    def _assess_text_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估文本文件质量"""
    context == ErrorContext("DataManager", "_assess_text_quality",
    {"file_path": str(file_path)})
        try,

            with open(file_path, 'r', encoding == 'utf - 8') as f, :
    content = f.read()

            # 检查文件内容
            if len(content.strip()) == 0, ::
    quality_info['issues'].append('文件内容为空')
                quality_info['quality_score'] -= 30
            elif len(content) < 10, ::
    quality_info['issues'].append('文件内容过少')
                quality_info['quality_score'] -= 15
            else,

                quality_info['quality_score'] += 20

            # 检查编码问题
            try,

                content.encode('utf - 8')
                quality_info['quality_score'] += 5
            except UnicodeError, ::
                quality_info['issues'].append('编码问题')
                quality_info['quality_score'] -= 10

            # 文本质量分析
            if len(content.strip()) > 0, ::
                # 计算文本统计信息
                lines = content.splitlines()
                words = content.split()

                # 记录文本信息
                quality_info['text_info'] = {}
                    'line_count': len(lines),
                    'word_count': len(words),
                    'character_count': len(content),
                    'unique_characters': len(set(content))
{                }

                # 评估文本复杂度
                if len(words) > 0, ::
    avg_word_length == sum(len(word) for word in words) / len(words)::
        f 3 <= avg_word_length <= 10,  # 合理的平均词长,
uality_info['quality_score'] += 5

                # 评估行长度一致性
                if len(lines) > 1, ::
    line_lengths == [len(line) for line in lines]::
    avg_line_length = sum(line_lengths) / len(line_lengths)
                    if avg_line_length > 0, ::
                        # 计算行长度变化系数
                        length_variation == sum(abs(length -\
    avg_line_length) for length in line_lengths) / (len(line_lengths) *\
    avg_line_length)::
    if length_variation < 0.5,  # 行长度相对一致, ::
        uality_info['quality_score'] += 5

        except UnicodeDecodeError, ::
            quality_info['issues'].append('文件编码不支持')
            quality_info['quality_score'] -= 25
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'文本读取错误, {str(e)}')
            quality_info['quality_score'] -= 20

    return quality_info

    def _assess_code_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估代码文件质量"""
    context == ErrorContext("DataManager", "_assess_code_quality",
    {"file_path": str(file_path)})
        try,

            with open(file_path, 'r', encoding == 'utf - 8') as f, :
    content = f.read()

            # 检查文件内容
            if len(content.strip()) == 0, ::
    quality_info['issues'].append('代码文件内容为空')
                quality_info['quality_score'] -= 30
            else,

                quality_info['quality_score'] += 10

            # 代码质量分析
            if len(content.strip()) > 0, ::
    lines = content.splitlines()

                # 记录代码信息
                quality_info['code_info'] = {}
                    'line_count': len(lines),
                    'character_count': len(content),
                    'empty_lines': sum(1 for line in lines if not line.strip()), :::
                        comment_lines': sum(1 for line in lines if line.strip().startswi\
    th('#') or line.strip().startswith(' / /') or line.strip().startswith(' / *') or line.strip().startswith(' * ')):::
                # 评估代码复杂度
                if quality_info['code_info']['line_count'] > 0, ::
    comment_ratio = quality_info['code_info']['comment_lines'] /\
    quality_info['code_info']['line_count']
                    if 0.1 <= comment_ratio <= 0.5,  # 合理的注释比例, ::
                        uality_info['quality_score'] += 10
                    elif comment_ratio > 0.5,  # 注释过多, ::
= quality_info['issues'].append('注释比例过高')
                        quality_info['quality_score'] -= 5

                # 检查代码行长度
                long_lines == sum(1 for line in lines if len(line) > 100)::
    if long_lines == 0, ::
    quality_info['quality_score'] += 5
                elif long_lines / len(lines) > 0.3,  # 过多长行, ::
= quality_info['issues'].append('代码行过长过多')
                    quality_info['quality_score'] -= 10

        except UnicodeDecodeError, ::
            quality_info['issues'].append('代码文件编码不支持')
            quality_info['quality_score'] -= 25
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'代码读取错误, {str(e)}')
            quality_info['quality_score'] -= 20

    return quality_info

    def _assess_model_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估模型文件质量"""
    context == ErrorContext("DataManager", "_assess_model_quality",
    {"file_path": str(file_path)})
        try,
            # 检查文件扩展名
            extension = file_path.suffix.lower()
            if extension in ['.pth', '.pt']::
    quality_info['model_type'] = 'PyTorch'
            elif extension in ['.h5', '.hdf5']::
    quality_info['model_type'] = 'Keras / TensorFlow'
            elif extension in ['.pb']::
    quality_info['model_type'] = 'TensorFlow'
            elif extension in ['.onnx']::
    quality_info['model_type'] = 'ONNX'
            elif extension in ['.tflite']::
    quality_info['model_type'] = 'TensorFlow Lite'
            else,

                quality_info['model_type'] = 'Unknown'
                quality_info['issues'].append('未知模型格式')
                quality_info['quality_score'] -= 10

            # 模型文件大小评估
            if quality_info['file_size'] < 1024,  # 小于1KB, ::
= quality_info['issues'].append('模型文件过小')
                quality_info['quality_score'] -= 20
            elif quality_info['file_size'] > 1024 * 1024 * 1024,  # 大于1GB, ::
= quality_info['issues'].append('模型文件过大')
                quality_info['quality_score'] -= 10
            else,

                quality_info['quality_score'] += 15

            # 检查文件是否可读(基本完整性)
            with open(file_path, 'rb') as f, :
    header = f.read(1024)  # 读取文件头
                if len(header) > 0, ::
    quality_info['quality_score'] += 5
                else,

                    quality_info['issues'].append('模型文件头为空')
                    quality_info['quality_score'] -= 15

        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'模型文件读取错误, {str(e)}')
            quality_info['quality_score'] -= 25

    return quality_info

    def _assess_data_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估数据文件质量"""
    context == ErrorContext("DataManager", "_assess_data_quality",
    {"file_path": str(file_path)})
        try,

            extension = file_path.suffix.lower()

            # JSON数据文件
            if extension == '.json':::
from tests.test_json_fix import
                with open(file_path, 'r', encoding == 'utf - 8') as f, :
    data = json.load(f)

                # 检查数据结构
                if isinstance(data, dict)::
                    uality_info['data_info'] = {}
                        'type': 'dict',
                        'keys': list(data.keys()) if isinstance(data, dict) else []::
                            size': len(data) if hasattr(data, '__len__') else 0, ::
                    quality_info['quality_score'] += 10
                elif isinstance(data, list)::
                    uality_info['data_info'] = {}
                        'type': 'list',
                        'size': len(data)
{                    }
                    if len(data) > 0, ::
    quality_info['quality_score'] += 10
                    else,

                        quality_info['issues'].append('JSON数据为空')
                        quality_info['quality_score'] -= 10
                else,

                    quality_info['issues'].append('JSON数据格式不正确')
                    quality_info['quality_score'] -= 15

            # CSV数据文件
            elif extension == '.csv':::
from apps.backend.src.tools.csv_tool import
                with open(file_path, 'r', encoding == 'utf - 8') as f, :
    reader = csv.reader(f)
                    rows = list(reader)

                quality_info['data_info'] = {}
                    'type': 'csv',
                    'rows': len(rows),
                    'columns': len(rows[0]) if rows else 0, ::
                if len(rows) > 0, ::
    quality_info['quality_score'] += 10
                else,

                    quality_info['issues'].append('CSV数据为空')
                    quality_info['quality_score'] -= 10

            # 其他数据文件
            else,

                quality_info['data_info'] = {}
                    'type': extension,
                    'size': quality_info['file_size']
{                }
                quality_info['quality_score'] += 5

        except json.JSONDecodeError, ::
            quality_info['issues'].append('JSON格式错误')
            quality_info['quality_score'] -= 20
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'数据文件读取错误, {str(e)}')
            quality_info['quality_score'] -= 15

    return quality_info

    def _assess_archive_quality(self, file_path, Path, quality_info, Dict) -> Dict, :
    """评估压缩文件质量"""
    context == ErrorContext("DataManager", "_assess_archive_quality",
    {"file_path": str(file_path)})
        try,

# TODO: Fix import - module 'zipfile' not found
# TODO: Fix import - module 'tarfile' not found

            extension = file_path.suffix.lower()

            # 尝试打开压缩文件以检查完整性
            if extension in ['.zip']::
    with zipfile.ZipFile(file_path, 'r') as zip_file, :
    file_list = zip_file.namelist()
                    quality_info['archive_info'] = {}
                        'type': 'zip',
                        'file_count': len(file_list),
                        'files': file_list[:10]  # 只记录前10个文件
{                    }
            elif extension in ['.tar', '.gz']::
    with tarfile.open(file_path, 'r') as tar_file, :
    file_list = tar_file.getnames()
                    quality_info['archive_info'] = {}
                        'type': 'tar',
                        'file_count': len(file_list),
                        'files': file_list[:10]  # 只记录前10个文件
{                    }
            else,

                quality_info['archive_info'] = {}
                    'type': 'unknown',
                    'file_count': 0
{                }
                quality_info['issues'].append('不支持的压缩格式')
                quality_info['quality_score'] -= 10

            # 压缩文件大小评估
            if quality_info['file_size'] < 1024,  # 小于1KB, ::
= quality_info['issues'].append('压缩文件过小')
                quality_info['quality_score'] -= 15
            elif quality_info['file_size'] > 500 * 1024 * 1024,  # 大于500MB, ::
= quality_info['issues'].append('压缩文件过大')
                quality_info['quality_score'] -= 5
            else,

                quality_info['quality_score'] += 10

            # 检查文件数量
            file_count = quality_info.get('archive_info', {}).get('file_count', 0)
            if file_count > 0, ::
    quality_info['quality_score'] += 5
            else,

                quality_info['issues'].append('压缩文件为空')
                quality_info['quality_score'] -= 10

        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            quality_info['issues'].append(f'压缩文件读取错误, {str(e)}')
            quality_info['quality_score'] -= 20

    return quality_info

    def _is_file_corrupted(self, file_path, Path) -> bool, :
    """检查文件是否可能已损坏"""
    context == ErrorContext("DataManager", "_is_file_corrupted",
    {"file_path": str(file_path)})
        try,
            # 计算文件的MD5哈希值
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f, :
    for chunk in iter(lambda, f.read(4096), b""):::
    hash_md5.update(chunk)

            # 简单检查：如果文件大小为0, 则认为已损坏
            if file_path.stat().st_size == 0, ::
    return True

            return False
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            return True

    def get_data_by_type(self, data_type, str) -> List[Dict[str, Any]]:
    """根据数据类型获取文件列表"""
    context == ErrorContext("DataManager", "get_data_by_type", {"data_type": data_type})
        try,

            result = []
            for file_info in self.data_catalog.values():::
                f file_info['type'] == data_type,


    result.append(file_info)
            return result
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 根据数据类型获取文件列表失败, {data_type} - {e}")
            return []

    def get_high_quality_data(self, min_quality_score, int == 70) -> Dict[str,
    List[Dict[str, Any]]]:
    """获取高质量数据(按类型分组)"""
    context == ErrorContext("DataManager", "get_high_quality_data")
        try,

            high_quality_data = {}

            # 先评估所有数据的质量
            for file_path in self.data_catalog.keys():::
= self.assess_data_quality(file_path)

            # 按类型分组高质量数据
            for file_path, quality_info in self.data_quality_scores.items():::
                f quality_info['quality_score'] >= min_quality_score,


    file_info = self.data_catalog.get(file_path)
                    if file_info, ::
    data_type = file_info['type']
                        if data_type not in high_quality_data, ::
    high_quality_data[data_type] = []
                        high_quality_data[data_type].append(file_info)

            return high_quality_data
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取高质量数据失败, {e}")
            return {}

    def prepare_training_data(self, model_type, str) -> List[Dict[str, Any]]:
    """为特定模型类型准备训练数据"""
    context == ErrorContext("DataManager", "prepare_training_data",
    {"model_type": model_type})
    logger.info(f"📦 为模型 {model_type} 准备训练数据")

        try,
            # 获取该模型支持的数据类型
            supported_types = self.model_data_mapping.get(model_type, [])
            if not supported_types, ::
    logger.warning(f"⚠️ 未找到模型 {model_type} 的数据映射")
                return []

            # 收集支持的数据
            training_data = []
            for data_type in supported_types, ::
    data_files = self.get_data_by_type(data_type)
                training_data.extend(data_files)

            # 对于概念模型, 直接添加概念模型训练数据
            if model_type in ['concept_models', 'environment_simulator',
    'causal_reasoning_engine', :::]:
[                adaptive_learning_controller', 'alpha_deep_model']
                # 添加概念模型专用训练数据
                concept_data_dir = self.data_dir / "concept_models_training_data"
                if concept_data_dir.exists():::
                    or json_file in concept_data_dir.glob(" * .json")
                        # 根据模型类型过滤数据
                        if self._is_data_relevant_for_model(json_file.name(),
    model_type)::
                            ile_info = {}
                                'path': str(json_file),
                                'relative_path': str(json_file.relative_to(self.data_dir\
    \
    \
    ())),
                                'size': json_file.stat().st_size,
                                'modified_time': json_file.stat().st_mtime,
                                'extension': '.json',
                                'type': 'json'
{                            }
                            training_data.append(file_info)

            # 过滤高质量数据
            high_quality_data = self.get_high_quality_data()
            filtered_data = []
            for data_item in training_data, ::
                # 检查数据是否在高质量数据中
                data_type = data_item['type']
                if data_type in high_quality_data, ::
    high_quality_files == [f['path'] for f in high_quality_data[data_type]]::
    if data_item['path'] in high_quality_files, ::
    filtered_data.append(data_item)
                else,
                    # 如果没有高质量数据检查, 直接添加
                    filtered_data.append(data_item)

            logger.info(f"✅ 为模型 {model_type} 准备了 {len(filtered_data)} 个训练数据文件")
            return filtered_data
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 为模型 {model_type} 准备训练数据失败, {e}")
            return []

    def _is_data_relevant_for_model(self, filename, str, model_type, str) -> bool, :
    """检查数据文件是否与特定模型相关"""
    context == ErrorContext("DataManager", "_is_data_relevant_for_model",
    {"filename": filename, "model_type": model_type})
        try,
            # 根据文件名和模型类型判断相关性
            if model_type == 'environment_simulator' and 'environment' in filename, ::
    return True
            elif model_type == 'causal_reasoning_engine' and 'causal' in filename, ::
    return True
            elif model_type == 'adaptive_learning_controller' and \
    'adaptive' in filename, ::
    return True
            elif model_type == 'alpha_deep_model' and 'alpha' in filename, ::
    return True
            elif model_type == 'concept_models':::
                # 概念模型可以使用所有概念数据
                return any(keyword in filename for keyword in ['environment', 'causal',
    'adaptive', 'alpha'])::
                    eturn False
        except Exception as e, ::
    self.error_handler.handle_error(e, context)
            logger.error(f"❌ 检查数据文件相关性失败, {filename} - {model_type} - {e}")
            return False

    def get_data_statistics(self) -> Dict[str, Any]:
    """获取数据统计信息"""
    context == ErrorContext("DataManager", "get_data_statistics")
        try,

            if not self.data_catalog, ::
    self.scan_data()

            stats = {}
                'total_files': len(self.data_catalog()),
                'file_types': {}
                'total_size': 0,
                'last_scan_time': datetime.now().isoformat()
{            }

            # 统计各类文件数量和大小
            for file_info in self.data_catalog.values():::
                ile_type = file_info['type']
                if file_type not in stats['file_types']::
    stats['file_types'][file_type] = {'count': 0, 'size': 0}

                stats['file_types'][file_type]['count'] += 1
                stats['file_types'][file_type]['size'] += file_info['size']
                stats['total_size'] += file_info['size']

            return stats
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取数据统计信息失败, {e}")
            return {}

    def save_data_catalog(self, catalog_path, str == None):
        ""保存数据目录到文件"""
    context == ErrorContext("DataManager", "save_data_catalog")
        try,

            if not catalog_path, ::
    catalog_path == TRAINING_DIR / "data_catalog.json"

            catalog_data = {}
                'catalog': self.data_catalog(),
                'quality_scores': self.data_quality_scores(),
                'statistics': self.get_data_statistics(),
                'generated_at': datetime.now().isoformat()
{            }

            try,


                with open(catalog_path, 'w', encoding == 'utf - 8') as f, :
    json.dump(catalog_data, f, ensure_ascii == False, indent = 2)
                logger.info(f"💾 数据目录已保存到, {catalog_path}")
            except Exception as e, ::
                logger.error(f"❌ 保存数据目录失败, {e}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存数据目录失败, {e}")

    def load_data_catalog(self, catalog_path, str == None):
        ""从文件加载数据目录"""
    context == ErrorContext("DataManager", "load_data_catalog")
        try,

            if not catalog_path, ::
    catalog_path == TRAINING_DIR / "data_catalog.json"

            if not Path(catalog_path).exists():::
= logger.warning(f"⚠️ 数据目录文件不存在, {catalog_path}")
                return False

            try,


                with open(catalog_path, 'r', encoding == 'utf - 8') as f, :
    catalog_data = json.load(f)

                self.data_catalog = catalog_data.get('catalog', {})
                self.data_quality_scores = catalog_data.get('quality_scores', {})
                logger.info(f"✅ 数据目录已从 {catalog_path} 加载")
                return True
            except Exception as e, ::
                logger.error(f"❌ 加载数据目录失败, {e}")
                return False
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载数据目录失败, {e}")
            return False


def main() -> None, :
    """主函数, 用于测试DataManager"""
    print("🔍 测试数据管理器...")

    # 初始化数据管理器
    data_manager == DataManager()

    # 扫描数据
    catalog = data_manager.scan_data()
    print(f"📊 扫描到 {len(catalog)} 个文件")

    # 显示数据统计
    stats = data_manager.get_data_statistics()
    print(f"📈 数据统计, ")
    print(f"  总文件数, {stats['total_files']}")
    print(f"  总大小, {stats['total_size'] / (1024 * 1024).2f} MB")
    print(f"  文件类型分布, ")
    for file_type, info in stats['file_types'].items():::
= print(f"    {file_type} {info['count']} 个文件, {info['size'] / (1024 * 1024).2f} MB")

    # 评估几个文件的质量
    print(f"\n🔍 数据质量评估, ")
    sample_files == list(catalog.keys())[:3]  # 取前3个文件进行评估
    for file_path in sample_files, ::
    quality = data_manager.assess_data_quality(file_path)
    print(f"  {file_path} 质量评分 {quality['quality_score']} / 100")
        if quality['issues']::
    print(f"    问题, {', '.join(quality['issues'])}")

    # 为不同模型准备数据
    print(f"\n📦 训练数据准备, ")
    for model_type in ['vision_service', 'audio_service', 'causal_reasoning_engine']::
    training_data = data_manager.prepare_training_data(model_type)
    print(f"  {model_type} {len(training_data)} 个训练文件")

    # 保存数据目录
    data_manager.save_data_catalog()
    print(f"\n✅ 数据管理器测试完成")


if __name"__main__":::
    main()