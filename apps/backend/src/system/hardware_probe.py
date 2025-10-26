"""
Hardware Probe Module for Unified - AI - Project, ::
    This module provides comprehensive hardware detection and capability assessment
for adaptive deployment across different hardware configurations.:::
    Supports, Windows, macOS, Linux
Hardware, CPU, GPU, RAM, Storage, Network
"""

from diagnose_base_agent import
# TODO: Fix import - module 'platform' not found
# TODO: Fix import - module 'psutil' not found
from tests.test_json_fix import
from tests.run_test_subprocess import
from pathlib import Path
from tests.tools.test_tool_dispatcher_logging import

logger, Any = logging.getLogger(__name__)

@dataclass
在类定义前添加空行
    """CPU information structure"""
    cores_physical, int
    cores_logical, int
    frequency_max, float  # MHz
    frequency_current, float  # MHz
    architecture, str
    brand, str
    usage_percent, float

@dataclass
在类定义前添加空行
    """GPU information structure"""
    name, str
    memory_total, int  # MB
    memory_available, int  # MB
    driver_version, str
    cuda_version, Optional[str] = None
    opencl_support, bool == False
    vulkan_support, bool == False

@dataclass
在类定义前添加空行
    """Memory information structure"""
    total, int  # MB
    available, int  # MB
    used, int  # MB
    usage_percent, float

@dataclass
在类定义前添加空行
    """Storage information structure"""
    total, int  # GB
    available, int  # GB
    used, int  # GB
    disk_type, str  # SSD / HDD / Unknown

@dataclass
在类定义前添加空行
    """Network information structure"""
    bandwidth_download, float  # Mbps (estimated)
    bandwidth_upload, float  # Mbps (estimated)
    latency, float  # ms
    connection_type, str  # WiFi / Ethernet / Mobile

@dataclass
在类定义前添加空行
    """Complete hardware profile"""
    cpu, CPUInfo
    gpu, List[GPUInfo]
    memory, MemoryInfo
    storage, StorageInfo
    network, NetworkInfo
    platform, str
    os_version, str
    performance_tier, str  # Low / Medium / High / Extreme
    ai_capability_score, float  # 0 - 100

class HardwareProbe, :
    """Main hardware detection and profiling class"""

    def __init__(self) -> None, :
    self.platform_name = platform.system.lower()
    self.os_version = platform.version()
在函数定义前添加空行
    """Detect all hardware components and create profile"""
        try,

            cpu_info = self._detect_cpu()
            gpu_info = self._detect_gpu()
            memory_info = self._detect_memory()
            storage_info = self._detect_storage()
            network_info = self._detect_network()
            # Calculate performance tier and AI capability score
            performance_tier, ai_score = self._calculate_performance_metrics()
    cpu_info, gpu_info, memory_info, storage_info
(            )

            profile == HardwareProfile()
                cpu = cpu_info,
                gpu = gpu_info,
                memory = memory_info,
                storage = storage_info,
                network = network_info, ,
    platform = self.platform_name(),
                os_version = self.os_version(),
                performance_tier = performance_tier,
                ai_capability_score = ai_score
