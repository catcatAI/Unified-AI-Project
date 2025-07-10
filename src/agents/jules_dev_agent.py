from typing import Dict, Any, List

from src.shared.types.common_types import AIVirtualInputServiceCommandResponse, VirtualKeyboardCommand, VirtualMouseCommand # Assuming AVIS types might be used

# Forward declaration for services that might be injected
class DialogueManager: # Placeholder
    pass
class AIVirtualInputService: # Placeholder
    pass
class SandboxExecutor: # Placeholder
    pass
class LightweightCodeModel: # Placeholder
    pass
class HAMMemoryManager: # Placeholder
    pass
class LLMInterface: # Placeholder
    pass
class ToolDispatcher: # Placeholder
    pass


class JulesDevelopmentCapability:
    """
    Jules - Asynchronous Development Capability.
    Provides functionalities for handling software development tasks like bug fixing and
    feature implementation, intended to be orchestrated by a central AI persona (e.g., Angela).
    """

    def __init__(self,
                 # dialogue_manager: DialogueManager, # No longer needed directly, Angela manages dialogue
                 avis_service: AIVirtualInputService,
                 sandbox_executor: SandboxExecutor,
                 code_model: LightweightCodeModel,
                 memory_manager: HAMMemoryManager,
                 llm_interface: LLMInterface,
                 tool_dispatcher: ToolDispatcher,
                 config: Dict[str, Any] = None):
        """
        Initializes the JulesDevelopmentCapability.
        This capability module is expected to be instantiated and used by a central orchestrator (e.g., Angela).

        Args:
            avis_service: Service for interacting with a simulated GUI environment.
            sandbox_executor: Service for executing code in a sandboxed environment.
            code_model: Service for understanding code structure.
            memory_manager: Service for storing and retrieving task states, learnings.
            llm_interface: Interface to large language models for generation and understanding.
            tool_dispatcher: Service for dispatching tasks to specialized tools.
            config: Configuration dictionary relevant to this capability.
        """
        # self.dialogue_manager = dialogue_manager # Removed
        self.avis_service = avis_service
        self.sandbox_executor = sandbox_executor
        self.code_model = code_model
        self.memory_manager = memory_manager
        self.llm_interface = llm_interface
        self.tool_dispatcher = tool_dispatcher
        self.config = config or {}
        self.current_task_context = None # Stores context for the current task being handled by this capability
        self.current_plan_for_task = None # Stores the plan for the current task

        print("JulesDevelopmentCapability initialized.")

    def process_development_task_description(self, task_description: str, task_id: str = None) -> Dict[str, Any]:
        """
        Processes a development task description provided by the orchestrating AI (e.g., Angela).
        This method helps in understanding and structuring the task.

        Args:
            task_description: Natural language description of the task from the orchestrator.
            task_id: Optional unique ID for the task, managed by the orchestrator.

        Returns:
            A dictionary containing the structured task context or an error status.
        """
        print(f"JulesDevelopmentCapability: Processing task description: {task_description}")
        # 1. Use LLMInterface to parse task_description into a structured format.
        #    This structured information becomes the self.current_task_context.
        #    The orchestrator (Angela) would be responsible for the initial intake and dialogue.
        #    This method is for Jules to structure the specifics for its operational context.
        # 2. Potentially use HAMMemoryManager to save task details under Angela's context or a Jules-specific context.
        self.current_task_context = {
            "id": task_id or "jules_task_001", # ID might be prefixed by Angela
            "original_description": task_description,
            "parsed_type": "unknown", # To be filled by LLM (e.g., "bugfix", "feature")
            "relevant_files_identified": [], # To be filled by LLM or analysis
            "goal_summary": "", # To be filled by LLM
            "status": "description_processed",
            "code_analysis": None,
            "plan": None,
            "step_results": {},
            "output": None
        }
        # Example LLM call to populate context (conceptual)
        # prompt = f"Parse the following development task into type, relevant_files, goal_summary: {task_description}"
        # parsed_info = await self.llm_interface.generate_structured_output(prompt) # Assuming such a method
        # if parsed_info:
        #     self.current_task_context.update(parsed_info)

        # Example: self.memory_manager.store_experience(self.current_task_context, "jules_capability_task_processed", metadata={"orchestrator_task_id": task_id})
        return {"status": "success", "message": "Task description processed, context created.", "task_context": self.current_task_context}

    async def analyze_code_context_for_task(self, relevant_files: List[str] = None) -> Dict[str, Any]:
        """
        Analyzes specified code files to understand context for the current task,
        updating the self.current_task_context.
        Relevant files might be provided or inferred from task_context.

        Args:
            relevant_files: A list of file paths. If None, attempts to use from current_task_context.

        Returns:
            A dictionary with analysis summary or error status.
        """
        if not self.current_task_context:
            return {"status": "error", "message": "No current task context to analyze."}

        files_to_analyze = relevant_files or self.current_task_context.get("relevant_files_identified", [])
        if not files_to_analyze:
            return {"status": "warning", "message": "No relevant files specified or identified for analysis."}

        print(f"JulesDevelopmentCapability: Analyzing codebase context for files: {files_to_analyze}")
        analysis_results = {}
        for file_path in files_to_analyze:
            # In a real scenario, this might involve AVIS to "read" virtual files
            # then pass content to LightweightCodeModel or LLM for deeper analysis.
            # For now, using a simplified mock via code_model.
            try:
                # structure = self.code_model.get_tool_structure(file_path) # Adapt to actual method
                # Mocking the call for now as get_tool_structure might expect a tool name not a path
                structure = {"path": file_path, "summary": f"Mocked structure for {file_path}", "functions": [{"name": f"mock_func_in_{file_path.replace('/', '_')}"}]}
                analysis_results[file_path] = structure
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                analysis_results[file_path] = {"error": str(e)}

        self.current_task_context["code_analysis"] = analysis_results
        self.current_task_context["status"] = "context_analyzed"
        return {"status": "success", "message": "Codebase context analyzed." , "analysis": analysis_results}

    async def develop_solution_plan(self) -> Dict[str, Any]:
        """
        Develops a step-by-step plan to address the current task,
        updating self.current_task_context.

        Returns:
            A dictionary containing the plan or an error status.
        """
        if not self.current_task_context or not self.current_task_context.get("code_analysis"):
            return {"status": "error", "message": "Task context or code analysis missing for planning."}

        task_id = self.current_task_context.get('id', 'unknown_task')
        print(f"JulesDevelopmentCapability: Developing plan for task: {task_id}")

        # Conceptual: Use LLM with full task context to generate a plan.
        # prompt = f"Given task: {self.current_task_context['original_description']} " \
        #            f"and code analysis: {self.current_task_context['code_analysis']}, " \
        #            f"generate a detailed step-by-step plan to achieve the goal. " \
        #            f"Plan steps should be one of: avis_read_file, llm_analyze_code, llm_generate_code_modification, " \
        #            f"avis_write_file, sandbox_run_test, generate_commit_message, generate_git_commands."
        # generated_plan_struct = await self.llm_interface.generate_structured_output(prompt, output_schema=List[Dict]) # Assuming schema

        # Using a more concrete example plan for now:
        example_plan = [
            {"type": "avis_read_file", "path": "src/module/file.py", "output_key": "file_content"},
            {"type": "llm_generate_code_modification",
             "inputs": {"original_code_var": "file_content", "task_description": self.current_task_context['original_description']},
             "instruction": "Based on the task, provide the modified code block.",
             "output_key": "modified_code_block"},
            {"type": "avis_apply_modification", # New conceptual step: apply a block modification
             "path": "src/module/file.py", # Or use file_content_var and target specific lines
             "modification_var": "modified_code_block" # This might be a diff or specific instructions
            },
            {"type": "sandbox_run_test", "script_path": "tests/test_file.py", "inputs": {}}, # Pass relevant context if tests need it
            {"type": "generate_commit_message", "inputs": {"task_description": self.current_task_context['original_description'], "changes_made_summary_var": "modification_summary_from_llm"}}, # summary could be another llm step
        ]
        self.current_plan_for_task = example_plan # generated_plan_struct or example_plan
        self.current_task_context["plan"] = self.current_plan_for_task
        self.current_task_context["status"] = "plan_developed"
        # self.memory_manager.store_experience(self.current_plan_for_task, "jules_capability_plan", metadata={"task_id": task_id})
        return {"status": "success", "message": "Solution plan developed.", "plan": self.current_plan_for_task}

    async def execute_step_in_plan(self, step_index: int, current_step_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a single step from the current plan.
        This method is async to accommodate potential long-running operations like AVIS calls or LLM interactions.

        Args:
            step_index: The index of the plan step to execute.
            current_step_outputs: A dictionary holding outputs from previous steps, used for input to current step.

        Returns:
            A dictionary with the outcome of the step execution and any new outputs.
        """
        if not self.current_plan_for_task or step_index >= len(self.current_plan_for_task):
            return {"status": "error", "message": "Invalid plan or step index."}

        step = self.current_plan_for_task[step_index]
        step_type = step.get("type")
        task_id = self.current_task_context.get('id', 'unknown_task')
        print(f"JulesDevelopmentCapability: Executing plan step {step_index} ({step_type}) for task {task_id}")

        step_input_params = {}
        if "inputs" in step:
            for param_name, source_key in step["inputs"].items():
                if source_key in current_step_outputs:
                    step_input_params[param_name] = current_step_outputs[source_key]
                elif source_key in self.current_task_context: # Check task_context root for static values
                    step_input_params[param_name] = self.current_task_context[source_key]
                else:
                    # Potentially raise error or use a default if input is missing
                    print(f"Warning: Missing input '{source_key}' for step {step_index}")


        # This part is highly conceptual and needs actual implementation per step type
        step_execution_result = {"status": "success", "message": f"Step {step_type} processed."}
        new_outputs_from_step = {}

        # Actual implementation for 'avis_read_file'
        if step_type == "avis_read_file":
            file_path_to_read = step.get("path")
            output_key = step.get("output_key", "file_content") # Default output key
            if not file_path_to_read:
                step_execution_result = {"status": "error", "message": "Missing 'path' for avis_read_file step."}
            else:
                # Construct the command for AVIS
                # Ensure AVISFileOperationCommand and AVISFileOperationResponse are imported
                # from src.shared.types.common_types import AVISFileOperationCommand, AVISFileOperationResponse
                avis_command = {
                    "action_type": "file_operation",
                    "operation": "read_file",
                    "path": file_path_to_read
                }
                # AVIS service methods might not be async yet, adjust if they become async
                # For now, assuming synchronous for placeholder. If AVIS becomes async:
                # avis_response = await self.avis_service.process_file_operation_command(avis_command)
                if hasattr(self.avis_service, 'process_file_operation_command'):
                    # The actual AVIS method might need to be made async if it involves I/O
                    # For now, this is a conceptual synchronous call.
                    try:
                        # This will be a direct call, not async, if AVIS is not async.
                        # If AVIS method is async, this line needs `await`.
                        # Let's assume for now AVIS methods are not async for this placeholder.
                        # In a real scenario, AVIS file ops would likely be async.
                        # This will be updated when AVIS is updated.
                        avis_response = self.avis_service.process_file_operation_command(avis_command)

                        if avis_response.get("status") == "success":
                            new_outputs_from_step[output_key] = avis_response.get("content")
                            step_execution_result["message"] = f"Successfully read virtual file: {file_path_to_read}"
                        else:
                            step_execution_result["status"] = "error"
                            step_execution_result["message"] = f"AVIS Error reading {file_path_to_read}: {avis_response.get('message')}"
                    except Exception as e:
                        step_execution_result["status"] = "error"
                        step_execution_result["message"] = f"Exception calling AVIS for {file_path_to_read}: {str(e)}"
                else:
                    step_execution_result["status"] = "error"
                    step_execution_result["message"] = "AVIS service does not have 'process_file_operation_command' or is not available."

        elif step_type == "llm_generate_code_modification":
            # Conceptual: result = await self.llm_interface.generate_text(prompt=f"{step.get('instruction')} Code: {step_input_params.get('original_code_var')}")
            new_outputs_from_step[step.get("output_key", "modified_code")] = f"// Mock modified code for {step_input_params.get('task_description')}"
            step_execution_result["message"] = "LLM code modification simulated."
            pass # Retain pass for other conceptual types
        elif step_type == "sandbox_run_test":
            # Conceptual: result = await self.sandbox_executor.execute_python_code(script_content_or_path=step.get("script_path"))
            new_outputs_from_step["test_results"] = "Mock test passed."
            step_execution_result["message"] = "Sandbox test run simulated."
            pass # Retain pass
        # Add more step types...
        else:
            step_execution_result["message"] = f"Step type '{step_type}' simulation placeholder."

        # Update task context with step result, including any new outputs
        self.current_task_context["step_results"][step_index] = {**step_execution_result, "outputs": new_outputs_from_step}
        # self.memory_manager.store_experience(self.current_task_context["step_results"][step_index], "jules_capability_step_executed", metadata={"task_id": task_id, "step": step_index})

        return {**step_execution_result, "new_outputs": new_outputs_from_step}


    async def execute_full_solution_plan(self) -> Dict[str, Any]:
        """
        Executes all steps in the current plan sequentially for the current task.
        Manages the flow of outputs from one step to the inputs of the next.
        """
        if not self.current_plan_for_task:
            if not self.current_task_context or not self.current_task_context.get("plan"):
                 return {"status": "error", "message": "No plan developed for the current task."}
            self.current_plan_for_task = self.current_task_context.get("plan")

        overall_status = {"status": "success", "step_results": []}
        accumulated_outputs = {} # To pass outputs from one step to the next

        self.current_task_context["status"] = "executing_plan"
        for i, step_config in enumerate(self.current_plan_for_task):
            step_execution_outcome = await self.execute_step_in_plan(i, accumulated_outputs)
            overall_status["step_results"].append(step_execution_outcome)

            if "new_outputs" in step_execution_outcome:
                accumulated_outputs.update(step_execution_outcome["new_outputs"])

            if step_execution_outcome["status"] != "success": # Use '!= "success"' to catch 'failure', 'error' etc.
                print(f"JulesDevelopmentCapability: Error executing step {i} for task {self.current_task_context.get('id')}, aborting plan.")
                self.current_task_context["status"] = "plan_execution_failed"
                overall_status["status"] = "error"
                overall_status["message"] = f"Execution failed at step {i}: {step_execution_outcome.get('message')}"
                break

        if self.current_task_context["status"] == "executing_plan": # If not failed
            self.current_task_context["status"] = "plan_executed"
            overall_status["message"] = "Plan executed successfully."

        self.current_task_context["accumulated_outputs_at_plan_end"] = accumulated_outputs # Store for output generation
        return overall_status

    def generate_development_output(self) -> Dict[str, Any]:
        """
        Generates the final output for the task (e.g., diff, commit message, git commands).

        Returns:
            A dictionary containing the generated output.
        """
        if not self.current_task_context or self.current_task_context.get("status") not in ["plan_executed"]:
            return {"status": "error", "message": "Task's plan not successfully executed or task context missing for output generation."}

        task_id = self.current_task_context.get('id', 'unknown_task')
        print(f"JulesDevelopmentCapability: Generating output for task: {task_id}")
        # 1. Based on executed plan and results, generate output.
        #    - Code changes (diff format)
        #    - Commit message (using LLMInterface based on task and changes)
        #    - Git commands (text strings)

        # Conceptual: Use LLM to generate commit message based on task_description and accumulated_outputs
        # commit_prompt = f"Task: {self.current_task_context['original_description']}. Changes: {self.current_task_context.get('accumulated_outputs_at_plan_end', {}).get('modification_summary_from_llm', 'Modifications performed.')}. Generate a commit message."
        # commit_message = await self.llm_interface.generate_text(commit_prompt)
        commit_message = f"feat: Simulated fix for task {task_id} based on: {self.current_task_context['original_description'][:50]}..."


        simulated_diff = self.current_task_context.get("accumulated_outputs_at_plan_end", {}).get("modified_code_block", "Conceptual diff: -old_code\n+new_code")

        git_commands = [
            "git pull", # Conceptual
            f"git checkout -b feat/jules-task-{task_id}",
            # "git apply changes.diff" (if diff was generated and saved)
            # "git add .", # Or specific files based on plan
            f"git commit -m \"{commit_message}\"",
            f"git push origin feat/jules-task-{task_id}"
        ]
        output_data = {
            "task_id": task_id,
            "commit_message": commit_message,
            "simulated_diff": simulated_diff,
            "simulated_git_commands": git_commands,
            "final_status_message": f"Development task {task_id} output generated. Review and apply."
        }
        self.current_task_context["status"] = "output_generated"
        self.current_task_context["output"] = output_data
        # self.memory_manager.store_experience(output_data, "jules_capability_output", metadata={"task_id": task_id})
        return {"status": "success", "output": output_data}

    def get_current_task_status_and_context(self) -> Dict[str, Any]:
        """
        Reports the current status and context of the capability's active task.
        This would be called by the orchestrator (Angela) to get updates.
        """
        if self.current_task_context:
            return {"status": "info", "capability_name": "JulesDevelopmentCapability", "task_active": True, "task_context": self.current_task_context}
        else:
            return {"status": "info", "capability_name": "JulesDevelopmentCapability", "task_active": False, "message": "No active task."}

    def clear_current_task_context(self):
        """Clears the context for the current task, making the capability ready for a new one."""
        print(f"JulesDevelopmentCapability: Clearing context for task_id: {self.current_task_context.get('id', 'N/A') if self.current_task_context else 'N/A'}")
        self.current_task_context = None
        self.current_plan_for_task = None


# Example of how JulesDevelopmentCapability might be used by an orchestrator (e.g., Angela)
if __name__ == '__main__':
    import asyncio
    # Import the new AVIS command and response types for the mock
    from src.shared.types.common_types import AVISFileOperationCommand, AVISFileOperationResponse, Literal

    # Mock services for standalone execution
    class MockAIVirtualInputService:
        def __init__(self, name="MockAIVirtualInputService"):
            self.name = name
            self.virtual_file_system: Dict[str, str] = {}
            print(f"MockService '{name}' initialized.")

        def load_virtual_files(self, files_content: Dict[str, str]):
            self.virtual_file_system = files_content
            print(f"{self.name}: Loaded virtual files: {list(self.virtual_file_system.keys())}")

        # This mock needs to be synchronous to match the current Jules implementation.
        # If Jules's call to AVIS becomes async, this should also become async.
        def process_file_operation_command(self, command: AVISFileOperationCommand) -> AVISFileOperationResponse:
            print(f"{self.name}: processing file op command: {command}")
            op = command.get("operation")
            path = command.get("path")
            if op == "read_file":
                if path in self.virtual_file_system:
                    return {"status": "success", "content": self.virtual_file_system[path], "message": "File read successfully."}
                else:
                    return {"status": "error_file_not_found", "message": f"File '{path}' not found in mock AVIS."}
            return {"status": "error_other", "message": "Unsupported mock file operation."}

        async def process_virtual_command(self, *args, **kwargs): # Generic placeholder for other AVIS commands if needed
            print(f"{self.name}: processing generic AVIS command with {args}, {kwargs}")
            await asyncio.sleep(0.05)
            return {"status": "success", "message": "Mock generic AVIS command processed"}


    class MockService: # For other services
        def __init__(self, name="MockService"):
            self.name = name
            print(f"MockService '{name}' initialized.")

        def get_tool_structure(self, path): # Mock for LightweightCodeModel
             print(f"{self.name}: getting structure for {path}")
             return {"path": path, "functions": [{"name": "mock_func_in_" + path.replace('/', '_')}]}

        async def generate_text(self, prompt): # Mock for LLMInterface
            print(f"{self.name}: generating text for prompt: {prompt[:70]}...")
            await asyncio.sleep(0.05)
            if "commit message" in prompt.lower():
                return f"feat: Mock LLM generated commit for '{prompt[60:100]}...'"
            return f"Mocked LLM response for: {prompt[:70]}"

        async def generate_structured_output(self, prompt, output_schema=None): # Mock for LLMInterface
            print(f"{self.name}: generating structured output for prompt: {prompt[:70]}...")
            await asyncio.sleep(0.05)
            if "Parse the following development task" in prompt: # Corresponds to process_development_task_description
                return {"parsed_type": "bugfix",
                        "relevant_files_identified": ["src/main.py", "src/utils.py"], # Example files
                        "goal_summary": "Fix typo in calculate_sum in main.py and update its usage in utils.py"}
            if "generate a detailed step-by-step plan" in prompt: # Corresponds to develop_solution_plan
                 return [
                    {"type": "avis_read_file", "path": "src/main.py", "output_key": "main_py_content"},
                    {"type": "avis_read_file", "path": "src/utils.py", "output_key": "utils_py_content"},
                    {"type": "llm_generate_code_modification",
                     "inputs": {"original_code_var": "main_py_content", "task_description": "Fix typo in calculate_sum"},
                     "instruction": "In the provided code (main_py_content), find function 'calculate_sum' and fix typo 'smu' to 'sum'.",
                     "output_key": "modified_main_py_code_block"},
                    {"type": "llm_generate_code_modification",
                     "inputs": {"original_code_var": "utils_py_content", "task_description": "Update usage of calculate_sum if affected by changes in main.py"},
                     "instruction": "In utils_py_content, review usage of 'calculate_sum' and update if necessary.",
                     "output_key": "modified_utils_py_code_block"},
                    {"type": "avis_apply_modification", "path": "src/main.py", "modification_var": "modified_main_py_code_block"},
                    {"type": "avis_apply_modification", "path": "src/utils.py", "modification_var": "modified_utils_py_code_block"},
                    {"type": "sandbox_run_test", "script_path": "tests/test_main.py", "inputs": {}},
                    {"type": "generate_commit_message", "inputs": {"task_description": self.current_task_context['original_description'] if hasattr(self, 'current_task_context') and self.current_task_context else "N/A", "changes_made_summary_var": "final_summary_from_llm"}},
                ]
            return {} # Default empty structured output

        # Mock for SandboxExecutor if needed directly (though ASCS uses it)
        async def execute_python_code(self, code_string: str, timeout: int = 10):
            print(f"{self.name}: Mock executing python code (first 50 chars): {code_string[:50]}")
            await asyncio.sleep(0.1)
            return {"stdout": "Mock execution successful", "stderr": "", "exit_code": 0, "status_message": "Completed"}


    async def main_orchestrator_example():
        print("\n--- Initializing Mock Services for JulesCapability ---")
        # Using the more specific MockAIVirtualInputService
        mock_avis = MockAIVirtualInputService()
        mock_sandbox_executor = MockService(name="SandboxExecutor")
        mock_code_model = MockService(name="LightweightCodeModel")
        mock_memory_manager = MockService(name="HAMMemoryManager")
        mock_llm_interface = MockService(name="LLMInterface")
        mock_tool_dispatcher = MockService(name="ToolDispatcher")

        print("\n--- Initializing JulesDevelopmentCapability ---")
        jules_capability = JulesDevelopmentCapability(
            avis_service=mock_avis,
            sandbox_executor=mock_sandbox_executor,
            code_model=mock_code_model,
            memory_manager=mock_memory_manager,
            llm_interface=mock_llm_interface,
            tool_dispatcher=mock_tool_dispatcher
        )

        print("\n--- Angela (Orchestrator) decides to use Jules capability ---")
        task_description_from_user = "Fix a critical typo in the main.py file, function 'calculate_sum'. It currently reads 'smu' instead of 'sum'. Also check utils.py for impacts."
        orchestrator_task_id = "ANGELA-JULES-TASK-008" # Angela assigns an ID

        # Mock loading virtual files into AVIS
        mock_avis.load_virtual_files({
            "src/main.py": "def calculate_smu(a, b):\n  return a + b # Typo here\n\nprint(calculate_smu(1,2))",
            "src/utils.py": "from main import calculate_smu\n\nresult = calculate_smu(5, 5)\nprint(f'Utils result: {result}')",
            "tests/test_main.py": "from main import calculate_smu\n\nassert calculate_smu(10,10) == 20"
        })

        print(f"\n--- Step 1: Angela processes task description using Jules capability ({orchestrator_task_id}) ---")
        # This method is now async in the main class, but the mock LLM call is the async part.
        # For this example, process_development_task_description itself is not async.
        # If it were to call an async LLM method, it would need to be async.
        # Let's make it async to match the potential need for async LLM calls.
        task_context_result = await jules_capability.process_development_task_description(task_description_from_user, task_id=orchestrator_task_id)
        print(f"Jules Capability Task Processing Result: {jules_capability.current_task_context}")


        if task_context_result["status"] == "success":
            # Angela (orchestrator) would look at task_context_result.get('task_context').get('relevant_files_identified')
            # and pass it to analyze_code_context_for_task.
            # For this mock, relevant_files_identified is filled by the mock LLM.
            print(f"\n--- Step 2: Angela triggers code analysis using Jules capability ---")
            analysis_result = await jules_capability.analyze_code_context_for_task()
            print(f"Jules Capability Codebase Analysis Result: {jules_capability.current_task_context.get('code_analysis')}")

            print(f"\n--- Step 3: Angela triggers solution planning using Jules capability ---")
            plan_development_result = await jules_capability.develop_solution_plan()
            # The plan is now more detailed from the mock LLM.
            print(f"Jules Capability Plan Development Result (first 2 steps): {plan_development_result.get('plan')[:2] if plan_development_result.get('plan') else 'No plan'}")

            if jules_capability.current_plan_for_task: # Check attribute directly
                print(f"\n--- Step 4: Angela triggers plan execution using Jules capability ---")
                plan_execution_status = await jules_capability.execute_full_solution_plan()
                print(f"Jules Capability Plan Execution Overall Status: {plan_execution_status}")

                if plan_execution_status["status"] == "success":
                    print(f"\n--- Step 5: Angela triggers output generation using Jules capability ---")
                    # This method might also need to be async if it uses LLM for commit message generation
                    final_output_result = await jules_capability.generate_development_output()
                    print(f"Jules Capability Generated Output: {final_output_result.get('output')}")
                else:
                    print(f"Skipping output generation due to plan execution failure: {plan_execution_status.get('message')}")
            else:
                print("Skipping plan execution and output generation as no plan was developed.")
        else:
            print("Skipping further steps as task description processing failed.")

        current_status_info = jules_capability.get_current_task_status_and_context()
        print(f"\n--- Final Jules Capability Status for Task ({orchestrator_task_id}): ---")
        print(f"  Overall Status: {current_status_info.get('task_context', {}).get('status')}")
        print(f"  Task ID: {current_status_info.get('task_context', {}).get('id')}")
        if current_status_info.get('task_context', {}).get('output'):
            print(f"  Generated Commit Message: {current_status_info['task_context']['output'].get('commit_message')}")
            print(f"  Simulated Git Commands: {current_status_info['task_context']['output'].get('simulated_git_commands')}")

        # Angela decides the task is done with Jules capability for now.
        jules_capability.clear_current_task_context()
        print(f"\n--- Jules Capability Status after clearing: {jules_capability.get_current_task_status_and_context()}")


    asyncio.run(main_orchestrator_example())

"""
Potential future enhancements for JulesDevelopmentCapability:
- Ensure all methods that use `await self.llm_interface` are marked `async`. (Review needed)
- More detailed plan execution logic with actual (non-mocked) service calls to AVIS, SandboxExecutor etc.
- Actual interaction with a virtual file system via AVIS.
- Generation of actual diffs.
- More sophisticated interaction with LLM for code generation/modification.
- Integration with a testing framework via SandboxExecutor, with results fed back to Angela.
"""
