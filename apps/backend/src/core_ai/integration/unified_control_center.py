import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Import actual system components
try:
    from ..memory.ham_memory_manager import HAMMemoryManager
    from ..memory.vector_store import VectorMemoryStore
    from ..reasoning.causal_reasoning_engine import CausalReasoningEngine
    from ...hsp.connector import HSPConnector
    from ...services.audio_service import AudioService
    from ...services.vision_service import VisionService
    from ...services.multi_llm_service import MultiLLMService
    from ..dialogue.dialogue_manager import DialogueManager
    from ..learning.learning_manager import LearningManager
except ImportError as e:
    logging.warning(f"Some components not available for import: {e}")
    HAMMemoryManager = None
    VectorMemoryStore = None
    CausalReasoningEngine = None
    HSPConnector = None
    AudioService = None
    VisionService = None
    MultiLLMService = None
    DialogueManager = None
    LearningManager = None

logger = logging.getLogger(__name__)

# Placeholder classes
class ComponentOrchestrator:
    async def create_execution_plan(self, subtasks: List[Any]) -> List[Any]:
        logger.debug("Creating execution plan (conceptual)...")
        await asyncio.sleep(0.01)
        return subtasks # Dummy: just return subtasks as plan

    async def select_component(self, subtask: Any) -> Any:
        logger.debug("Selecting component for subtask (conceptual)...")
        await asyncio.sleep(0.005)
        # Dummy: always return a mock component that can execute
        class MockComponent:
            async def execute(self, task: Any) -> Dict[str, Any]:
                logger.debug(f"MockComponent executing task: {task.get('name')}")
                await asyncio.sleep(0.01)
                return {"status": "success", "output": f"Processed {task.get('name')}"}
        return MockComponent()

class SystemMonitor:
    def __init__(self):
        self.components_registered = []

    def register_component(self, component: Any):
        logger.debug(f"Registering component: {component.__class__.__name__}")
        self.components_registered.append(component)

    async def start_monitoring(self):
        logger.debug("Starting system monitoring (conceptual)...")
        await asyncio.sleep(0.01)