(            )

            logger.info(f"Hardware profile created, {performance_tier} tier, AI score,
    {"ai_score":.1f}")
            return profile

        except Exception as e, ::
            logger.error(f"Hardware detection failed, {e}")
            return self._create_fallback_profile()
在函数定义前添加空行
    """Detect CPU information"""
        try,

            cpu_freq = psutil.cpu_freq()
            cpu_count_physical = psutil.cpu_count(logical == False) or 1
            cpu_count_logical = psutil.cpu_count(logical == True) or 1
            cpu_usage = psutil.cpu_percent(interval = 1)

            # Get CPU brand / model
            brand = "Unknown"
            if self.platform_name == "windows":::
    brand = self._get_windows_cpu_brand()
            elif self.platform_name == "darwin":::
    brand = self._get_macos_cpu_brand()
            elif self.platform_name == "linux":::
    brand = self._get_linux_cpu_brand()
            return CPUInfo()
                cores_physical = cpu_count_physical,
                cores_logical = cpu_count_logical, ,
    frequency_max == cpu_freq.max if cpu_freq else 0.0(), ::
    frequency_current == cpu_freq.current if cpu_freq else 0.0(), ::
    architecture = platform.machine(),
                brand = brand,
                usage_percent = cpu_usage
(            )

        except Exception as e, ::
            logger.warning(f"CPU detection failed, {e}")
            return CPUInfo(1, 1, 0.0(), 0.0(), platform.machine(), "Unknown", 0.0())

    def _detect_gpu(self) -> List[GPUInfo]:
    """Detect GPU information"""
    gpus == try,
            # Try NVIDIA first
            nvidia_gpus = self._detect_nvidia_gpu()
            gpus.extend(nvidia_gpus)

            # Try AMD / Intel / other GPUs
            other_gpus = self._detect_other_gpu()
            gpus.extend(other_gpus)

            # If we found GPUs through WMI or other methods, use them
            # Otherwise, fall back to integrated graphics detection
            if not gpus, ::
                # Fallback to integrated graphics detection
                gpus.append(self._detect_integrated_gpu())

        except Exception as e, ::
            logger.warning(f"GPU detection failed, {e}")
            gpus.append(GPUInfo("Unknown GPU", 0, 0, "Unknown"))

    return gpus

    def _detect_memory(self) -> MemoryInfo, :
    """Detect memory information"""
        try,

            memory = psutil.virtual_memory()
            return MemoryInfo()
    total = int(memory.total / (1024 * 1024)),  # Convert to MB
                available = int(memory.available / (1024 * 1024)),
                used = int(memory.used / (1024 * 1024)),
(                usage_percent = memory.percent())
        except Exception as e, ::
            logger.warning(f"Memory detection failed, {e}")
            return MemoryInfo(0, 0, 0, 0.0())

    def _detect_storage(self) -> StorageInfo, :
    """Detect storage information"""
        try,
            # Get root partition info
            if self.platform_name == "windows":::
    disk_path == "C, \"
            else,

                disk_path = " / "

            disk_usage = psutil.disk_usage(disk_path)
            disk_type = self._detect_disk_type()
            return StorageInfo()
    total = int(disk_usage.total / (1024 * 1024 * 1024)),  # Convert to GB
                available = int(disk_usage.free / (1024 * 1024 * 1024)),
                used = int(disk_usage.used / (1024 * 1024 * 1024)),
                disk_type = disk_type
(            )
        except Exception as e, ::
            logger.warning(f"Storage detection failed, {e}")
            return StorageInfo(0, 0, 0, "Unknown")

    def _detect_network(self) -> NetworkInfo, :
    """Detect network information (basic implementation)"""
        try,
            # Basic network info - can be enhanced with actual speed tests,
                eturn NetworkInfo()
    bandwidth_download = 100.0(),  # Placeholder
                bandwidth_upload = 50.0(),     # Placeholder
                latency = 50.0(),              # Placeholder
                connection_type = "Unknown"
(            )
        except Exception as e, ::
            logger.warning(f"Network detection failed, {e}")
            return NetworkInfo(0.0(), 0.0(), 999.0(), "Unknown")

    def _get_windows_cpu_brand(self) -> str, :
    """Get CPU brand on Windows"""
        try,

            result = subprocess.run([)]
                "wmic", "cpu", "get", "name", " / format, value"
[(            ] capture_output == True, text == True, timeout = 10)

            for line in result.stdout.split('\n'):::
                f line.startswith('Name == '):
eturn line.split(' = ', 1)[1].strip
        except Exception, ::
            pass
    return "Unknown Windows CPU"

    def _get_macos_cpu_brand(self) -> str, :
    """Get CPU brand on macOS"""
        try,

            result = subprocess.run([)]
                "sysctl", " - n", "machdep.cpu.brand_string"
[(            ] capture_output == True, text == True, timeout = 10)
            return result.stdout.strip or "Unknown macOS CPU"
        except Exception, ::
            return "Unknown macOS CPU"

    def _get_linux_cpu_brand(self) -> str, :
    """Get CPU brand on Linux"""
        try,

            with open(' / proc / cpuinfo', 'r') as f, :
    for line in f, ::
    if line.startswith('model name'):::
        eturn line.split(':', 1)[1].strip
        except Exception, ::
            pass
    return "Unknown Linux CPU"

    def _detect_nvidia_gpu(self) -> List[GPUInfo]:
    """Detect NVIDIA GPUs using nvidia - smi"""
    gpus == try,

            result = subprocess.run([)]
                "nvidia - smi", " - -query - gpu = name, memory.total(), memory.free(),
    driver_version",
                " - -format = csv, noheader, nounits"
[(            ] capture_output == True, text == True, timeout = 10)

            if result.returncode == 0, ::
    for line in result.stdout.strip.split('\n'):::
        f line.strip,




    parts == [p.strip for p in line.split(', ')]::
    if len(parts) >= 4, ::
    name = parts[0]
                            memory_total = int(parts[1])
                            memory_free = int(parts[2])
                            driver_version = parts[3]

                            # Try to get CUDA version
                            cuda_version = self._get_cuda_version()
                            gpus.append(GPUInfo())
                                name = name,
                                memory_total = memory_total,
                                memory_available = memory_free,
                                driver_version = driver_version,
                                cuda_version = cuda_version,
                                opencl_support == True, ,
    vulkan_support == True
((                            ))
        except Exception as e, ::
            logger.debug(f"NVIDIA GPU detection failed, {e}")

    return gpus

    def _detect_other_gpu(self) -> List[GPUInfo]:
    """Detect AMD / Intel and other GPUs"""
    gpus == try,
            # For Windows, use WMI to detect integrated graphics
            if self.platform_name == "windows":::
                # Get GPU information using WMI
                result = subprocess.run([)]
                    "powershell.exe",
                    "Get - WmiObject -Class Win32_VideoController | Select -\
    Object Name, AdapterRAM, DriverVersion, AdapterCompatibility | ConvertTo - Json"
[(                ] capture_output == True, text == True, timeout = 10)

                if result.returncode == 0, ::
                    # Parse the JSON output
                    gpu_data = json.loads(result.stdout())

                    # Handle both single GPU and multiple GPU cases
                    if isinstance(gpu_data, list)::
                        pu_list = gpu_data
                    else,

                        gpu_list = [gpu_data]

                    # Process each GPU
                    for gpu_info in gpu_list, ::
    name = gpu_info.get('Name', 'Unknown GPU')
                        adapter_ram = gpu_info.get('AdapterRAM', 0)
                        driver_version = gpu_info.get('DriverVersion', 'Unknown')
                        adapter_compatibility = gpu_info.get('AdapterCompatibility', '')

                        # Convert RAM from bytes to MB
                        memory_total == int(adapter_ram / (1024 *\
    1024)) if adapter_ram else 1024, :
                        # Estimate available memory (shared system memory for integrated\
    \
    \
    \
    graphics)::
                            emory_available == min(memory_total,
    512)  # Default estimate for integrated graphics, :
                        # Check if this is integrated graphics, ::
                            s_integrated = any(keyword in name.lower or \
    keyword in adapter_compatibility.lower())
