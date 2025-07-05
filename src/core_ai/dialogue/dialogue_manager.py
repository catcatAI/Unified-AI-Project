# Placeholder for Dialogue Manager
# This module will orchestrate the conversation flow, integrate with other AI components,
# and generate responses.

import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid # For test session IDs in __main__
import os # Added for os.path.exists and os.remove in __main__

from core_ai.personality.personality_manager import PersonalityManager
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from services.llm_interface import LLMInterface, LLMInterfaceConfig
from core_ai.emotion_system import EmotionSystem
from core_ai.crisis_system import CrisisSystem
from core_ai.time_system import TimeSystem
from core_ai.formula_engine import FormulaEngine
from tools.tool_dispatcher import ToolDispatcher
from core_ai.learning.self_critique_module import SelfCritiqueModule
from core_ai.learning.fact_extractor_module import FactExtractorModule
from core_ai.learning.learning_manager import LearningManager
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule # Added
import networkx as nx # Added
from shared.types.common_types import FormulaConfigEntry, CritiqueResult, OperationalConfig


class DialogueManager:
    def __init__(self, personality_manager: Optional[PersonalityManager] = None,
                 memory_manager: Optional[HAMMemoryManager] = None,
                 llm_interface: Optional[LLMInterface] = None,
                 emotion_system: Optional[EmotionSystem] = None,
                 crisis_system: Optional[CrisisSystem] = None,
                 time_system: Optional[TimeSystem] = None,
                 formula_engine: Optional[FormulaEngine] = None,
                 tool_dispatcher: Optional[ToolDispatcher] = None,
                 self_critique_module: Optional[SelfCritiqueModule] = None,
                 learning_manager: Optional[LearningManager] = None,
                 content_analyzer: Optional[ContentAnalyzerModule] = None, # Added
                 config: Optional[Dict[str, Any]] = None):

        self.config = config or {}
        op_configs_from_main = self.config.get("operational_configs")

        self.personality_manager = personality_manager if personality_manager else PersonalityManager()
        self.memory_manager = memory_manager if memory_manager else HAMMemoryManager(core_storage_filename="dialogue_context_memory.json")

        self.llm_interface = llm_interface if llm_interface else LLMInterface(operational_config=op_configs_from_main)

        self.formula_engine = formula_engine if formula_engine else FormulaEngine()
        self.tool_dispatcher = tool_dispatcher if tool_dispatcher else ToolDispatcher(llm_interface=self.llm_interface)

        self.fact_extractor_module = FactExtractorModule(
            llm_interface=self.llm_interface
        )
        self.self_critique_module = self_critique_module if self_critique_module else SelfCritiqueModule(
            self.llm_interface,
            operational_config=op_configs_from_main
        )
        self.learning_manager = learning_manager if learning_manager else LearningManager(
            self.memory_manager,
            self.fact_extractor_module,
            operational_config=op_configs_from_main
        )
        self.content_analyzer = content_analyzer if content_analyzer else ContentAnalyzerModule() # Added

        current_pers_profile = self.personality_manager.current_personality
        self.emotion_system = emotion_system if emotion_system else EmotionSystem(personality_profile=current_pers_profile)
        self.crisis_system = crisis_system if crisis_system else CrisisSystem(config=self.config) # Pass full config
        self.time_system = time_system if time_system else TimeSystem(config=self.config) # Pass full config

        self.active_sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_knowledge_graphs: Dict[str, nx.DiGraph] = {} # Added
        self.max_history_per_session: int = self.config.get("max_dialogue_history", 6)

        self.turn_timeout_seconds = self.config.get("operational_configs", {}).get("timeouts", {}).get("dialogue_manager_turn", 120)
        self.min_critique_score_to_store = self.config.get("operational_configs", {}).get("learning_thresholds", {}).get("min_critique_score_to_store", 0.0)


        if not self.personality_manager.current_personality:
            self.personality_manager.load_personality(self.personality_manager.default_profile_name)

        print(f"DialogueManager: Initialized. Turn timeout: {self.turn_timeout_seconds}s. Min critique score to store: {self.min_critique_score_to_store}")

    async def _analyze_and_store_text_context(self, text_content: str, context_id: str):
        """
        Analyzes text content using ContentAnalyzerModule and stores the
        resulting NetworkX graph in session_knowledge_graphs.
        """
        if not self.content_analyzer:
            print("DialogueManager: ContentAnalyzerModule not available.")
            return

        print(f"DialogueManager: Analyzing content for context_id '{context_id}'...")
        try:
            _, nx_graph = self.content_analyzer.analyze_content(text_content)
            self.session_knowledge_graphs[context_id] = nx_graph
            print(f"DialogueManager: Knowledge graph for context_id '{context_id}' updated with {nx_graph.number_of_nodes()} nodes and {nx_graph.number_of_edges()} edges.")
        except Exception as e:
            print(f"DialogueManager: Error during content analysis for context_id '{context_id}': {e}")


    async def get_simple_response(self, user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        print(f"DialogueManager: Received input='{user_input}', session_id='{session_id}', user_id='{user_id}'")
        # TODO: Implement actual overall turn timeout using self.turn_timeout_seconds

        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")
        response_text: str = ""
        critique_result: Optional[CritiqueResult] = None
        user_mem_id: Optional[str] = None

        # Store user input first to get user_mem_id for learning reference
        if self.memory_manager:
            user_metadata = {"speaker": "user", "timestamp": datetime.now().isoformat(), "user_id": user_id, "session_id": session_id}
            user_mem_id = self.memory_manager.store_experience(user_input, "user_dialogue_text", user_metadata) # Removed await

        # Attempt to learn from user input (if not in crisis, and input was stored)
        if user_mem_id and self.learning_manager:
             # Check crisis before learning attempt as well
            crisis_level_for_learning = self.crisis_system.assess_input_for_crisis({"text": user_input})
            if not (crisis_level_for_learning > 0):
                await self.learning_manager.process_and_store_learnables(
                    text=user_input,
                    user_id=user_id,
                    session_id=session_id,
                    source_interaction_ref=user_mem_id
                )

        # Now assess crisis for response generation
        crisis_level = self.crisis_system.assess_input_for_crisis({"text": user_input})

        # POC: Command to trigger content analysis
        analysis_command = "!analyze: "
        if user_input.startswith(analysis_command):
            if session_id:
                text_to_analyze = user_input[len(analysis_command):]
                await self._analyze_and_store_text_context(text_to_analyze, session_id)
                return f"{ai_name}: Context analysis triggered for session '{session_id}'. Knowledge graph updated."
            else:
                return f"{ai_name}: Cannot analyze context without a session_id."

        if crisis_level > 0:
            response_text = self.config.get("crisis_response_text",
                                           f"{ai_name}: I sense this is a sensitive situation. If you need help, please reach out to appropriate support channels.")
            self.emotion_system.update_emotion_based_on_input({"text": user_input})
        else:
            session_history_for_context: List[Dict[str, str]] = []
            prompt_context_for_llm = ""
            if session_id:
                self.active_sessions.setdefault(session_id, [])
                session_history_for_context = self.active_sessions[session_id][:]
                if session_history_for_context:
                    prompt_context_for_llm += "Previous conversation turns:\n"
                    for turn in session_history_for_context:
                        prompt_context_for_llm += f"{turn['speaker'].capitalize()}: {turn['text']}\n"
                    prompt_context_for_llm += "\n"

            if user_id and self.memory_manager:
                learned_facts_records = self.memory_manager.query_core_memory(
                    user_id_for_facts=user_id,
                    data_type_filter="learned_fact_",
                    limit=self.config.get("learned_facts_context_limit", 3),
                    sort_by_confidence=True
                )
                if learned_facts_records:
                    facts_summary_parts = []
                    for record in learned_facts_records:
                        fact_content = record.get("fact_content")
                        if isinstance(fact_content, dict):
                            fact_type = record.get("metadata", {}).get("fact_type", "unknown_fact_type")
                            if fact_type == "user_preference":
                                category = fact_content.get('category', 'preference')
                                preference_value = fact_content.get('preference', fact_content.get('value', 'unknown'))
                                liked = fact_content.get('liked')
                                if liked is True: facts_summary_parts.append(f"User likes {preference_value} (category: {category})")
                                elif liked is False: facts_summary_parts.append(f"User dislikes {preference_value} (category: {category})")
                                else: facts_summary_parts.append(f"User's preference for {category} is {preference_value}")
                            elif fact_type == "user_statement":
                                attribute = fact_content.get('attribute', 'attribute')
                                value = fact_content.get('value', 'unknown')
                                facts_summary_parts.append(f"User stated: {attribute} is {value}")
                            else: facts_summary_parts.append(f"User fact ({fact_type}): {fact_content}")
                    if facts_summary_parts:
                        facts_summary_str = "Context about the user: " + "; ".join(facts_summary_parts) + ".\n"
                        prompt_context_for_llm += facts_summary_str
                        print(f"DialogueManager: Added to LLM context: {facts_summary_str.strip()}")

            # POC: Augment prompt with KG info if available
            if session_id and session_id in self.session_knowledge_graphs:
                nx_graph = self.session_knowledge_graphs[session_id]
                if nx_graph.number_of_nodes() > 0:
                    kg_summary_parts = [f"Analyzed context for this session contains a knowledge graph with {nx_graph.number_of_nodes()} entities and {nx_graph.number_of_edges()} relationships."]

                    # More targeted KG augmentation
                    kg_prompt_addition_parts = []

                    # Simple entity linking: find entities from graph mentioned in user_input
                    mentioned_graph_entities: Dict[str, Dict[Any, Any]] = {} # Store node_id: node_data
                    for node_id, node_data in nx_graph.nodes(data=True):
                        entity_label = node_data.get("label", "")
                        if entity_label and entity_label.lower() in user_input.lower(): # Simple substring check
                            mentioned_graph_entities[node_id] = node_data

                    if mentioned_graph_entities:
                        kg_prompt_addition_parts.append("From the analyzed context related to your query:")
                        for node_id, node_data in list(mentioned_graph_entities.items())[:2]: # Max 2 mentioned entities for brevity
                            entity_label = node_data.get("label", node_id)
                            entity_type = node_data.get("type", "unknown_type")
                            entity_info = f"- Entity '{entity_label}' (type: {entity_type})"

                            # Get direct relationships for this entity
                            rels_found = 0
                            for successor_id in list(nx_graph.successors(node_id))[:2]: # Max 2 outgoing rels
                                edge_data = nx_graph.get_edge_data(node_id, successor_id)
                                target_node_data = nx_graph.nodes[successor_id]
                                target_label = target_node_data.get("label", successor_id)
                                rel_type = edge_data.get("type", "related_to")
                                entity_info += f" --[{rel_type}]--> '{target_label}'"
                                rels_found +=1
                            for predecessor_id in list(nx_graph.predecessors(node_id))[:2]: # Max 2 incoming rels
                                if rels_found >= 2: break # Overall limit for relationships shown per entity
                                edge_data = nx_graph.get_edge_data(predecessor_id, node_id)
                                source_node_data = nx_graph.nodes[predecessor_id]
                                source_label = source_node_data.get("label", predecessor_id)
                                rel_type = edge_data.get("type", "related_to")
                                entity_info += f" <--[{rel_type}]-- '{source_label}'"
                                rels_found +=1
                            kg_prompt_addition_parts.append(entity_info)
                    else: # Fallback to generic summary if no direct mentions
                        kg_prompt_addition_parts.append(f"Analyzed context for this session contains a knowledge graph with {nx_graph.number_of_nodes()} entities and {nx_graph.number_of_edges()} relationships.")
                        entity_labels_sample = [data.get("label", nid) for nid, data in list(nx_graph.nodes(data=True))[:2]]
                        if entity_labels_sample:
                            kg_prompt_addition_parts.append(f"Sample entities include: {', '.join(entity_labels_sample)}.")

                    if kg_prompt_addition_parts:
                        kg_prompt_addition = " ".join(kg_prompt_addition_parts) + "\n"
                        prompt_context_for_llm += kg_prompt_addition
                        print(f"DialogueManager: Added targeted KG info to LLM context: {kg_prompt_addition.strip()}")

            if prompt_context_for_llm:
                 prompt_context_for_llm += "\nCurrent user query:\n"

            self.emotion_system.update_emotion_based_on_input({"text": user_input})
            matched_formula = self.formula_engine.match_input(user_input)

            if matched_formula:
                formula_execution_result = self.formula_engine.execute_formula(matched_formula)
                action_name = formula_execution_result.get("action_name", "unknown_action")
                action_params = formula_execution_result.get("action_params", {})

                if action_name == "dispatch_tool":
                    tool_name = action_params.get("tool_name")
                    tool_query = action_params.get("tool_query") # This might be a template

                    # Basic template filling for tool_query using action_params for now
                    # A more robust solution would involve regex capture groups from formula conditions.
                    if isinstance(tool_query, str):
                        try:
                            tool_query = tool_query.format(**action_params) # Fill if template
                        except KeyError:
                            print(f"DialogueManager: Warning - could not format tool_query template for formula {matched_formula.get('name')}")

                    if tool_name and tool_query:
                        print(f"DialogueManager: Formula '{matched_formula.get('name')}' dispatching to tool '{tool_name}' with query '{tool_query}'")
                        tool_result = self.tool_dispatcher.dispatch(query=str(tool_query), explicit_tool_name=tool_name)
                        response_text = f"{ai_name}: {tool_result}" if tool_result is not None else f"{ai_name}: I tried to use a tool, but it didn't work as expected."
                    else:
                        response_text = f"{ai_name}: Formula '{matched_formula.get('name')}' tried to dispatch a tool, but tool_name or tool_query was missing/invalid."
                else: # Not a dispatch_tool action
                    response_template = matched_formula.get("response_template")
                    if response_template:
                        try:
                            format_kwargs = {"ai_name": ai_name, **action_params}
                            response_text = response_template.format(**format_kwargs)
                        except KeyError as e:
                            response_text = f"{ai_name}: Formula '{matched_formula.get('name')}' triggered action '{action_name}' (template error: {e})."
                        except Exception as e:
                            response_text = f"{ai_name}: Formula '{matched_formula.get('name')}' triggered action '{action_name}' (general template error)."
                    elif action_name:
                        response_text = f"{ai_name}: Action '{action_name}' triggered."
                    else:
                        response_text = f"{ai_name}: I recognized pattern: '{matched_formula.get('name')}'."
            else: # No formula matched, proceed to LLM
                full_prompt_for_llm = f"{prompt_context_for_llm}{user_input}"
                llm_response_text = self.llm_interface.generate_response(prompt=full_prompt_for_llm) # Removed await
                base_response = f"{ai_name}: {llm_response_text}"
                response_text = base_response

            emotion_expression = self.emotion_system.get_current_emotion_expression()
            emotion_suffix = emotion_expression.get("text_ending", "")
            response_text = f"{response_text}{emotion_suffix}" if emotion_suffix else response_text

            critique_result = self.self_critique_module.critique_interaction(
                user_input, response_text, session_history_for_context
            )
            if critique_result:
                print(f"DialogueManager: Self-critique result: Score={critique_result['score']}, Reason='{critique_result.get('reason', '')}'")
            else:
                print("DialogueManager: Self-critique module did not return a result.")

        # --- Memory Storage for AI response ---
        ai_metadata: Dict[str, Any] = {"speaker": "ai", "timestamp": datetime.now().isoformat(), "user_id": user_id, "session_id": session_id}
        if critique_result:
            min_critique_score = self.config.get("operational_configs", {}).get("learning_thresholds", {}).get("min_critique_score_to_store", 0.0)
            if critique_result["score"] >= min_critique_score:
                ai_metadata["critique"] = critique_result
            else:
                print(f"DialogueManager: Critique score {critique_result['score']} is below threshold {min_critique_score}. Not storing critique in HAM.")

        if self.memory_manager and user_mem_id :
            ai_metadata["user_input_ref"] = user_mem_id
            self.memory_manager.store_experience(response_text, "ai_dialogue_text", ai_metadata) # Removed await

        if session_id:
            self.active_sessions[session_id].append({"speaker": "user", "text": user_input})
            self.active_sessions[session_id].append({"speaker": "ai", "text": response_text})
            if len(self.active_sessions[session_id]) > self.max_history_per_session:
                self.active_sessions[session_id] = self.active_sessions[session_id][-self.max_history_per_session:]

        return response_text

    async def start_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        print(f"DialogueManager: New session started for user '{user_id if user_id else 'anonymous'}', session_id: {session_id}.")
        if session_id:
            self.active_sessions[session_id] = []
        base_prompt = self.personality_manager.get_initial_prompt()
        time_segment = self.time_system.get_time_of_day_segment()
        time_specific_greeting_prefix = ""
        if time_segment == "morning": time_specific_greeting_prefix = "Good morning!"
        elif time_segment == "afternoon": time_specific_greeting_prefix = "Good afternoon!"
        elif time_segment == "evening": time_specific_greeting_prefix = "Good evening!"
        elif time_segment == "night": time_specific_greeting_prefix = "Hello,"
        return f"{time_specific_greeting_prefix} {base_prompt}" if time_specific_greeting_prefix else base_prompt

if __name__ == '__main__':
    import asyncio
    import json
    from core_ai.personality.personality_manager import PersonalityManager
    from tools.tool_dispatcher import ToolDispatcher
    from services.llm_interface import LLMInterface, LLMInterfaceConfig
    from core_ai.learning.self_critique_module import SelfCritiqueModule
    from core_ai.learning.fact_extractor_module import FactExtractorModule
    from core_ai.learning.learning_manager import LearningManager
    from shared.types.common_types import OperationalConfig

    # Using the actual LLMInterface for Ollama testing, no longer patching for this specific test run.
    # PatchedLLMInterfaceForDMTest can be kept for other tests that need specific mock responses.
    # class PatchedLLMInterfaceForDMTest(LLMInterface):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self.last_prompt_for_test: Optional[str] = None
    #
    #     async def generate_response(self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None, request_timeout: Optional[int] = None) -> str:
    #         # This entire method body would be the mock logic if the class were active.
    #         # For now, it's fully commented out as we use the real LLMInterface.
    #         # self.last_prompt_for_test = prompt
    #         # prompt_lower = prompt.lower()
    #         # print(f"DEBUG: PatchedLLMInterface received prompt for model '{model_name}':\n{prompt}\n--------------------")
    #         # ... (rest of the mock logic) ...
    #         return f"This would be a mock response if PatchedLLMInterfaceForDMTest was active."

    async def main_dm_test():
        test_op_configs_dict: OperationalConfig = { # type: ignore
            "timeouts": {
                "llm_general_request": 10, "llm_critique_request": 8, "llm_fact_extraction_request": 8,
                "dialogue_manager_turn": 30,
                "llm_ollama_request": 60, # Added for Ollama
                "llm_ollama_list_models_request": 10 # Added for Ollama
            },
            "learning_thresholds": {"min_fact_confidence_to_store": 0.7, "min_critique_score_to_store": 0.25}
        }

        # Configure to use Ollama
        # IMPORTANT: User needs to have Ollama running and the specified model downloaded.
        ollama_llm_config_for_dm_test: LLMInterfaceConfig = { # type: ignore
            "default_provider": "ollama",
            "default_model": "nous-hermes2:latest", # Replace if you use a different default model for Ollama
            "providers": {
                "ollama": {"base_url": "http://localhost:11434"}
            },
            "default_generation_params": {"temperature": 0.7},
            "operational_configs": test_op_configs_dict # Pass operational configs here
        }

        # Instantiate the actual LLMInterface with Ollama config
        # All tests will now attempt to use Ollama, so mock responses for critique/fact extraction won't trigger
        # This means those specific assertions might fail if Ollama doesn't produce the exact mock text.
        # For this step, we are primarily testing if DialogueManager can *use* the Ollama-configured LLMInterface.
        actual_llm_interface_for_dm = LLMInterface(config=ollama_llm_config_for_dm_test)


        pm = PersonalityManager()
        test_ham_file = f"dialogue_manager_test_ham_{uuid.uuid4().hex}.json"
        memory_manager_inst = HAMMemoryManager(core_storage_filename=test_ham_file)

        dm = DialogueManager(
            personality_manager=pm,
            memory_manager=memory_manager_inst,
            llm_interface=actual_llm_interface_for_dm, # Use the Ollama-configured LLMInterface
            config={"operational_configs": test_op_configs_dict}
        )

        print(f"\n--- Test: Basic Interaction & Formula (Ollama LLM where applicable) ---")
        test_session_id_1 = "session_basic_001"
        test_user_id_1 = "user_basic_001"
        print(await dm.start_session(user_id=test_user_id_1, session_id=test_session_id_1))

        user_msg = "Hello Miko" # Should trigger formula
        ai_reply = await dm.get_simple_response(user_msg, session_id=test_session_id_1, user_id=test_user_id_1)
        print(f"User: {user_msg}\nAI: {ai_reply}")
        assert "Hello! I am Miko (Base). How can I help you today?" in ai_reply # Updated to include (Base)

        print("\n--- Test: Learning and Using Learned Facts ---")
        test_session_id_2 = "session_learning_002"
        test_user_id_2 = "user_learner_002"
        print(await dm.start_session(user_id=test_user_id_2, session_id=test_session_id_2))

        user_q1 = "My favorite animal is a dog."
        ai_r1 = await dm.get_simple_response(user_q1, session_id=test_session_id_2, user_id=test_user_id_2)
        print(f"User: {user_q1}\nAI: {ai_r1}")
        # HAM should now contain "user likes dogs" for user_learner_002

        user_q2 = "Should I get a cat or a dog?"
        ai_r2 = await dm.get_simple_response(user_q2, session_id=test_session_id_2, user_id=test_user_id_2)
        print(f"User: {user_q2}\nAI: {ai_r2}")
        assert "dogs" in ai_r2.lower() # Check if the AI's response considers the learned fact

        user_q3 = "What is my favorite animal?"
        ai_r3 = await dm.get_simple_response(user_q3, session_id=test_session_id_2, user_id=test_user_id_2)
        print(f"User: {user_q3}\nAI: {ai_r3}")
        assert "dog" in ai_r3.lower()


        print("\n--- Test: Tool Dispatch via Formula ---")
        user_msg_tool = "calculate for me 2 plus 2" # Assuming a formula exists for this
        # We need to ensure formula `formula_trigger_calculation` is updated or a new one exists
        # For now, let's use the existing "calculate for me" which has a fixed "25 * 4" query
        user_msg_tool_formula = "calculate for me"
        ai_reply_tool = await dm.get_simple_response(user_msg_tool_formula, session_id=test_session_id_1, user_id=test_user_id_1)
        print(f"User: '{user_msg_tool_formula}'\nAI: {ai_reply_tool}")
        assert "Result: 100" in ai_reply_tool

        print("\n--- Test: Content Analysis and KG Prompt Augmentation ---")
        test_session_id_3 = "session_kg_analysis_003"
        test_user_id_3 = "user_analyzer_003"
        print(await dm.start_session(user_id=test_user_id_3, session_id=test_session_id_3))

        analyze_cmd = "!analyze: Google is a company. Sundar Pichai is the CEO of Google. Google is based in Mountain View."
        analyze_reply = await dm.get_simple_response(analyze_cmd, session_id=test_session_id_3, user_id=test_user_id_3)
        print(f"User: {analyze_cmd}\nAI: {analyze_reply}")
        assert "Context analysis triggered" in analyze_reply
        assert test_session_id_3 in dm.session_knowledge_graphs # Check if KG was stored

        # Ensure the graph has content before checking the next reply
        if test_session_id_3 in dm.session_knowledge_graphs:
            nx_g_session3 = dm.session_knowledge_graphs[test_session_id_3]
            print(f"Session 3 KG: {nx_g_session3.number_of_nodes()} nodes, {nx_g_session3.number_of_edges()} edges.")
            # for node, data in nx_g_session3.nodes(data=True): print(f"  Node: {node}, Data: {data}") # For debugging
            # for u,v,data in nx_g_session3.edges(data=True): print(f"  Edge: {u} -> {v}, Data: {data}") # For debugging


        follow_up_q = "Tell me about Google from this session." # Changed to be more specific
        follow_up_r = await dm.get_simple_response(follow_up_q, session_id=test_session_id_3, user_id=test_user_id_3)
        print(f"User: {follow_up_q}\nAI: {follow_up_r}")
        # Check if patched LLM used the *specific* augmented prompt
        # The following assertions will likely fail if using a real Ollama model
        # print(f"DEBUG: Last prompt sent to LLM for KG test: {dm.llm_interface.last_prompt_for_test if hasattr(dm.llm_interface, 'last_prompt_for_test') else 'N/A'}")

        print("\n--- Test: New CONCEPT Node and 'is_a' relationship via !analyze ---")
        test_session_id_4 = "session_concept_test_004"
        test_user_id_4 = "user_concept_tester_004"
        print(await dm.start_session(user_id=test_user_id_4, session_id=test_session_id_4))

        analyze_cmd_concepts = "!analyze: AlphaOrg is a new company. BetaCorp's new CEO is a person."
        analyze_reply_concepts = await dm.get_simple_response(analyze_cmd_concepts, session_id=test_session_id_4, user_id=test_user_id_4)
        print(f"User: {analyze_cmd_concepts}\nAI: {analyze_reply_concepts}")

        if test_session_id_4 in dm.session_knowledge_graphs:
            kg_concept_test = dm.session_knowledge_graphs[test_session_id_4]
            print(f"KG for session '{test_session_id_4}':")
            print("  Nodes:")
            for node_id, node_data in kg_concept_test.nodes(data=True):
                print(f"    - {node_id}: {node_data}")
            print("  Edges:")
            for u, v, edge_data in kg_concept_test.edges(data=True):
                u_label = kg_concept_test.nodes[u].get('label', u)
                v_label = kg_concept_test.nodes[v].get('label', v)
                print(f"    - {u_label} --[{edge_data.get('type', 'related_to')}]--> {v_label} (Data: {edge_data})")
        else:
            print(f"No knowledge graph found for session_id '{test_session_id_4}' after !analyze command.")


        print("\nDialogueManager tests finished (using Ollama where LLM is involved).")

        # Clean up test HAM file
        if os.path.exists(memory_manager_inst.core_storage_filepath):
            try:
                os.remove(memory_manager_inst.core_storage_filepath)
                print(f"Cleaned up {memory_manager_inst.core_storage_filepath}")
            except Exception as e:
                print(f"Error cleaning up test HAM file: {e}")

    asyncio.run(main_dm_test())