class UnifiedControlCenter:
    """統一控制中心"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.components = self._initialize_components()
        self.orchestrator = ComponentOrchestrator()
        self.monitor = SystemMonitor()
        self.logger = logging.getLogger(__name__)
    
    async def initialize_system(self):
        """初始化整個系統"""
        self.logger.info("Initializing Unified Control Center system...")
        # 按依賴順序初始化組件
        initialization_order = [
            'memory_manager',
            'hsp_connector',
            'learning_manager',
            'world_model',
            'reasoning_engine',
            'dialogue_manager'
        ]
        
        for component_name in initialization_order:
            component = self.components.get(component_name) # Use .get to avoid KeyError for conceptual components
            if component:
                if hasattr(component, 'initialize') and asyncio.iscoroutinefunction(component.initialize):
                    await component.initialize()
                self.monitor.register_component(component)
            else:
                self.logger.warning(f"Component '{component_name}' not found during initialization. Skipping.")
        
        # 建立組件間連接 (conceptual)
        await self._establish_inter_component_connections()
        
        # 啟動監控
        await self.monitor.start_monitoring()
        self.logger.info("Unified Control Center system initialized.")

    def _initialize_components(self) -> Dict[str, Any]:
        """Initialize and return a dictionary of actual core system components."""
        self.logger.info("Initializing actual core system components...")
        components = {}
        
        try:
            # Initialize Memory Management
            if HAMMemoryManager:
                components["memory_manager"] = HAMMemoryManager(
                    storage_dir=self.config.get("memory_storage_dir", "./ham_data")
                )
                self.logger.info("HAM Memory Manager initialized")
            
            # Initialize Vector Store for semantic memory
            if VectorMemoryStore:
                components["vector_store"] = VectorMemoryStore(
                    persist_directory=self.config.get("vector_storage_dir", "./chroma_db")
                )
                self.logger.info("Vector Memory Store initialized")
            
            # Initialize Causal Reasoning Engine
            if CausalReasoningEngine:
                components["reasoning_engine"] = CausalReasoningEngine(
                    config=self.config.get("reasoning_config", {})
                )
                self.logger.info("Causal Reasoning Engine initialized")
            
            # Initialize HSP Connector for inter-agent communication
            if HSPConnector:
                try:
                    components["hsp_connector"] = HSPConnector(
                        ai_id=self.config.get("ai_id", "unified_control_center"),
                        broker_address=self.config.get("mqtt_host", "localhost"),
                        broker_port=self.config.get("mqtt_port", 1883)
                    )
                    self.logger.info("HSP Connector initialized")
                except Exception as e:
                    self.logger.warning(f"Could not initialize HSP Connector: {e}")
            
            # Initialize Multimodal Services
            if AudioService:
                components["audio_service"] = AudioService(
                    config=self.config.get("audio_config", {})
                )
                self.logger.info("Audio Service initialized")
            
            if VisionService:
                components["vision_service"] = VisionService(
                    config=self.config.get("vision_config", {})
                )
                self.logger.info("Vision Service initialized")
            
            # Initialize Language Model Service
            if MultiLLMService:
                components["llm_service"] = MultiLLMService()
                self.logger.info("Multi-LLM Service initialized")
            
            # Initialize Dialogue Manager (Skip complex initialization for now)
            # if DialogueManager:
            #     components["dialogue_manager"] = DialogueManager(...)
            #     self.logger.info("Dialogue Manager initialized")
            
            # Initialize Learning Manager (Skip complex initialization for now) 
            # if LearningManager:
            #     components["learning_manager"] = LearningManager(...)
            #     self.logger.info("Learning Manager initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            
        self.logger.info(f"Initialized {len(components)} core components successfully")
        return components

    async def process_complex_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """處理複雜任務的核心協調方法"""
        task_id = task.get('id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.logger.info(f"Processing complex task '{task.get('name')}' (ID: {task_id})")
        
        # Store task context in memory
        if self.components.get('memory_manager'):
            try:
                await self.components['memory_manager'].store_memory(
                    f"task_context_{task_id}",
                    {"task": task, "timestamp": datetime.now().isoformat()},
                    memory_type="task"
                )
            except Exception as e:
                self.logger.warning(f"Could not store task context: {e}")
        
        try:
            # 智能任務分析和分解
            subtasks = await self._intelligent_decompose_task(task)
            
            # 制定動態執行計畫
            execution_plan = await self._create_dynamic_execution_plan(subtasks)
            
            # 並行和順序執行任務
            results = await self._execute_with_coordination(execution_plan, task_id)
            
            # 智能結果整合
            final_result = await self._intelligent_integrate_results(results, task)
            
            # 因果學習和系統改進
            await self._causal_learning_and_improvement(task, final_result)
            
            # 記錄成功執行
            if self.components.get('memory_manager'):
                try:
                    await self.components['memory_manager'].store_memory(
                        f"task_result_{task_id}",
                        {"result": final_result, "execution_time": datetime.now().isoformat()},
                        memory_type="result"
                    )
                except Exception as e:
                    self.logger.warning(f"Could not store task result: {e}")
            
            self.logger.info(f"Complex task '{task.get('name')}' completed successfully")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error processing task '{task.get('name')}': {e}")
            error_result = {
                "status": "error",
                "error": str(e),
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store error for learning
            if self.components.get('memory_manager'):
                try:
                    await self.components['memory_manager'].store_memory(
                        f"task_error_{task_id}",
                        error_result,
                        memory_type="error"
                    )
                except Exception as e:
                    self.logger.warning(f"Could not store task error: {e}")
            
            return error_result

    async def _create_dynamic_execution_plan(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """創建動態執行計劃，考慮依賴關係和資源約束"""
        self.logger.debug(f"Creating dynamic execution plan for {len(subtasks)} subtasks")
        
        # 按優先級排序
        sorted_tasks = sorted(subtasks, key=lambda x: x.get('priority', 5))
        
        # 分析依賴關係並分組
        execution_plan = []
        for task in sorted_tasks:
            task['estimated_start_time'] = datetime.now().isoformat()
            task['allocated_component'] = task.get('component', 'llm_service')
            execution_plan.append(task)
        
        return execution_plan
    
    async def _execute_with_coordination(self, execution_plan: List[Dict[str, Any]], task_id: str) -> List[Dict[str, Any]]:
        """協調執行子任務，支持並行和順序執行"""
        self.logger.info(f"Executing {len(execution_plan)} subtasks with coordination")
        results = []
        
        for subtask in execution_plan:
            try:
                # 獲取負責的組件
                component_name = subtask.get('allocated_component', 'llm_service')
                responsible_component = self.components.get(component_name)
                
                if responsible_component:
                    # 執行子任務
                    if hasattr(responsible_component, 'process') or hasattr(responsible_component, 'execute'):
                        if hasattr(responsible_component, 'process'):
                            result = await responsible_component.process(subtask.get('input', subtask))
                        else:
                            result = await responsible_component.execute(subtask.get('input', subtask))
                    else:
                        # 模擬執行
                        result = await self._simulate_component_execution(responsible_component, subtask)
                    
                    result['subtask_id'] = subtask.get('id')
                    result['component_used'] = component_name
                    results.append(result)
                else:
                    # 組件不可用，記錄錯誤
                    error_result = {
                        "status": "error",
                        "error": f"Component {component_name} not available",
                        "subtask_id": subtask.get('id'),
                        "component_used": component_name
                    }
                    results.append(error_result)
                    
            except Exception as e:
                self.logger.error(f"Error executing subtask {subtask.get('id')}: {e}")
                error_result = {
                    "status": "error",
                    "error": str(e),
                    "subtask_id": subtask.get('id')
                }
                results.append(error_result)
        
        return results
    
    async def _simulate_component_execution(self, component: Any, subtask: Dict[str, Any]) -> Dict[str, Any]:
        """模擬組件執行（用於還沒有完整實現execute方法的組件）"""
        await asyncio.sleep(0.1)  # 模擬處理時間
        return {
            "status": "success",
            "output": f"Simulated processing of {subtask.get('name')} by {component.__class__.__name__}",
            "component_type": component.__class__.__name__
        }

    async def _establish_inter_component_connections(self):
        """建立組件間的實際連接和通訊通道"""
        self.logger.info("Establishing inter-component connections...")
        
        try:
            # 建立記憶系統之間的連接
            if self.components.get('memory_manager') and self.components.get('vector_store'):
                # 將向量存儲連接到HAM記憶管理器
                if hasattr(self.components['memory_manager'], 'set_vector_store'):
                    self.components['memory_manager'].set_vector_store(
                        self.components['vector_store']
                    )
                self.logger.debug("Connected memory manager with vector store")
            
            # 建立推理引擎與記憶系統的連接
            if self.components.get('reasoning_engine') and self.components.get('memory_manager'):
                if hasattr(self.components['reasoning_engine'], 'set_memory_manager'):
                    self.components['reasoning_engine'].set_memory_manager(
                        self.components['memory_manager']
                    )
                self.logger.debug("Connected reasoning engine with memory manager")
            
            # 建立HSP通訊連接
            if self.components.get('hsp_connector'):
                # 為所有組件註冊HSP通訊能力
                for component_name, component in self.components.items():
                    if hasattr(component, 'set_hsp_connector'):
                        component.set_hsp_connector(self.components['hsp_connector'])
                        self.logger.debug(f"Registered HSP connector for {component_name}")
            
            # 建立多模態服務間的協調
            multimodal_services = {
                'audio': self.components.get('audio_service'),
                'vision': self.components.get('vision_service'),
                'llm': self.components.get('llm_service')
            }
            
            available_services = {k: v for k, v in multimodal_services.items() if v is not None}
            
            if len(available_services) > 1:
                # 為每個多模態服務設置其他服務的引用
                for service_name, service in available_services.items():
                    other_services = {k: v for k, v in available_services.items() if k != service_name}
                    if hasattr(service, 'set_peer_services'):
                        service.set_peer_services(other_services)
                
                self.logger.info(f"Established multimodal coordination between {list(available_services.keys())}")
            
            # 建立對話管理器的連接
            if self.components.get('dialogue_manager'):
                dialogue_dependencies = {
                    'memory_manager': self.components.get('memory_manager'),
                    'llm_service': self.components.get('llm_service'),
                    'audio_service': self.components.get('audio_service'),
                    'vision_service': self.components.get('vision_service')
                }
                
                available_deps = {k: v for k, v in dialogue_dependencies.items() if v is not None}
                
                if hasattr(self.components['dialogue_manager'], 'set_dependencies'):
                    self.components['dialogue_manager'].set_dependencies(available_deps)
                    self.logger.debug(f"Connected dialogue manager with {list(available_deps.keys())}")
            
            # 建立學習管理器連接
            if self.components.get('learning_manager'):
                learning_deps = {
                    'memory_manager': self.components.get('memory_manager'),
                    'reasoning_engine': self.components.get('reasoning_engine'),
                    'vector_store': self.components.get('vector_store')
                }
                
                available_learning_deps = {k: v for k, v in learning_deps.items() if v is not None}
                
                if hasattr(self.components['learning_manager'], 'set_dependencies'):
                    self.components['learning_manager'].set_dependencies(available_learning_deps)
                    self.logger.debug(f"Connected learning manager with {list(available_learning_deps.keys())}")
            
            self.logger.info("Successfully established inter-component connections")
            
        except Exception as e:
            self.logger.error(f"Error establishing inter-component connections: {e}")

    async def _integrate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Conceptual: Integrates results from subtask executions."""
        self.logger.debug("Integrating results (conceptual)...")
        await asyncio.sleep(0.005)
        # Dummy integration: combine statuses
        overall_status = "success" if all(r.get("status") == "success" for r in results) else "failure"
        return {"status": overall_status, "integrated_output": [r.get("output") for r in results]}

    async def _call_llm_for_decomposition(self, prompt: str) -> Dict[str, Any]:
        """使用LLM服務進行任務分解"""
        try:
            if self.components.get('llm_service'):
                # 模擬LLM調用進行任務分解
                response = await self.components['llm_service'].generate_response(
                    prompt, max_tokens=500
                )
                # 解析結構化響應
                return self._parse_decomposition_response(response)
            return {"subtasks": []}
        except Exception as e:
            self.logger.error(f"Error calling LLM for decomposition: {e}")
            return {"subtasks": []}
    
    def _parse_decomposition_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的任務分解響應"""
        # 簡化的解析邏輯，實際實現會更複雜
        subtasks = []
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                task_name = line.strip()[1:].strip()
                if task_name:
                    subtasks.append({
                        'name': task_name,
                        'component': 'llm_service',
                        'priority': 2
                    })
        return {"subtasks": subtasks}
    
    async def _combine_text_outputs(self, text_outputs: List[str]) -> str:
        """整合多個文本輸出"""
        if not text_outputs:
            return ""
        
        if len(text_outputs) == 1:
            return text_outputs[0]
        
        # 使用LLM服務整合文本
        if self.components.get('llm_service'):
            combination_prompt = f"""
            整合以下文本輸出為一個連貫的摘要：
            {chr(10).join([f"{i+1}. {text}" for i, text in enumerate(text_outputs)])}
            """
            try:
                combined = await self.components['llm_service'].generate_response(
                    combination_prompt, max_tokens=300
                )
                return combined
            except Exception as e:
                self.logger.error(f"Error combining text outputs: {e}")
        
        # 回退到簡單連接
        return " ".join(text_outputs)
    
    async def _intelligent_decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """智能任務分解：使用LLM和因果推理分解複雜任務"""
        self.logger.debug(f"Intelligently decomposing task: {task.get('name')}")
        
        subtasks = []
        task_type = task.get('type', 'general')
        
        try:
            # 使用LLM服務進行任務分解
            if self.components.get('llm_service'):
                decomposition_prompt = f"""
                分解以下複雜任務為具體的子任務：
                任務名稱：{task.get('name', 'Unknown')}
                任務描述：{task.get('description', 'No description')}
                任務類型：{task_type}
                
                請提供結構化的子任務列表，每個子任務包含：
                1. 任務名稱
                2. 所需組件
                3. 預期輸出
                4. 優先級
                """
                
                # 簡化的LLM調用（實際實現會使用完整的LLM服務）
                llm_response = await self._call_llm_for_decomposition(decomposition_prompt)
                subtasks.extend(llm_response.get('subtasks', []))
            
            # 基於任務類型的智能分解
            if task_type == 'multimodal_analysis':
                subtasks.extend([
                    {
                        'name': 'audio_processing',
                        'component': 'audio_service',
                        'input': task.get('audio_data'),
                        'priority': 1
                    },
                    {
                        'name': 'vision_processing', 
                        'component': 'vision_service',
                        'input': task.get('image_data'),
                        'priority': 1
                    },
                    {
                        'name': 'text_analysis',
                        'component': 'llm_service',
                        'input': task.get('text_data'),
                        'priority': 2
                    }
                ])
            elif task_type == 'reasoning_task':
                subtasks.extend([
                    {
                        'name': 'gather_context',
                        'component': 'memory_manager',
                        'input': task.get('context_query'),
                        'priority': 1
                    },
                    {
                        'name': 'causal_analysis',
                        'component': 'reasoning_engine',
                        'input': task.get('reasoning_data'),
                        'priority': 2
                    }
                ])
            else:
                # 通用任務分解
                subtasks.append({
                    'name': f"process_{task.get('name', 'unknown')}",
                    'component': 'llm_service',
                    'input': task,
                    'priority': 1
                })
            
            # 添加任務ID和時間戳
            for i, subtask in enumerate(subtasks):
                subtask['id'] = f"{task.get('id', 'task')}_{i}"
                subtask['parent_task'] = task.get('id')
                subtask['created_at'] = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Error in task decomposition: {e}")
            # 回退到簡單分解
            subtasks = [{
                'name': 'fallback_processing',
                'component': 'llm_service',
                'input': task,
                'priority': 1,
                'id': f"{task.get('id', 'task')}_fallback"
            }]
        
        self.logger.info(f"Decomposed task into {len(subtasks)} subtasks")
        return subtasks
    
    async def _intelligent_integrate_results(self, results: List[Dict[str, Any]], original_task: Dict[str, Any]) -> Dict[str, Any]:
        """智能結果整合：使用多模態融合和語義理解整合子任務結果"""
        self.logger.debug("Intelligently integrating results from subtasks...")
        
        if not results:
            return {"status": "error", "message": "No results to integrate"}
        
        # 分析結果狀態
        successful_results = [r for r in results if r.get("status") == "success"]
        failed_results = [r for r in results if r.get("status") != "success"]
        
        # 計算整體成功率
        success_rate = len(successful_results) / len(results) if results else 0
        
        integrated_result = {
            "status": "success" if success_rate >= 0.7 else "partial" if success_rate > 0 else "failed",
            "success_rate": success_rate,
            "total_subtasks": len(results),
            "successful_subtasks": len(successful_results),
            "failed_subtasks": len(failed_results),
            "task_id": original_task.get('id'),
            "integration_timestamp": datetime.now().isoformat()
        }
        
        # 多模態結果融合
        multimodal_outputs = {}
        text_outputs = []
        numerical_outputs = []
        
        for result in successful_results:
            output = result.get("output", {})
            
            # 分類和整合不同類型的輸出
            if isinstance(output, dict):
                if "audio_features" in output:
                    multimodal_outputs["audio"] = output["audio_features"]
                if "image_analysis" in output:
                    multimodal_outputs["vision"] = output["image_analysis"]
                if "text_analysis" in output:
                    text_outputs.append(output["text_analysis"])
                if "numerical_result" in output:
                    numerical_outputs.append(output["numerical_result"])
            elif isinstance(output, str):
                text_outputs.append(output)
            elif isinstance(output, (int, float)):
                numerical_outputs.append(output)
        
        # 整合文本輸出
        if text_outputs:
            integrated_result["text_summary"] = await self._combine_text_outputs(text_outputs)
        
        # 整合數值結果
        if numerical_outputs:
            integrated_result["numerical_summary"] = {
                "average": sum(numerical_outputs) / len(numerical_outputs),
                "max": max(numerical_outputs),
                "min": min(numerical_outputs),
                "count": len(numerical_outputs)
            }
        
        # 多模態特徵融合
        if multimodal_outputs:
            integrated_result["multimodal_features"] = multimodal_outputs
        
        # 錯誤和警告彙總
        if failed_results:
            integrated_result["errors"] = [
                {"subtask": r.get("subtask_id"), "error": r.get("error", "Unknown error")}
                for r in failed_results
            ]
        
        # 置信度評估
        integrated_result["confidence"] = self._calculate_integration_confidence(
            successful_results, failed_results, original_task
        )
        
        self.logger.info(f"Integration completed with {success_rate:.2%} success rate")
        return integrated_result
    
    async def _causal_learning_and_improvement(self, task: Dict[str, Any], final_result: Dict[str, Any]):
        """因果學習和系統改進：從任務執行中學習並改進系統性能"""
        self.logger.debug("Performing causal learning and system improvement...")
        
        try:
            # 記錄執行數據用於因果分析
            execution_data = {
                "task_type": task.get('type'),
                "task_complexity": len(task.get('subtasks', [])),
                "execution_time": final_result.get('execution_time'),
                "success_rate": final_result.get('success_rate', 0),
                "confidence": final_result.get('confidence', 0),
                "components_used": final_result.get('components_used', []),
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用因果推理引擎學習執行模式
            if self.components.get('reasoning_engine'):
                await self.components['reasoning_engine'].learn_causal_relationships([
                    {
                        "variables": list(execution_data.keys()),
                        "data": execution_data,
                        "outcome": final_result.get('status'),
                        "id": f"execution_{task.get('id')}"
                    }
                ])
            
            # 學習管理器記錄經驗
            if self.components.get('learning_manager'):
                learning_data = {
                    "experience_type": "task_execution",
                    "input": task,
                    "output": final_result,
                    "context": execution_data,
                    "success": final_result.get('status') == 'success'
                }
                
                # 模擬學習管理器的經驗記錄
                if hasattr(self.components['learning_manager'], 'record_experience'):
                    await self.components['learning_manager'].record_experience(learning_data)
            
            # 向量存儲中保存執行模式
            if self.components.get('vector_store'):
                pattern_description = f"""
                Task execution pattern:
                Type: {task.get('type', 'unknown')}
                Success rate: {final_result.get('success_rate', 0):.2%}
                Confidence: {final_result.get('confidence', 0):.2f}
                Components: {', '.join(final_result.get('components_used', []))}
                """
                
                await self.components['vector_store'].add_memory(
                    memory_id=f"pattern_{task.get('id')}",
                    content=pattern_description,
                    metadata={
                        "type": "execution_pattern",
                        "task_type": task.get('type'),
                        "success_rate": final_result.get('success_rate', 0),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # 系統性能調優建議
            improvement_suggestions = await self._generate_improvement_suggestions(
                execution_data, final_result
            )
            
            if improvement_suggestions:
                self.logger.info(f"Generated {len(improvement_suggestions)} improvement suggestions")
                
        except Exception as e:
            self.logger.error(f"Error in causal learning and improvement: {e}")
        return " ".join(text_outputs)
    
    def _calculate_integration_confidence(self, successful_results: List[Dict], 
                                        failed_results: List[Dict], 
                                        original_task: Dict[str, Any]) -> float:
        """計算結果整合的置信度"""
        total_results = len(successful_results) + len(failed_results)
        if total_results == 0:
            return 0.0
        
        success_rate = len(successful_results) / total_results
        
        # 基於任務類型調整置信度
        task_type = original_task.get('type', 'general')
        if task_type == 'multimodal_analysis':
            # 多模態任務需要更高的成功率
            confidence = success_rate * 0.8 if success_rate >= 0.8 else success_rate * 0.5
        elif task_type == 'reasoning_task':
            # 推理任務對準確性要求更高
            confidence = success_rate * 0.9 if success_rate >= 0.9 else success_rate * 0.6
        else:
            confidence = success_rate * 0.85
        
        return min(confidence, 1.0)
    
    async def _generate_improvement_suggestions(self, execution_data: Dict[str, Any], 
                                              final_result: Dict[str, Any]) -> List[str]:
        """生成系統改進建議"""
        suggestions = []
        
        success_rate = final_result.get('success_rate', 0)
        confidence = final_result.get('confidence', 0)
        
        if success_rate < 0.7:
            suggestions.append("考慮改進任務分解策略以提高成功率")
        
        if confidence < 0.6:
            suggestions.append("需要加強組件間的協調和結果驗證")
        
        execution_time = execution_data.get('execution_time')
        if execution_time and execution_time > 30:  # 假設30秒為閾值
            suggestions.append("優化執行效率，考慮並行處理更多子任務")
        
        return suggestions