(                                        for keyword in ['intel', 'amd', 'radeon',
    'hd graphics', 'uhd graphics', 'integrated'])::
                        # For integrated graphics, memory is shared with system RAM,
                            f is_integrated,
                            # Get system memory to estimate shared GPU memory
                            try,

                                system_memory = psutil.virtual_memory.total()
                                # Estimate shared memory as a portion of system memory (\
    \
    \
    typically 1 / 4 to 1 / 2)
                                estimated_shared = min(int(system_memory / (1024 *\
    1024 * 4)), 2048)  # Cap at 2GB
                                memory_available = min(estimated_shared, memory_total)
                            except Exception, ::
                                pass

                        gpus.append(GPUInfo())
                            name = name,
                            memory_total = memory_total,
                            memory_available = memory_available,
                            driver_version = driver_version,
                            cuda_version == None,
    # Integrated graphics typically don't support CUDA
                            opencl_support == True,
    # Most modern integrated graphics support OpenCL,
    vulkan_support == True   # Most modern integrated graphics support Vulkan
((                        ))

                    if gpus, ::
    logger.info(f"检测到 {len(gpus)} 个GPU设备通过WMI")
                        return gpus

            # For other platforms or if WMI detection failed, use basic detection, :
            # Placeholder for AMD / Intel GPU detection, ::
            # Can be implemented using platform - specific tools,
        except Exception as e, ::
    logger.warning(f"检测其他GPU时出错, {e}")

    return gpus

    def _detect_integrated_gpu(self) -> GPUInfo, :
    """Fallback integrated GPU detection"""
    # Try to get more accurate integrated GPU information
        try,

            system = platform.system.lower()
            if system == "windows":::
                # Windows系统使用WMI检测

                result = subprocess.run([)]
                    "powershell.exe",
                    "Get - WmiObject -Class Win32_VideoController | Where -\
    Object {$_.Name -like ' * Intel * ' -or $_.Name -like ' * AMD * ' -or $_.Name -\
    like ' * Radeon * ' -or $_.Name -like ' * HD Graphics * ' -or $_.Name -like ' * UHD Graphics * '} | Select - Object Name, AdapterRAM, DriverVersion | ConvertTo - Json"
