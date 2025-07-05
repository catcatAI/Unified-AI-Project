import unittest
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from fragmenta.fragmenta_orchestrator import FragmentaOrchestrator
from unittest.mock import MagicMock, call
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from services.llm_interface import LLMInterface
from tools.tool_dispatcher import ToolDispatcher

class TestFragmentaOrchestrator(unittest.TestCase):

    def setUp(self):
        self.mock_llm_interface = MagicMock(spec=LLMInterface)
        self.mock_llm_interface.generate_response.side_effect = lambda prompt, params=None: f"LLM mock response for: {prompt}"

        self.mock_ham_manager = MagicMock(spec=HAMMemoryManager)
        self.mock_ham_manager.store_experience.side_effect = lambda raw_data, data_type, metadata: f"mem_{metadata.get('chunk_index', 0)}_{metadata.get('original_task_id', 'task')}"

        def mock_recall_gist_side_effect(memory_id):
            if "task_short_123" in memory_id and "0" in memory_id :
                 return {"rehydrated_gist": f"LLM mock response for: Process this data chunk (1/1) for task task_short_123: Hello world." , "metadata": {}}
            if "task_long_456" in memory_id: # For test_03
                long_text_for_mock = "This is a sentence that is quite long and should be chunked."
                chunk1_content = long_text_for_mock[0:50]
                chunk2_content = long_text_for_mock[45:58]
                mock_resp1 = f"Summary C1: {chunk1_content[:10]}"
                mock_resp2 = f"Summary C2: {chunk2_content[:10]}"
                if memory_id == f"mem_0_task_long_456": return {"rehydrated_gist": mock_resp1, "metadata":{}}
                if memory_id == f"mem_1_task_long_456": return {"rehydrated_gist": mock_resp2, "metadata":{}}
            if "task_tool_789" in memory_id:
                 return {"rehydrated_gist": "Result: 4", "metadata":{}}
            return {"rehydrated_gist": f"Content for {memory_id}", "metadata": {}}
        self.mock_ham_manager.recall_gist.side_effect = mock_recall_gist_side_effect

        self.mock_tool_dispatcher = MagicMock(spec=ToolDispatcher)
        self.mock_tool_dispatcher.tools = {"calculate": MagicMock(), "evaluate_logic": MagicMock(), "translate_text": MagicMock()}

        self.orchestrator = FragmentaOrchestrator(
            ham_manager=self.mock_ham_manager,
            tool_dispatcher=self.mock_tool_dispatcher,
            llm_interface=self.mock_llm_interface,
            config={"default_chunking_threshold": 30,
                    "default_text_chunking_params": {"chunk_size": 50, "overlap": 5}}
        )

    def test_01_orchestrator_initialization(self):
        self.assertIsNotNone(self.orchestrator)
        print("TestFragmentaOrchestrator.test_01_orchestrator_initialization PASSED")

    def test_02_process_complex_task_short_text_direct_processing(self):
        task_desc = {"goal": "process short text", "task_id": "task_short_123"}
        short_text = "Hello world."
        expected_llm_call_prompt = f"Process this data chunk (1/1) for task {task_desc['task_id']}: {short_text}"
        expected_llm_response = f"LLM mock response for: {expected_llm_call_prompt}"

        self.mock_llm_interface.generate_response.reset_mock(); self.mock_llm_interface.generate_response.side_effect = [expected_llm_response]
        self.mock_ham_manager.store_experience.reset_mock(); self.mock_ham_manager.recall_gist.reset_mock()
        # Configure recall_gist mock specifically for this test's expected memory ID
        expected_mem_id = f"mem_0_{task_desc['task_id']}"
        self.mock_ham_manager.recall_gist.side_effect = lambda mem_id: {"rehydrated_gist": expected_llm_response} if mem_id == expected_mem_id else None

        result = self.orchestrator.process_complex_task(task_desc, short_text)
        self.mock_llm_interface.generate_response.assert_called_once_with(prompt=expected_llm_call_prompt, params={})
        self.assertEqual(result, expected_llm_response)
        self.mock_ham_manager.store_experience.assert_called_once()
        call_args = self.mock_ham_manager.store_experience.call_args_list[0]
        self.assertEqual(call_args.kwargs['raw_data'], expected_llm_response)
        self.assertEqual(call_args.kwargs['data_type'], "fragmenta_chunk_result")
        self.mock_ham_manager.recall_gist.assert_called_once_with(expected_mem_id)
        print("TestFragmentaOrchestrator.test_02_process_complex_task_short_text_direct_processing PASSED")

    def test_03_process_complex_task_long_text_chunking(self):
        task_desc = {"goal": "summarize long text", "task_id": "task_long_456"}
        long_text = "This is a sentence that is quite long and should be chunked." # len 58

        chunk1_text = long_text[0:50]  # "This is a sentence that is quite long and should "
        chunk2_text = long_text[45:58] # "ould be chunked."

        expected_prompt_chunk1 = f"Summarize this text chunk (1/2) for task {task_desc['task_id']}: {chunk1_text}"
        expected_prompt_chunk2 = f"Summarize this text chunk (2/2) for task {task_desc['task_id']}: {chunk2_text}"

        mock_response_chunk1 = f"Summary C1: {chunk1_text[:10]}"
        mock_response_chunk2 = f"Summary C2: {chunk2_text[:10]}"

        self.mock_llm_interface.generate_response.reset_mock(); self.mock_llm_interface.generate_response.side_effect = [mock_response_chunk1, mock_response_chunk2]
        self.mock_ham_manager.store_experience.reset_mock()
        mem_id_chunk1 = f"mem_0_{task_desc['task_id']}"
        mem_id_chunk2 = f"mem_1_{task_desc['task_id']}"
        self.mock_ham_manager.store_experience.side_effect = [mem_id_chunk1, mem_id_chunk2]
        self.mock_ham_manager.recall_gist.reset_mock()
        def recall_side_effect_long_text(mem_id):
            if mem_id == mem_id_chunk1: return {"rehydrated_gist": mock_response_chunk1}
            if mem_id == mem_id_chunk2: return {"rehydrated_gist": mock_response_chunk2}
            return None
        self.mock_ham_manager.recall_gist.side_effect = recall_side_effect_long_text

        expected_merged_result = f"{mock_response_chunk1}\n{mock_response_chunk2}"
        result = self.orchestrator.process_complex_task(task_desc, long_text)

        self.assertEqual(self.mock_llm_interface.generate_response.call_count, 2)
        llm_calls = self.mock_llm_interface.generate_response.call_args_list
        self.assertEqual(llm_calls[0].kwargs['prompt'], expected_prompt_chunk1)
        self.assertEqual(llm_calls[1].kwargs['prompt'], expected_prompt_chunk2) # Critical assertion
        self.assertEqual(result, expected_merged_result)
        self.assertEqual(self.mock_ham_manager.store_experience.call_count, 2)
        self.assertEqual(self.mock_ham_manager.recall_gist.call_count, 2)
        print("TestFragmentaOrchestrator.test_03_process_complex_task_long_text_chunking PASSED")

    def test_04_analyze_input_placeholder(self):
        analysis_text = self.orchestrator._analyze_input("hello")
        self.assertEqual(analysis_text["type"], "text"); self.assertEqual(analysis_text["size"], 5)
        analysis_list = self.orchestrator._analyze_input([1,2,3])
        self.assertEqual(analysis_list["type"], "structured_data"); self.assertEqual(analysis_list["size"], 3)
        print("TestFragmentaOrchestrator.test_04_analyze_input_placeholder PASSED")

    def test_05_chunking_placeholder(self):
        long_text = "This is a sentence that is quite long and should be chunked." # len 58
        chunks_long = self.orchestrator._chunk_data(long_text, {"chunk_size": 30, "overlap": 5})
        self.assertEqual(len(chunks_long), 3)
        self.assertEqual(chunks_long[0], "This is a sentence that is qui")
        self.assertEqual(chunks_long[1], "s quite long and should be chu")
        self.assertEqual(chunks_long[2], "e chunked.")
        print("TestFragmentaOrchestrator.test_05_chunking_placeholder PASSED")

    def test_06_process_task_with_tool_dispatch(self):
        task_desc = {"goal": "calculate", "requested_tool": "calculate", "task_id": "task_tool_789"}
        input_data = "2 + 2"; mock_tool_result = "Result: 4"
        self.mock_tool_dispatcher.dispatch.return_value = mock_tool_result
        expected_mem_id = f"mem_0_{task_desc['task_id']}"
        self.mock_ham_manager.recall_gist.side_effect = lambda mem_id: {"rehydrated_gist": mock_tool_result} if mem_id == expected_mem_id else None
        self.mock_llm_interface.generate_response.reset_mock(); self.mock_ham_manager.store_experience.reset_mock()
        result = self.orchestrator.process_complex_task(task_desc, input_data)
        self.mock_tool_dispatcher.dispatch.assert_called_once_with(query=input_data, explicit_tool_name="calculate")
        self.mock_llm_interface.generate_response.assert_not_called()
        self.assertEqual(result, mock_tool_result)
        self.mock_ham_manager.store_experience.assert_called_once()
        self.mock_ham_manager.recall_gist.assert_called_once_with(expected_mem_id)
        print("TestFragmentaOrchestrator.test_06_process_task_with_tool_dispatch PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
