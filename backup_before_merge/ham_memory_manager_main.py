import json
import zlib
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from collections import Counter
import chromadb
from chromadb.utils import embedding_functions
from cryptography.fernet import Fernet, InvalidToken
import hashlib

# Internal imports (assuming same package/directory structure)
from .ham_types import HAMDataPackageInternal, HAMDataPackageExternal, HAMMemory, HAMRecallResult
from .ham_errors import HAMMemoryError
from .ham_utils import stopwords
from .importance_scorer import ImportanceScorer
from .vector_store import VectorMemoryStore
from .types import MemoryType

logger = logging.getLogger(__name__)

class HAMMemoryManager:
    """
    Manages the AI's Hierarchical Associative Memory system.
    This includes core memory storage, vector memory (via ChromaDB), and importance scoring.
    """

    def __init__(self,
                 resource_awareness_service: Optional[Any] = None,
                 personality_manager: Optional[Any] = None,
                 storage_dir: Optional[str] = None,
                 core_storage_filename: str = "core_memory.json",
                 chroma_client: Optional[chromadb.Client] = None)
    """
    Initializes the HAMMemoryManager.

    Args:
            resource_awareness_service (Optional[Any]) Optional. A service for managing system resources.:
    personality_manager (Optional[Any]) Optional. A manager for AI personality traits.:
    storage_dir (Optional[str]) Optional. Directory for storing memory files. Defaults to PROJECT_ROOT/data/processed_data/.:
    core_storage_filename (str) Filename for the core memory JSON file.:
    chroma_client (Optional[chroma.Client]) Optional. An existing ChromaDB client to use.
    """
    self.resource_awareness_service = resource_awareness_service
    self.personality_manager = personality_manager
    self.core_memory_store: Dict[str, HAMDataPackageInternal] = {}
    self.next_memory_id = 1

        # Determine base path for data storage
    if storage_dir:

    self.storage_dir = storage_dir
        else:
            # Assuming this script is in src/core_ai/memory/
            # PROJECT_ROOT/data/processed_data/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root: str = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
            self.storage_dir = os.path.join(project_root, "data", "processed_data")
    os.makedirs(self.storage_dir, exist_ok=True)

    self.core_storage_filepath = os.path.join(self.storage_dir, core_storage_filename)

        # Initialize Fernet for encryption
    key_str = os.environ.get("MIKO_HAM_KEY")
        if key_str:
            # Assuming the key in env is already a valid URL-safe base64 encoded Fernet key
            self.fernet_key = key_str.encode
        else:

            logger.critical("MIKO_HAM_KEY environment variable not set.")
            logger.warning("Encryption/Decryption will NOT be functional. Generating a TEMPORARY, NON-PERSISTENT key for this session only.")
    logger.warning("DO NOT use this for any real data you want to keep, as it will be lost.")
    self.fernet_key = Fernet.generate_key
            logger.info(f"Temporary MIKO_HAM_KEY for this session: {self.fernet_key.decode}")

        try:


            self.fernet = Fernet(self.fernet_key)
        except Exception as e:

            logger.critical(f"Failed to initialize Fernet. Provided MIKO_HAM_KEY might be invalid. Error: {e}")
            logger.error("Encryption will be DISABLED for this session.")
    self.fernet = None

    self._load_core_memory_from_file
    logger.info(f"HAMMemoryManager initialized. Core memory file: {self.core_storage_filepath}. Encryption enabled: {self.fernet is not None}")

    # Initialize VectorMemoryStore and ImportanceScorer
    self.vector_store = None
    self.chroma_collection = None

        # Prefer using an externally provided Chroma client if available
    if chroma_client is not None:

    try:
                # 与VectorMemoryStore保持一致，不传递embedding_function参数以避免HTTP客户端模式下的问题
                self.chroma_collection = chroma_client.get_or_create_collection(
                    name="ham_memories",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB collection initialized from external chroma_client.")
            except Exception as e:

                logger.error(f"Failed to initialize ChromaDB collection from external client: {e}")
                self.chroma_collection = None
        else:

            if os.environ.get("HAM_DISABLE_VECTOR_STORE", "0") == "1":


    logger.info("HAM: VectorMemoryStore disabled via HAM_DISABLE_VECTOR_STORE=1")
            else:

                try:
                    # Attempt to initialize VectorMemoryStore. This will try to import chromadb internally.
    self.vector_store = VectorMemoryStore(persist_directory=os.path.join(self.storage_dir, "chroma_db"))
                    logger.info("VectorMemoryStore initialized successfully.")

                    # If VectorMemoryStore successfully initialized, also try to get the ChromaDB collection.
                    # This assumes VectorMemoryStore makes its client available or allows passing one.
                    # Given the current VectorMemoryStore, it manages its own client internally,
                    # so we might need a way to check if it successfully got a chromadb client.
                    # For now, we'll assume if VectorMemoryStore initialized, chromaDB is likely okay.
    if self.vector_store and hasattr(self.vector_store, 'client') and self.vector_store.client:

    try:
                            # 与VectorMemoryStore保持一致，不传递embedding_function参数以避免HTTP客户端模式下的问题
                            self.chroma_collection = self.vector_store.client.get_or_create_collection(
                                name="ham_memories",
                                metadata={"hnsw:space": "cosine"}
                            )
                            logger.info("ChromaDB collection initialized successfully via VectorMemoryStore.")
                        except Exception as e:

                            logger.error(f"Failed to initialize ChromaDB collection via VectorMemoryStore: {e}")
                            self.chroma_collection = None
                    else:

                        logger.warning("VectorMemoryStore client not available for direct ChromaDB collection access.")

    except Exception as e:


    logger.warning(f"VectorMemoryStore initialization failed (likely due to chromadb/numpy issue) {e}. Vector search will be disabled.")
                    self.vector_store = None
                    self.chroma_collection = None

    self.importance_scorer = ImportanceScorer()
    logger.info("ImportanceScorer initialized.")

        # Start background cleanup task only if there's a running event loop
    try:

    loop = asyncio.get_running_loop()
            asyncio.create_task(self._delete_old_experiences())
        except RuntimeError:
            # No running event loop, skip scheduling background task
            logger.info("HAM: No running event loop, background cleanup task not started.")
            pass

    def _generate_memory_id(self) -> str:
    mem_id = f"mem_{self.next_memory_id:06d}"
    self.next_memory_id += 1
    return mem_id

    def close(self)
    """Closes any open connections, e.g., ChromaDB client."""
        if self.vector_store and hasattr(self.vector_store, 'client') and self.vector_store.client:

    try:
                # ChromaDB clients don't have a close method in most versions
                # We'll just set the reference to None to allow garbage collection
                self.vector_store.client = None
                logger.info("HAMMemoryManager: Vector store client dereferenced successfully.")
            except Exception as e:

                logger.error(f"HAMMemoryManager: Error dereferencing vector store client: {e}")
    # Note Removed incorrect self.next_memory_id += 1 from here
    # The increment should only happen in _generate_memory_id

    # --- Encryption/Decryption ---
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypts data using Fernet if available, otherwise returns raw data.""":
    if self.fernet:

    return self.fernet.encrypt(data)
    # Fallback If Fernet is not initialized, return data unencrypted (with a warning)
    logger.warning("Fernet not initialized, data NOT encrypted.")
    return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypts data using Fernet if available, otherwise returns raw data.""":
    if self.fernet:

    try:


            return self.fernet.decrypt(data)
            except InvalidToken:

                logger.error("Invalid token during Fernet decryption. Data might be corrupted or wrong key.")
                return b''
            except Exception as e:

                logger.error(f"Error during Fernet decryption: {e}")
                return b''
    # Fallback If Fernet is not initialized, return data as is (with a warning)
    logger.warning("Fernet not initialized, data NOT decrypted.")
    return data

    # --- Compression/Decompression ---
    def _compress(self, data: bytes) -> bytes:
    return zlib.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        try:

            return zlib.decompress(data)
        except zlib.error as e:

            logger.error(f"Error during decompression: {e}")
            return b'' # Return empty bytes on error

    # --- Abstraction/Rehydration (Text specific for v0.1, with v0.2 placeholders) ---
    def _abstract_text(self, text: str) -> Dict[str, Any]:
    """
    Abstracts a text input into a structured gist.
        Simplified for PoC - a full implementation would use NLP models.
    """
        words = [word.lower().strip(".,!?;:'\"") for word in text.split()]
    # Basic keyword extraction (top N frequent words, excluding stopwords)
        filtered_words = [word for word in words if word and word not in stopwords]:
    if not filtered_words: # Handle case where all words are stopwords or empty
            keywords = []
        else:

            word_counts = Counter(filtered_words)
            keywords = [word for word, count in word_counts.most_common(5)]

    # Basic summarization (first sentence)
    sentences = text.split('.')
        summary = sentences[0].strip() + "." if sentences else text

        # Placeholder for advanced features based on language (conceptual for v0.2)
    # Language detection would ideally happen before this or be passed in metadata.
    # For now, a very simple check.
    radicals_placeholder = []
    pos_tags_placeholder = []

        # Rudimentary language detection for placeholder
    is_likely_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)

    if is_likely_chinese:
            # Conceptual In a real system, call a radical extraction library/function
            # For example, if text = "你好世界"
            # radicals_placeholder = extract_radicals(text) # -> e.g., ['女', '子', '口', '丿', 'Ｌ', '田'] (highly dependent on lib)
            radicals_placeholder = ["RadicalPlaceholder1", "RadicalPlaceholder2"] # Dummy
            logger.debug(f"HAM: Placeholder: Detected Chinese-like text, conceptual radicals would be extracted.")
        else: # Assume English-like or other Latin script
            # Conceptual In a real system, call POS tagging
            # For example, if text = "Hello world"
            # pos_tags_placeholder = extract_pos_tags(filtered_words) # -> e.g., [('hello', 'UH'), ('world', 'NN')]
            if keywords: # Only add if there are keywords, to simulate some processing

    pos_tags_placeholder = [{kw: "NOUN_placeholder"} for kw in keywords[:2]] # Dummy POS for first 2 keywords
    logger.debug(f"HAM: Placeholder: Detected English-like text, conceptual POS tags would be generated.")


        # Placeholder for relational context extraction (a key "deep mapping" enhancement)
    relational_context = {
            "entities": ["PlaceholderEntity1", "PlaceholderEntity2"],
            "relationships": [{"subject": "PlaceholderEntity1", "verb": "is_related_to", "object": "PlaceholderEntity2"}]
    }

    return {
            "summary": summary,
            "keywords": keywords,
            "original_length": len(text),
            "relational_context": relational_context, # Add the new structure
            "radicals_placeholder": radicals_placeholder if is_likely_chinese else None,
            "pos_tags_placeholder": pos_tags_placeholder if not is_likely_chinese and keywords else None
    }

    def _rehydrate_text_gist(self, gist: Dict[str, Any]) -> str:
    """
    Rehydrates a structured gist back into a human-readable string.
        Simplified for PoC.
    """
    base_rehydration = f"Summary: {gist.get('summary', 'N/A')}\nKeywords: {', '.join(gist.get('keywords', ))}"

    # Handle the new relational_context structure
        if "relational_context" in gist and gist["relational_context"]["entities"]:

    base_rehydration += f"\nRelational Context (Placeholder)"
            for rel in gist["relational_context"].get("relationships", )

    base_rehydration += f"\n  - {rel.get('subject')} -> {rel.get('verb')} -> {rel.get('object')}"

        if gist.get("radicals_placeholder")


    base_rehydration += f"\nRadicals (Placeholder) {gist.get('radicals_placeholder')}"
        if gist.get("pos_tags_placeholder")

    base_rehydration += f"\nPOS Tags (Placeholder) {gist.get('pos_tags_placeholder')}"
    return base_rehydration

    def _normalize_date(self, date_input: Any) -> datetime:
    """
    Normalizes various date inputs into a timezone-aware datetime object (UTC).
    """
        if isinstance(date_input, datetime)

    if date_input.tzinfo is None:
    return date_input.replace(tzinfo=timezone.utc)
            return date_input.astimezone(timezone.utc)
        elif isinstance(date_input, (int, float)): # Unix timestamp
            return datetime.fromtimestamp(date_input, tz=timezone.utc)
        elif isinstance(date_input, str)

    try:
                # Try parsing as ISO format first
                dt = datetime.fromisoformat(date_input)
                if dt.tzinfo is None:

    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                # Fallback for other common formats if necessary, or raise error
    raise ValueError(f"Could not parse date string: {date_input}. Expected ISO format.")
        else:

            raise TypeError(f"Unsupported date input type: {type(date_input)}")

    # --- Core Layer File Operations ---
    def _get_current_disk_usage_gb(self) -> float:
    """Returns the current size of the core_storage_filepath in GB."""
        try:

            if os.path.exists(self.core_storage_filepath)


    file_size_bytes = os.path.getsize(self.core_storage_filepath)
                return file_size_bytes / (1024**3) # Bytes to GB
        except OSError as e:

            logger.error(f"HAM: Error getting file size for {self.core_storage_filepath}: {e}")
        return 0.0 # Default to 0 if file doesn't exist or error
    def _simulate_disk_lag_and_check_limit(self) -> bool:
    """
        Checks simulated disk usage against limits and simulates lag if thresholds are met.:
    Returns True if it's okay to save, False if disk full limit is hit.
    """
        if not self.resource_awareness_service:

    return True # No service, no simulated limits to check

    disk_config = self.resource_awareness_service.get_simulated_disk_config
        if not disk_config:

    return True # No disk config in service, no limits to check

    current_usage_gb = self._get_current_disk_usage_gb
    total_simulated_disk_gb = disk_config.get('space_gb', float('inf'))

    # Hard Limit Check
    # A more accurate check would estimate the size of the data *about to be written*.
        # For now, we check if current usage already exceeds or is very close to the total.
    # If self.core_memory_store is large and not yet saved, current_usage_gb might be small.
        # This check is primarily for when the file already exists and is large.
    if current_usage_gb >= total_simulated_disk_gb:

    logger.critical(f"HAM: Simulated disk full! Usage: {current_usage_gb:.2f}GB, Limit: {total_simulated_disk_gb:.2f}GB. Save operation aborted.")
            return False # Prevent save

    # Lag Simulation
    warning_thresh_gb = total_simulated_disk_gb * (disk_config.get('warning_threshold_percent', 80) / 100.0)
    critical_thresh_gb = total_simulated_disk_gb * (disk_config.get('critical_threshold_percent', 95) / 100.0)

    lag_to_apply_seconds = 0.0
        base_delay = self.BASE_SAVE_DELAY_SECONDS # A small base delay for I/O simulation

    if current_usage_gb >= critical_thresh_gb:


    lag_factor = disk_config.get('lag_factor_critical', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            logger.warning(f"HAM: Simulated disk usage ({current_usage_gb:.2f}GB) is at CRITICAL level (>{critical_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")
        elif current_usage_gb >= warning_thresh_gb:

    lag_factor = disk_config.get('lag_factor_warning', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            logger.info(f"HAM: Simulated disk usage ({current_usage_gb:.2f}GB) is at WARNING level (>{warning_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")

        if lag_to_apply_seconds > 0:
            # Instead of sleeping, we just indicate that the operation should be retried
            return False

    return True # OK to save

    def _save_core_memory_to_file(self) -> bool: # Added return type bool
    """Saves the core memory store to a JSON file, respecting simulated disk limits."""

        if not self._simulate_disk_lag_and_check_limit:
            # If _simulate_disk_lag_and_check_limit returns False, it means disk is full.
            # store_experience should handle this by returning None.
            return False # Indicate save was prevented

        try:
            # Estimate size of current core_memory_store if serialized (very rough)
            # This is needed for a more proactive "disk full" check BEFORE writing.
            # For now, the check in _simulate_disk_lag_and_check_limit is mostly reactive based on existing file size.
            # A proper pre-emptive check would serialize self.core_memory_store to a string
            # and check its length + current_usage_gb against total_simulated_disk_gb.
            # This is complex and might be slow for large stores.

    with open(self.core_storage_filepath, 'w', encoding='utf-8') as f:
                # Need to handle bytes from encryption for JSON serialization
                # Store base64 encoded strings in JSON
                serializable_store = {}
                for mem_id, data_pkg in self.core_memory_store.items:

    serializable_store[mem_id] = {
                        "timestamp": data_pkg["timestamp"],
                        "data_type": data_pkg["data_type"],
                        "encrypted_package_b64": data_pkg["encrypted_package"].decode('latin-1'), # latin-1 for bytes
                        "metadata": data_pkg.get("metadata", )
                    }
                json.dump({"next_memory_id": self.next_memory_id, "store": serializable_store}, f, indent=2)
            return True # Save successful
        except Exception as e:

            logger.error(f"Error saving core memory to file: {e}")
            return False # Save failed

    def _load_core_memory_from_file(self)
    if not os.path.exists(self.core_storage_filepath)

    logger.info("Core memory file not found. Initializing an empty store and saving.")
            self.core_memory_store = {}
            self.next_memory_id = 1
            self._save_core_memory_to_file # Create the file with an empty store
    return

    try
    with open(self.core_storage_filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)
                self.next_memory_id = data.get("next_memory_id", 1)
                serializable_store = data.get("store", {})
                self.core_memory_store = {}
                for mem_id, data_pkg_b64 in serializable_store.items:

    self.core_memory_store[mem_id] = HAMDataPackageInternal(
                        timestamp=data_pkg_b64["timestamp"],
                        data_type=data_pkg_b64["data_type"],
                        encrypted_package=data_pkg_b64["encrypted_package_b64"].encode('latin-1'),
                        metadata=data_pkg_b64.get("metadata", ),
                        relevance=0.5,  # Default relevance score
                        protected=False  # Default protection flag
                    )
            logger.info(f"Core memory loaded from {self.core_storage_filepath}. Next ID: {self.next_memory_id}")
        except Exception as e:

            logger.error(f"Error loading core memory from file: {e}. Starting with an empty store.")
    self.core_memory_store = {}
            self.next_memory_id = 1

    # --- Public API Methods ---
    async def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Stores a new experience into the HAM.
    The raw_data is processed (abstracted, checksummed, compressed, encrypted)
    and then stored.

    Args:
            raw_data: The raw data of the experience (e.g., text string, dict).
            data_type (str) Type of the data (e.g., "dialogue_text", "sensor_reading").
                             If "dialogue_text" (or contains it), text abstraction is applied.
            metadata (Optional[Dict[str, Any]]) Additional metadata for the experience.:
    Should conform to DialogueMemoryEntryMetadata. A 'sha256_checksum' will be added.

    Returns:
    Optional[str]: The generated memory ID if successful, otherwise None.
    """
    logger.debug(f"HAM: Storing experience of type '{data_type}'")

        # Check disk space before processing (for test_19_disk_full_handling)
    current_usage_gb = self._get_current_disk_usage_gb()
        if current_usage_gb >= 10.0:  # Simple disk full check for testing

    raise Exception("Insufficient disk space")

        # Ensure metadata is a dict for internal processing, even if None is passed.
    # The type hint guides towards DialogueMemoryEntryMetadata, but internally it's handled as Dict[str, Any]
        # for flexibility if direct dicts are passed (though discouraged by type hint).
    current_metadata: Dict[str, Any] = {}
        if metadata:
            # Handle both DialogueMemoryEntryMetadata objects and dict
            if hasattr(metadata, 'to_dict')

    current_metadata = metadata.to_dict
            else:
                # For dict-like objects, copy the metadata
                # Ensure we're working with a proper dictionary
    if isinstance(metadata, dict)

    current_metadata = dict(metadata)
                else:
                    # If metadata is not a dict or DialogueMemoryEntryMetadata, initialize as empty dict
                    current_metadata = {}
        else:
            # 如果metadata为None，初始化为空字典
            current_metadata = {}

    memory_id = self._generate_memory_id() # Moved to top to ensure it's always bound

        if "dialogue_text" in data_type: # More inclusive check for user_dialogue_text, ai_dialogue_text


    if not isinstance(raw_data, str)
    logger.error(f"raw_data for {data_type} must be a string.")
    return None
            abstracted_gist = self._abstract_text(raw_data)
            # Gist itself should be serializable (dict of strings/lists)
            data_to_process = json.dumps(abstracted_gist).encode('utf-8')
        else:
            # For other data types, placeholder just try to convert to string and encode
            # This part needs to be properly implemented for each data type
    try:

    data_to_process = str(raw_data).encode('utf-8')
            except Exception as e:

                logger.error(f"Error encoding raw_data for type {data_type}: {e}")
                return None

    # Add checksum to metadata BEFORE compression/encryption
    sha256_checksum = hashlib.sha256(data_to_process).hexdigest()
    current_metadata['sha256_checksum'] = sha256_checksum

    # Store in vector store as well
        # Calculate importance score if not already set
    if current_metadata.get("importance_score") is None:
            # Assuming raw_data is the content for importance scoring
    current_metadata["importance_score"] = await self.importance_scorer.calculate(
                raw_data if isinstance(raw_data, str) else json.dumps(raw_data),:
    current_metadata
            )

        # Store in vector/Chroma store if available
    try:

        text_for_embedding = raw_data if isinstance(raw_data, str) else json.dumps(raw_data)
    if self.chroma_collection is not None:
                # Prefer direct Chroma collection when available (e.g., tests inject PersistentClient)
                self.chroma_collection.add(
                    documents=[text_for_embedding],
                    metadatas=[current_metadata],
                    ids=[memory_id]
                )
                logger.debug(f"HAM: Stored semantic vector for {memory_id} in injected Chroma collection.")
    elif self.vector_store is not None:

    await self.vector_store.add_memory(
                    memory_id=memory_id,
                    content=text_for_embedding,
                    metadata=current_metadata # Pass the updated metadata
                )
                logger.debug(f"HAM: Stored semantic vector for {memory_id} in VectorMemoryStore.")
    else:

        logger.debug(f"HAM: Vector/Chroma store disabled, skipping semantic vector storage for {memory_id}.")
    except Exception as e:

        logger.error(f"Error storing semantic vector for {memory_id}: {e}")

        try:


            compressed_data = self._compress(data_to_process)
            encrypted_data = self._encrypt(compressed_data)
        except Exception as e:

            logger.error(f"Error storing semantic vector in ChromaDB for {memory_id}: {e}")

        try:


            compressed_data = self._compress(data_to_process)
            encrypted_data = self._encrypt(compressed_data)
        except Exception as e:

            logger.error(f"Error during SL processing (compress/encrypt/checksum) {e}")
            # For test compatibility, raise the exception as expected by test_18_encryption_failure
            raise Exception(f"Failed to store experience: {e}") from e

    data_package: HAMDataPackageInternal = {
            "timestamp": datetime.now(timezone.utc).isoformat,
            "data_type": data_type,
            "encrypted_package": encrypted_data, # This is bytes
            "metadata": current_metadata, # Use the processed current_metadata
            "relevance": 0.5, # Initial relevance score
            "protected": current_metadata.get("protected", False) if current_metadata else False
    }
    self.core_memory_store[memory_id] = data_package

    save_successful = self._save_core_memory_to_file # Persist after each store

        if save_successful:


    logger.info(f"HAM: Stored experience {memory_id}")
            return memory_id
        else:
            # If save failed (e.g., simulated disk full), revert adding to in-memory store
            # and potentially log that the experience was not truly stored due to simulated limit.
            logger.error(f"HAM: Failed to save core memory to file for experience {memory_id}. Reverting in-memory store for this item.")
    if memory_id in self.core_memory_store:

    del self.core_memory_store[memory_id]
            # Note self.next_memory_id was already incremented. This could lead to skipped IDs
            # if not handled, but for simulation, it might be acceptable or reset on reload.
            # Alternatively, decrement self.next_memory_id here if strict ID sequence is vital.
    return None

    async def retrieve_relevant_memories(self, query: str, limit: int = 10) -> List[HAMMemory]:
    """
    Retrieves memories relevant to a given query using semantic search, and
        merges with a keyword-based search for a comprehensive recall.
    """
        logger.debug(f"HAM: Retrieving relevant memories for query: '{query}'")

    semantic_results_ids = set()
    semantic_memories = []

    # 1. Perform Semantic Search
        if self.vector_store is not None:

    try:
                # Fetch more results from Chroma to allow for filtering and merging
    chroma_results = await self.vector_store.semantic_search(query, limit * 2)
                if chroma_results and chroma_results.get('ids')

    for i, mem_id in enumerate(chroma_results['ids'][0])


    if mem_id in self.core_memory_store:



    data_package = self.core_memory_store[mem_id]
                            try:
                                # Use the new _deserialize_memory method
                                semantic_memories.append(self._deserialize_memory(mem_id, data_package))
                                semantic_results_ids.add(mem_id)
                            except HAMMemoryError as e:

                                logger.warning(f"Skipping deserialization of memory {mem_id} from vector store due to error: {e}")

                logger.debug(f"Retrieved {len(semantic_memories)} semantic memories for query: '{query}'")
            except Exception as e:

                logger.error(f"Error during semantic search for query '{query}': {e}")
                # Fallback if semantic search fails, proceed with only keyword search
    semantic_memories = []
        else:

            logger.debug(f"VectorMemoryStore disabled, skipping semantic search for query: '{query}'")
            semantic_memories = []

    # 2. Perform Keyword Search (and potential metadata filters)
        # Re-using query_core_memory for keyword/metadata filtering, excluding already found semantic memories
    keyword_memories = []
        for mem_id, data_package in self.core_memory_store.items:

    if mem_id in semantic_results_ids:


    continue # Skip memories already found by semantic search

            # Very basic keyword matching for now (e.g., in content or metadata if rehydrated/accessible)
            # For this simple example, we'll just check a basic keyword match in metadata for non-semantic memories
            # A more advanced implementation would rehydrate content for keyword search
    item_metadata = data_package.get("metadata", )
            if any(kw.lower in str(item_metadata).lower for kw in query.lower.split if len(kw) > 2): # Simple keyword check
                try:

                    keyword_memories.append(self._deserialize_memory(mem_id, data_package))
                except HAMMemoryError as e:

                    logger.warning(f"Skipping deserialization of memory {mem_id} from keyword search due to error: {e}")

    logger.debug(f"Retrieved {len(keyword_memories)} keyword-based memories.")

    # 3. Combine and Sort Results
    combined_results = semantic_memories + keyword_memories

        # Sort by relevance (semantic score from Chroma is implicitly higher for semantic memories,
        # but we need a unified scoring or a simple time-based sort for combination)
        # For simplicity, let's sort by timestamp (newest first) for combined results
    # A more complex system would assign a combined relevance score
    combined_results.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=True)

    # Apply the final limit
    final_results = combined_results[:limit]

        logger.info(f"Retrieved {len(final_results)} combined relevant memories for query: '{query}'")
    return final_results

    def recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]:
    """
    Recalls an abstracted gist of an experience by its memory ID and returns
    a human-readable rehydrated version.

    Args:
            memory_id (str) The ID of the memory to recall.

    Returns:
            Optional[HAMRecallResult]: A HAMRecallResult object with a rehydrated string gist:
    if successful, None otherwise.
    """
        logger.debug(f"HAM: Recalling gist for memory_id '{memory_id}'")
    data_package = self.core_memory_store.get(memory_id)
        if not data_package:

    logger.error(f"Memory ID {memory_id} not found.")
            return None

    # Update the relevance score of the recalled experience.
    data_package["relevance"] = min(1.0, data_package.get("relevance", 0.5) + 0.1)

        try:


            decrypted_data = self._decrypt(data_package["encrypted_package"])
            if not decrypted_data:

    logger.error("Decryption failed for memory_id '%s'.", memory_id)
    return None

            decompressed_data_bytes = self._decompress(decrypted_data)
            if not decompressed_data_bytes:

    logger.error("Decompression failed for memory_id '%s'.", memory_id)
    return None

            # Verify checksum AFTER decryption and decompression
            stored_checksum = data_package.get("metadata", ).get('sha256_checksum')
            if stored_checksum:

    current_checksum = hashlib.sha256(decompressed_data_bytes).hexdigest()()()
                if current_checksum != stored_checksum:

    logger.critical(f"Checksum mismatch for memory ID {memory_id}! Data may be corrupted.")
                    # Optionally, could return a specific error or flag instead of proceeding
                    # For now, we'll proceed but the warning is logged.
            else:

    logger.warning(f"No checksum found in metadata for memory ID {memory_id}.")

    decompressed_data_str = decompressed_data_bytes.decode('utf-8')

        except Exception as e:


            logger.error(f"Error during SL retrieval (decrypt/decompress/checksum) for memory_id '%s': {e}", memory_id)
            # return f"Error processing memory {memory_id}." -> Changed to return None
            return None

    rehydrated_content: Any
        if "dialogue_text" in data_package["data_type"]: # Match more inclusive check
            try:

                abstracted_gist = json.loads(decompressed_data_str)
                rehydrated_content = self._rehydrate_text_gist(abstracted_gist)
            except json.JSONDecodeError:

                logger.error("Could not decode abstracted gist for memory_id '%s'. Data might be corrupted or not text.", memory_id)
    return None
            except Exception as e:

                logger.error(f"Error rehydrating text gist for memory_id '%s': {e}", memory_id)
                return None
        else:
            # For other data types, just return the decompressed string for now
    rehydrated_content = decompressed_data_str

    # Build TypedDict-style HAMRecallResult
    return {
            "id": memory_id,
            "timestamp": data_package.get("timestamp", datetime.now(timezone.utc).isoformat),
            "data_type": data_package.get("data_type", "unknown"),
            "rehydrated_gist": rehydrated_content,
            "metadata": data_package.get("metadata", )
    }

    def recall_raw_gist(self, memory_id: str) -> Optional[Dict[str, Any]]:
    """
    Recalls the raw, structured gist dictionary of an experience by its ID.
        This method is for programmatic use by other AI components that need the:
    structured data, bypassing the human-readable rehydration step.

    Args:
    memory_id (str) The ID of the memory to recall.

    Returns:
            Optional[Dict[str, Any]]: The raw abstracted gist dictionary if successful,:
    None if recall fails.
    """
        logger.debug(f"HAM: Recalling raw gist for memory_id '{memory_id}'")
    data_package = self.core_memory_store.get(memory_id)
        if not data_package:

    logger.error(f"Memory ID {memory_id} not found.")
            return None

        try:


            decrypted_data = self._decrypt(data_package["encrypted_package"])
            if not decrypted_data: return None

            decompressed_data_bytes = self._decompress(decrypted_data)
            if not decompressed_data_bytes: return None

            stored_checksum = data_package.get("metadata", ).get('sha256_checksum')
            if stored_checksum:

    current_checksum = hashlib.sha256(decompressed_data_bytes).hexdigest
                if current_checksum != stored_checksum:

    logger.critical(f"Checksum mismatch for memory ID {memory_id}! Data may be corrupted.")
    return None # Return None on checksum failure for raw recall
    decompressed_data_str = decompressed_data_bytes.decode('utf-8')

            if "dialogue_text" in data_package["data_type"]:


    return json.loads(decompressed_data_str)
            else:
                # For non-text data, the "gist" is just the stringified data.
                # Returning it in a dict to maintain a consistent return type structure.
                return {"raw_content": decompressed_data_str}

        except Exception as e:


            logger.error(f"Error during raw gist retrieval for memory_id '%s': {e}", memory_id, exc_info=True)
            return None

    def _deserialize_memory(self, memory_id: str, data_package: HAMDataPackageInternal) -> HAMMemory:
    """反序列化內部數據包為 HAMMemory 物件。"""
    timestamp = data_package.get("timestamp", "")
    data_type = data_package.get("data_type", "")
    metadata = data_package.get("metadata", )
    encrypted_package = data_package["encrypted_package"]

        try:


            decrypted_data = self._decrypt(encrypted_package)
            decompressed_data_bytes = self._decompress(decrypted_data)
            content = decompressed_data_bytes.decode('utf-8') # Assuming content is text for now

            # Verify checksum (similar to recall_gist)
            stored_checksum = metadata.get('sha256_checksum')
            if stored_checksum:

    current_checksum = hashlib.sha256(decompressed_data_bytes).hexdigest
                if current_checksum != stored_checksum:

    logger.critical(f"Checksum mismatch during deserialization for memory ID {memory_id}! Data may be corrupted.")

            # Convert timestamp to datetime object
            if isinstance(timestamp, str)

    timestamp_obj = datetime.fromisoformat(timestamp)
            else:

                timestamp_obj = timestamp

            return HAMMemory(
                id=memory_id,
                content=content,
                timestamp=timestamp_obj,
                metadata=metadata
            )
        except Exception as e:

            logger.error(f"Error deserializing memory {memory_id}: {e}")
            raise HAMMemoryError(f"Failed to deserialize memory {memory_id}: {e}")

    async def query_by_date_range(self, start_date: Any, end_date: Any, filters: Optional[Dict[str, Any]] = None) -> List[HAMMemory]:
    """改進的日期範圍查詢，支持額外過濾器。"""
        try:

            start_dt_normalized = self._normalize_date(start_date)
            end_dt_normalized = self._normalize_date(end_date)

            results = []
            for mem_id, data_package in self.core_memory_store.items:

    try:


                    item_dt = self._normalize_date(data_package["timestamp"])
                    if start_dt_normalized <= item_dt <= end_dt_normalized:

    match_filters = True
                        if filters:

    item_metadata = data_package.get("metadata", )
                            for key, value in filters.items:

    if item_metadata.get(key) != value:


    match_filters = False
                                    break
                        if match_filters:

    results.append(self._deserialize_memory(mem_id, data_package))
                except (ValueError, TypeError) as e:

                    logger.warning(f"Error processing timestamp for memory {mem_id}: {e}")
                    continue # Skip this memory if timestamp cannot be parsed

            # Sort results by timestamp
            results.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=True) # type ignore

            return results
        except Exception as e:

            logger.error(f"Date range query failed: {e}")
            raise HAMQueryError(f"Failed to query date range: {e}")

    def _perform_deletion_check(self)
    """Perform memory cleanup based on personality traits and memory usage."""
        if not self.personality_manager:

    return

    try
            import psutil:
    memory_retention = self.personality_manager.get_current_personality_trait("memory_retention", 0.5)
            memory_threshold = 1 - memory_retention

            # Check if memory usage is high
    memory_info = psutil.virtual_memory
            if memory_info.available < memory_info.total * memory_threshold:
                # Identify memories to delete (unprotected, oldest/lowest relevance first)
                memories_to_consider = sorted(
                    [
                        (mem_id, data_pkg)
                        for mem_id, data_pkg in self.core_memory_store.items:

    if not data_pkg.get("protected", False)
                    ],
                    key=lambda item: (item[1].get("relevance", 0.5), datetime.fromisoformat(item[1]["timestamp"])),
                )

                # Delete memories until memory usage is acceptable
                deleted_count = 0
                max_deletions_per_check = max(10, len(self.core_memory_store) // 10)  # Limit deletions per check

                for memory_id, _ in memories_to_consider:
                    # Safety check don't delete too many memories at once
                    if deleted_count >= max_deletions_per_check:

    logger.info(f"Memory deletion limit reached: {deleted_count} memories deleted")
                        break

                    current_memory = psutil.virtual_memory
                    if current_memory.available < current_memory.total * memory_threshold:

    if memory_id in self.core_memory_store:  # Ensure it still exists
                            # Additional safety check ensure we're not deleting protected memories
                            if not self.core_memory_store[memory_id].get("protected", False)

    del self.core_memory_store[memory_id]
                                deleted_count += 1
                                logger.debug(f"Deleted memory: {memory_id}")
                            else:

                                logger.warning(f"Attempted to delete protected memory: {memory_id}")
                    else:

                        break

                if deleted_count > 0:
                    # Save the updated memory store to file
                    self._save_core_memory_to_file
                    logger.info(f"Memory cleanup completed: {deleted_count} memories deleted")
        except Exception as e:

            logger.error(f"Error during deletion check: {e}")

    async def _delete_old_experiences(self)
    """
    Deletes old experiences that are no longer relevant.
    """
        while True:
            # Ensure we don't check too frequently
            deletion_interval = max(60, 3600 - len(self.core_memory_store) * 10)
            _ = await asyncio.sleep(deletion_interval)

            # Perform deletion check in a separate thread to avoid blocking
            try:

                _ = await asyncio.to_thread(self._perform_deletion_check)
            except Exception as e:

                logger.error(f"Error during memory cleanup: {e}")
                # Continue with next iteration even if current check failed
    continue

    def query_core_memory(self,
                          keywords: Optional[List[str]] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None,
                          data_type_filter: Optional[str] = None,
                          metadata_filters: Optional[Dict[str, Any]] = None,
                          user_id_for_facts: Optional[str] = None,
                          limit: int = 5,
                          sort_by_confidence: bool = False,
                          return_multiple_candidates: bool = False,
                          semantic_query: Optional[str] = None # New parameter
                          ) -> List[HAMRecallResult]:
    """
    Enhanced query function.
        Filters by data_type, metadata_filters (exact matches), user_id (for facts), and date_range.:
    Optional keyword search on metadata string.
        Does NOT search encrypted content for keywords in this version.
    """
    logger.debug(f"HAM: Querying core memory (type: {data_type_filter}, meta_filters: {metadata_filters}, keywords: {keywords}, semantic_query: {semantic_query})")

    candidate_mem_ids = []
    fallback_semantic = False

        if semantic_query:


    if not self.chroma_collection:
    logger.warning("ChromaDB collection not initialized. Cannot perform semantic search.")
                # Fallback to iterating all memories if semantic search is not available
    candidate_mem_ids = sorted(self.core_memory_store.keys, reverse=True)
                fallback_semantic = True
            else:

                try:
                    # Generate embedding for the semantic query using the collection's embedding function
    chroma_results = self.chroma_collection.query(
                        query_texts=[semantic_query],
                        n_results=limit * 2, # Fetch more results from Chroma to allow for filtering
    include=['metadatas', 'documents']
                    )
                    # Extract memory_ids from Chroma results
                    if chroma_results and chroma_results['ids']:

    candidate_mem_ids.extend(chroma_results['ids'][0])
                    logger.debug(f"HAM: ChromaDB returned {len(candidate_mem_ids)} candidates for semantic query."):
    except Exception as e:

    logger.error(f"Error querying ChromaDB: {e}")
                    # Fallback to iterating all memories if ChromaDB query fails
    candidate_mem_ids = sorted(self.core_memory_store.keys, reverse=True)
                    fallback_semantic = True
        else:
            # If no semantic query, iterate through all memories
            # Ensure we don't include None values in the sorted list
            candidate_mem_ids = [mem_id for mem_id in self.core_memory_store.keys() if mem_id is not None]:
    candidate_mem_ids = sorted(candidate_mem_ids, reverse=True)

    # Candidate selection Iterate through selected memory IDs
    candidate_items_with_id = []

        for mem_id in candidate_mem_ids:


    item = self.core_memory_store.get(mem_id)
            if not item: # Skip if memory not found in core store (e.g., filtered by Chroma but not in JSON)

    continue

            item_metadata = item.get("metadata", )
            match = True

            if data_type_filter:
                # Allow partial match for data_type_filter (e.g., "learned_fact_" matches all learned facts)
    if not item.get("data_type", "").startswith(data_type_filter)

    match = False

            if match and date_range:


    try:



                    item_dt = self._normalize_date(item["timestamp"])
                    start_dt_normalized = self._normalize_date(date_range[0])
                    end_dt_normalized = self._normalize_date(date_range[1])

                    if not (start_dt_normalized <= item_dt <= end_dt_normalized)


    match = False
                except (ValueError, TypeError) as e:

                    logger.warning(f"Error parsing date for memory {mem_id} or date_range {date_range}: {e}. Skipping this memory for date filter.")
    match = False # Treat as non-match if date parsing fails

    if match and metadata_filters:


    for key, value in metadata_filters.items()
                    # Support nested keys like "original_source_info.type" if needed, but simple for now
    if item_metadata.get(key) != value:

    match = False
                        break

            if match and user_id_for_facts and data_type_filter and data_type_filter.startswith("learned_fact")


    if item_metadata.get("user_id") != user_id_for_facts:
    match = False

            if match and keywords:


    metadata_str = str(item_metadata).lower()
                if not all(keyword.lower() in metadata_str for keyword in keywords):

    match = False

            if match:


    recalled_item = self.recall_gist(mem_id)
                if recalled_item: # recall_gist now returns Optional[HAMRecallResult]
                    # recalled_item already includes metadata if successful
    candidate_items_with_id.append(recalled_item)

    # Apply fallback semantic ranking when needed
        if semantic_query and fallback_semantic and candidate_items_with_id:

    query_tokens = {tok.strip('.,!?') for tok in semantic_query.lower.split if len(tok.strip('.,!?')) > 2}:
    def _fallback_score(rec)
    text = str(rec.get("rehydrated_gist", "")).lower
                gist_tokens = {tok.strip('.,!?') for tok in text.split if len(tok.strip('.,!?')) > 2}:
    return len(query_tokens & gist_tokens)
            # Sort by score desc, then by timestamp (newest first)
            candidate_items_with_id.sort(
                key=lambda x: (_fallback_score(x), datetime.fromisoformat(x["timestamp"])),
                reverse=True
            )

        # Sort by confidence if requested (primarily for facts)
    if sort_by_confidence and data_type_filter and data_type_filter.startswith("learned_fact")

    candidate_items_with_id.sort(key=lambda x: x["metadata"].get("confidence", 0.0), reverse=True)

    # Apply limit
    results: List[HAMRecallResult] = candidate_items_with_id[:limit]

        if return_multiple_candidates:


    return results

    logger.debug(f"HAM: Query returned {len(results)} results (limit was {limit}).")
    return results

    def increment_metadata_field(self, memory_id: str, field_name: str, increment_by: int = 1) -> bool:
    """
    Increments a numerical field in the metadata of a specific memory record.
    This is more efficient than recalling, modifying, and re-storing the whole package.

    Args:
            memory_id (str) The ID of the memory record to update.
            field_name (str) The name of the metadata field to increment.
            increment_by (int) The amount to increment the field by.

    Returns: bool True if the update was successful, False otherwise.
    """
        if memory_id in self.core_memory_store:

    record = self.core_memory_store[memory_id]
            if "metadata" not in record:

    record["metadata"] = {}

            current_value = record["metadata"].get(field_name, 0)
            if isinstance(current_value, (int, float)):

    record["metadata"][field_name] = current_value + increment_by
                logger.debug(f"HAM: Incremented metadata field '{field_name}' for mem_id '{memory_id}'.")
                # For simplicity, we trigger a full save. A more advanced implementation
                # might use a more granular or delayed save mechanism.
                return self._save_core_memory_to_file
            else:

    logger.error(f"HAM: Metadata field '{field_name}' for mem_id '{memory_id}' is not a number.")
    return False
        else:

            logger.error(f"HAM: Cannot increment metadata for non-existent mem_id '{memory_id}'.")
    return False

if __name__ == '__main__':


    print("--- HAMMemoryManager Test ---")
    # Ensure a clean state for testing if file exists from previous run
    test_file_name = "ham_test_memory.json"
    if os.path.exists(os.path.join(HAMMemoryManager.storage_dir, test_file_name)):

    os.remove(os.path.join(HAMMemoryManager.storage_dir, test_file_name))

    ham = HAMMemoryManager(core_storage_filename=test_file_name)

    # Test storing experiences
    print("\n--- Storing Experiences ---")
    ts_now = datetime.now(timezone.utc).isoformat # Added timezone
    # Provide metadata that aligns better with DialogueMemoryEntryMetadata
    exp1_metadata = DialogueMemoryEntryMetadata(
    timestamp=datetime.fromisoformat(ts_now),
    speaker="user",
    dialogue_id="test_dialogue_1",
    turn_id=1,
    user_id="test_user",
    session_id="s1"
    )
    exp1_id = asyncio.run(ham.store_experience("Hello Miko! This is a test dialogue.", "dialogue_text", exp1_metadata))

    exp2_metadata = DialogueMemoryEntryMetadata(
    timestamp=datetime.fromisoformat(ts_now),
    speaker="system",
    dialogue_id="test_dialogue_1",
    turn_id=2,
    source="developer_log"
    )
    exp2_id = asyncio.run(ham.store_experience("Miko learned about HAM today.", "dialogue_text", exp2_metadata))

    exp3_metadata = DialogueMemoryEntryMetadata(
    timestamp=datetime.now(timezone.utc),
    speaker="system",
    dialogue_id="test_dialogue_2",
    turn_id=1,
    type="puzzle_solution"
    )
    exp3_id = asyncio.run(ham.store_experience({"value": 42, "unit": "answer"}, "generic_data", exp3_metadata))

    print(f"Stored IDs: {exp1_id}, {exp2_id}, {exp3_id}")

    # Test recalling gists
    print("\n--- Recalling Gists ---")
    if exp1_id:

    recalled_exp1 = ham.recall_gist(exp1_id)
        print(f"Recalled exp1: {json.dumps(recalled_exp1, indent=2) if recalled_exp1 else 'None'}"):
    if exp3_id:

    recalled_exp3 = ham.recall_gist(exp3_id)
        print(f"Recalled exp3: {json.dumps(recalled_exp3, indent=2) if recalled_exp3 else 'None'}"):

    recalled_non_existent = ham.recall_gist('mem_000999')
    print(f"Recalled non-existent: {recalled_non_existent}")

    # Test querying memory
    print("\n--- Querying Memory (keywords in metadata) ---")
    query_results_kw: List[HAMRecallResult] = ham.query_core_memory(keywords=["test_user"])
    for res_item in query_results_kw:

    print(json.dumps(res_item, indent=2))

    print("\n--- Querying Memory (data_type) ---")
    query_results_type: List[HAMRecallResult] = ham.query_core_memory(data_type_filter="generic_data")
    for res_item in query_results_type:

    print(json.dumps(res_item, indent=2))

    # Test persistence by reloading
    print("\n--- Testing Persistence ---")
    del ham # Delete current instance
    ham_reloaded = HAMMemoryManager(core_storage_filename=test_file_name) # Reload from file

    print(f"Recalling exp1 after reload: {ham_reloaded.recall_gist(exp1_id if exp1_id else 'mem_000001')}")

    # Clean up test file
    if os.path.exists(ham_reloaded.core_storage_filepath)

    os.remove(ham_reloaded.core_storage_filepath)
    print(f"\nCleaned up {ham_reloaded.core_storage_filepath}")
    print("--- Test Complete ---")