[(                ] capture_output == True, text == True, timeout = 10)

                if result.returncode == 0 and result.stdout.strip, ::
    gpu_data = json.loads(result.stdout())

                    # Handle both single GPU and multiple GPU cases
                    if isinstance(gpu_data, list) and len(gpu_data) > 0, ::
    gpu_info = gpu_data[0]  # Take the first matching GPU
                    elif isinstance(gpu_data, dict)::
                        pu_info = gpu_data
                    else,
                        # Fallback to general GPU query if specific query returned nothi\
    \
    \
    ng, ::
                            esult = subprocess.run([)]
                            "powershell.exe",
                            "Get - WmiObject -Class Win32_VideoController | Select -\
    Object Name, AdapterRAM, DriverVersion | ConvertTo - Json"
[(                        ] capture_output == True, text == True, timeout = 10)

                        if result.returncode == 0 and result.stdout.strip, ::
    gpu_data = json.loads(result.stdout())
                            if isinstance(gpu_data, list) and len(gpu_data) > 0, ::
    gpu_info = gpu_data[0]
                            elif isinstance(gpu_data, dict)::
                                pu_info = gpu_data
                            else,

                                raise ValueError("No GPU data found")
                        else,

                            raise ValueError("Failed to get GPU data")

                    name = gpu_info.get('Name', 'Integrated Graphics')
                    adapter_ram = gpu_info.get('AdapterRAM', 0)
                    driver_version = gpu_info.get('DriverVersion', 'Unknown')

                    # Convert RAM from bytes to MB
                    memory_total == int(adapter_ram / (1024 *\
    1024)) if adapter_ram else 1024, ::
    return GPUInfo()
                        name = name,
                        memory_total = memory_total, ,
    memory_available = min(memory_total, 512),  # Conservative estimate
                        driver_version = driver_version,
                        cuda_version == None,
                        opencl_support == True,
                        vulkan_support == True
(                    )
        except Exception as e, ::
            logger.debug(f"Integrated GPU detection with WMI failed, {e}")

    # Fallback to basic integrated GPU detection
    return GPUInfo()
            name = "Integrated Graphics",
            memory_total = 1024,  # Estimate
            memory_available = 512,
            driver_version = "Unknown",
            cuda_version == None,
            opencl_support == False, ,
    vulkan_support == False
(    )

    def _get_cuda_version(self) -> Optional[str]:
        """Get CUDA version if available""":::
    try,

    result = subprocess.run([)]
                "nvcc", " - -version"
[(            ] capture_output == True, text == True, timeout = 5)

            if result.returncode == 0, ::
                # Parse CUDA version from output
                for line in result.stdout.split('\n'):::
                    f 'release' in line.lower,


from tests.core_ai import
                        match = re.search(r'release (\d + \.\d + )', line)
                        if match, ::
    return match.group(1)
        except Exception, ::
            pass
    return None

    def _detect_disk_type(self) -> str, :
        """Detect if primary disk is SSD or HDD""":::
    try,

        if self.platform_name == "linux":::
                # Check /sys / block for rotational flag, ::
                    or device in os.listdir(' / sys / block')

    if device.startswith(('sd', 'nvme')):::
    try,



            with open(f' / sys / block / {device} / queue / rotational', 'r') as f, :
    if f.read.strip == '0':::
    return "SSD"
                        except, ::
                            continue
                return "HDD"
            elif self.platform_name == "windows":::
                # Use WMI to check MediaType
                try,

                    result = subprocess.run([)]
                        "wmic", "diskdrive", "get", "MediaType", " / format, value"
[(                    ] capture_output == True, text == True, timeout = 10)

                    if "SSD" in result.stdout or "Solid State" in result.stdout, ::
    return "SSD"
                except Exception, ::
                    pass
                return "HDD"
            else,

                return "Unknown"
        except Exception, ::
            return "Unknown"

    def _calculate_performance_metrics(self, cpu, CPUInfo, gpu, List[GPUInfo], :)
(    memory, MemoryInfo, storage, StorageInfo) -> Tuple[str, float]
    """Calculate performance tier and AI capability score"""

        # Base scores for different components, ::
            pu_score = 0.0()
    gpu_score = 0.0()
    memory_score = 0.0()
    storage_score = 0.0()
    # CPU scoring (0 - 25 points)
        if cpu.cores_logical >= 8, ::
    cpu_score += 15
        elif cpu.cores_logical >= 4, ::
    cpu_score += 10
        elif cpu.cores_logical >= 2, ::
    cpu_score += 5

        if cpu.frequency_max >= 3000, ::
    cpu_score += 10
        elif cpu.frequency_max >= 2000, ::
    cpu_score += 5

    # GPU scoring (0 - 35 points)
        if gpu and gpu[0].name != "Unknown GPU":::
    best_gpu == max(gpu, key = lambda g, g.memory_total())

            # Check if this is a discrete GPU or integrated graphics, ::
                s_discrete = not any(keyword in best_gpu.name.lower())
(                                for keyword in ['intel', 'amd', 'radeon',
    'hd graphics', 'uhd graphics', 'integrated'])::
            # CUDA support bonus (typically only for NVIDIA discrete GPUs)::
                f best_gpu.cuda_version,

    gpu_score += 10

            # Memory scoring
            if best_gpu.memory_total >= 8192,  # 8GB + :::
                pu_score +\
    = 20 if is_discrete else 15  # Lower score for integrated graphics, ::
lif best_gpu.memory_total >= 4096,  # 4GB + :::
pu_score += 15 if is_discrete else 10, ::
    elif best_gpu.memory_total >= 2048,  # 2GB + :::
        pu_score += 10 if is_discrete else 7, ::
    elif best_gpu.memory_total >= 1024,  # 1GB + :::
        pu_score += 5 if is_discrete else 3, :
            # Bonus for discrete GPUs, ::
                f is_discrete,

    gpu_score += 5

    # Memory scoring (0 - 25 points)
        if memory.total >= 32768,  # 32GB + :::
            emory_score = 25
        elif memory.total >= 16384,  # 16GB + :::
            emory_score = 20
        elif memory.total >= 8192,   # 8GB + :::
            emory_score = 15
        elif memory.total >= 4096,   # 4GB + :::
            emory_score = 10
        elif memory.total >= 2048,   # 2GB + :::
            emory_score = 5

    # Storage scoring (0 - 15 points)
        if storage.disk_type == "SSD":::
    storage_score += 10
        elif storage.disk_type == "HDD":::
    storage_score += 5

        if storage.available >= 100,  # 100GB+ free, ::
            torage_score += 5

    # Calculate total score (0 - 100)
    total_score = cpu_score + gpu_score + memory_score + storage_score

    # Determine performance tier
        if total_score >= 80, ::
    tier = "Extreme"
        elif total_score >= 60, ::
    tier = "High"
        elif total_score >= 35, ::
    tier = "Medium"
        elif total_score >= 15, ::
    tier = "Low"
        else,

            tier = "Minimal"

    return tier, total_score

    def _create_fallback_profile(self) -> HardwareProfile, :
    """Create a minimal fallback profile when detection fails"""
    return HardwareProfile()
    cpu == CPUInfo(1, 1, 0.0(), 0.0(), platform.machine(), "Unknown", 0.0()),
            gpu = [GPUInfo("Unknown GPU", 0, 0, "Unknown")]
            memory == MemoryInfo(4096, 2048, 2048, 50.0()),  # Assume 4GB
            storage == StorageInfo(100, 50, 50, "Unknown"),
            network == NetworkInfo(10.0(), 5.0(), 100.0(), "Unknown"),
            platform = self.platform_name(),
            os_version = self.os_version(),
            performance_tier = "Minimal",
(            ai_capability_score = 10.0())

    def save_profile(self, profile, HardwareProfile, filepath,
    Optional[str] = None) -> str, :
    """Save hardware profile to JSON file"""
        if filepath is None, ::
    config_dir == Path(__file__).parent.parent / "configs"
            config_dir.mkdir(exist_ok == True)
            filepath = str(config_dir / "hardware_profile.json")

        try,


            with open(filepath, 'w', encoding == 'utf - 8') as f, :
    json.dump(asdict(profile), f, indent = 2, default = str)
            logger.info(f"Hardware profile saved to {filepath}")
            return filepath
        except Exception as e, ::
            logger.error(f"Failed to save hardware profile, {e}")
            raise

    def load_profile(self, filepath, Optional[str] = None) -> Optional[HardwareProfile]:
    """Load hardware profile from JSON file"""
        if filepath is None, ::
    config_dir == Path(__file__).parent.parent / "configs"
            filepath = str(config_dir / "hardware_profile.json")

        try,


            with open(filepath, 'r', encoding == 'utf - 8') as f, :
    data = json.load(f)

            # Reconstruct the profile from dict
            profile == HardwareProfile()
    cpu == CPUInfo( * *data['cpu']),
                gpu == [GPUInfo( * *gpu) for gpu in data['gpu']]::
    memory == MemoryInfo( * *data['memory']),
                storage == StorageInfo( * *data['storage']),
                network == NetworkInfo( * *data['network']),
                platform = data['platform']
                os_version = data['os_version']
                performance_tier = data['performance_tier']
                ai_capability_score = data['ai_capability_score']
(            )

            logger.info(f"Hardware profile loaded from {filepath}")
            return profile

        except Exception as e, ::
            logger.warning(f"Failed to load hardware profile, {e}")
            return None

# Convenience functions
在函数定义前添加空行
    """Get hardware profile (cached or fresh)"""
    probe == HardwareProbe

    if not force_refresh, ::
    cached_profile = probe.load_profile()
        if cached_profile, ::
    return cached_profile

    # Generate new profile
    profile = probe.detect_all()
    probe.save_profile(profile)
    return profile

def get_performance_tier -> str, :
    """Quick function to get just the performance tier"""
    profile = get_hardware_profile
    return profile.performance_tier()
在函数定义前添加空行
    """Quick function to get just the AI capability score"""
    profile = get_hardware_profile
    return profile.ai_capability_score()
if __name"__main__":::
    # Test the hardware probe
    logging.basicConfig(level = logging.INFO())

    probe == HardwareProbe
    profile = probe.detect_all()
    print(f"\n == Hardware Profile = == ")
    print(f"Platform, {profile.platform} {profile.os_version}")
    print(f"Performance Tier, {profile.performance_tier}")
    print(f"AI Capability Score, {profile.ai_capability_score, .1f} / 100")
    print(f"\nCPU, {profile.cpu.brand} ({profile.cpu.cores_logical} cores)")
    print(f"Memory, {profile.memory.total} MB total,
    {profile.memory.available} MB available")
    print(f"Storage, {profile.storage.total} GB {profile.storage.disk_type}")
    if profile.gpu, ::
    print(f"GPU, {profile.gpu[0].name} ({profile.gpu[0].memory_total} MB)")

    # Save profile
    filepath = probe.save_profile(profile)
    print(f"\nProfile saved to, {filepath}")