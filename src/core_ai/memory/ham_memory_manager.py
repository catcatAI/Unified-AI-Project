import json
import zlib
import base64
import os
from datetime import datetime, timezone
from collections import Counter
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import asyncio # Added for asyncio.to_thread
from typing import Optional, List, Dict, Any, Tuple, Union # Added Union for recall_gist return
from src.shared.types.common_types import DialogueMemoryEntryMetadata, HAMDataPackageInternal, HAMRecallResult # Import new types, changed to src.

# Placeholder for actual stopword list and NLP tools if not available
try:
    # A very basic list, consider a more comprehensive one for real use
    STOPWORDS = set(["a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "should",
                     "can", "could", "may", "might", "must", "of", "to", "in", "on", "at",
                     "for", "with", "about", "against", "between", "into", "through",
                     "during", "before", "after", "above", "below", "from", "up", "down",
                     "out", "off", "over", "under", "again", "further", "then", "once",
                     "here", "there", "when", "where", "why", "how", "all", "any", "both",
                     "each", "few", "more", "most", "other", "some", "such", "no", "nor",
                     "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
                     "just", "don", "should've", "now", "i", "me", "my", "myself", "we",
                     "our", "ours", "ourselves", "you", "your", "yours", "yourself",
                     "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
                     "herself", "it", "its", "itself", "they", "them", "their", "theirs",
                     "themselves", "what", "which", "who", "whom", "this", "that", "these",
                     "those", "am"])
except ImportError:
    STOPWORDS = set()


class HAMMemoryManager:
    """
    Hierarchical Abstractive Memory Manager v0.2.
    Handles storage and retrieval of experiences, incorporating abstraction,
    compression, Fernet encryption, and SHA256 checksums for data integrity.

    Encryption relies on the MIKO_HAM_KEY environment variable for the Fernet key.
    If not set, a temporary key is generated for the session (data not persistent).
    Can be made aware of simulated disk resource limits via ResourceAwarenessService.
    """
    BASE_SAVE_DELAY_SECONDS = 0.05 # Base delay for conceptual lag simulation

    def __init__(self,
                 core_storage_filename="ham_core_memory.json",
                 resource_awareness_service: Optional[Any] = None): # Optional['ResourceAwarenessService']
        """
        Initializes the HAMMemoryManager.

        Args:
            core_storage_filename (str): Filename for the persistent core memory store.
            resource_awareness_service (Optional[ResourceAwarenessService]): Service to get simulated resource limits.
        """
        self.resource_awareness_service = resource_awareness_service
        self.core_memory_store: Dict[str, HAMDataPackageInternal] = {}
        self.next_memory_id = 1

        # Determine base path for data storage within the project structure
        # Assuming this script is in src/core_ai/memory/
        # PROJECT_ROOT/data/processed_data/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        self.storage_dir = os.path.join(project_root, "data", "processed_data")
        os.makedirs(self.storage_dir, exist_ok=True)

        self.core_storage_filepath = os.path.join(self.storage_dir, core_storage_filename)

        # Initialize Fernet for encryption
        key_str = os.environ.get("MIKO_HAM_KEY")
        if key_str:
            # Assuming the key in env is already a valid URL-safe base64 encoded Fernet key
            self.fernet_key = key_str.encode()
        else:
            print("CRITICAL WARNING: MIKO_HAM_KEY environment variable not set.")
            print("Encryption/Decryption will NOT be functional. Generating a TEMPORARY, NON-PERSISTENT key for this session only.")
            print("DO NOT use this for any real data you want to keep, as it will be lost.")
            self.fernet_key = Fernet.generate_key()
            print(f"Temporary MIKO_HAM_KEY for this session: {self.fernet_key.decode()}")

        try:
            self.fernet = Fernet(self.fernet_key)
        except Exception as e:
            print(f"CRITICAL: Failed to initialize Fernet. Provided MIKO_HAM_KEY might be invalid. Error: {e}")
            print("Encryption will be DISABLED for this session.")
            self.fernet = None

        self._load_core_memory_from_file()
        print(f"HAMMemoryManager initialized. Core memory file: {self.core_storage_filepath}. Encryption enabled: {self.fernet is not None}")

    def _generate_memory_id(self) -> str:
        mem_id = f"mem_{self.next_memory_id:06d}"
        self.next_memory_id += 1
        return mem_id

    # --- Encryption/Decryption ---
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypts data using Fernet if available, otherwise returns raw data."""
        if self.fernet:
            return self.fernet.encrypt(data)
        # Fallback: If Fernet is not initialized, return data unencrypted (with a warning)
        print("Warning: Fernet not initialized, data NOT encrypted.")
        return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypts data using Fernet if available, otherwise returns raw data."""
        if self.fernet:
            try:
                return self.fernet.decrypt(data)
            except InvalidToken:
                print("Error: Invalid token during Fernet decryption. Data might be corrupted or wrong key.")
                return b''
            except Exception as e:
                print(f"Error during Fernet decryption: {e}")
                return b''
        # Fallback: If Fernet is not initialized, return data as is (with a warning)
        print("Warning: Fernet not initialized, data NOT decrypted.")
        return data

    # --- Compression/Decompression ---
    def _compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        try:
            return zlib.decompress(data)
        except zlib.error as e:
            print(f"Error during decompression: {e}")
            return b'' # Return empty bytes on error

    # --- Abstraction/Rehydration (Text specific for v0.1, with v0.2 placeholders) ---
    def _abstract_text(self, text: str) -> dict:
        """
        Abstracts raw text into a structured "gist" dictionary.
        Includes basic summarization, keyword extraction, and placeholders for
        advanced features like Chinese radical extraction and English POS tagging.
        """
        words = [word.lower().strip(".,!?;:'\"()") for word in text.split()]
        # Basic keyword extraction (top N frequent words, excluding stopwords)
        filtered_words = [word for word in words if word and word not in STOPWORDS]
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
            # Conceptual: In a real system, call a radical extraction library/function
            # For example, if text = "你好世界"
            # radicals_placeholder = extract_radicals(text) # -> e.g., ['女', '子', '口', '丿', 'Ｌ', '田'] (highly dependent on lib)
            radicals_placeholder = ["RadicalPlaceholder1", "RadicalPlaceholder2"] # Dummy
            print(f"HAM: Placeholder: Detected Chinese-like text, conceptual radicals would be extracted.")
        else: # Assume English-like or other Latin script
            # Conceptual: In a real system, call POS tagging
            # For example, if text = "Hello world"
            # pos_tags_placeholder = extract_pos_tags(filtered_words) # -> e.g., [('hello', 'UH'), ('world', 'NN')]
            if keywords: # Only add if there are keywords, to simulate some processing
                pos_tags_placeholder = [{kw: "NOUN_placeholder"} for kw in keywords[:2]] # Dummy POS for first 2 keywords
            print(f"HAM: Placeholder: Detected English-like text, conceptual POS tags would be generated.")


        return {
            "summary": summary,
            "keywords": keywords,
            "original_length": len(text),
            "radicals_placeholder": radicals_placeholder if is_likely_chinese else None,
            "pos_tags_placeholder": pos_tags_placeholder if not is_likely_chinese and keywords else None
        }

    def _rehydrate_text_gist(self, gist: dict) -> str:
        """
        Rehydrates an abstracted text gist into a human-readable string format.
        Includes summary, keywords, and any placeholder advanced features.
        """
        # For v0.2, could include placeholder info
        base_rehydration = f"Summary: {gist.get('summary', 'N/A')}\nKeywords: {', '.join(gist.get('keywords', []))}"
        if gist.get("radicals_placeholder"):
            base_rehydration += f"\nRadicals (Placeholder): {gist.get('radicals_placeholder')}"
        if gist.get("pos_tags_placeholder"):
            base_rehydration += f"\nPOS Tags (Placeholder): {gist.get('pos_tags_placeholder')}"
        return base_rehydration

    # --- Core Layer File Operations ---
    def _get_current_disk_usage_gb(self) -> float:
        """Returns the current size of the core_storage_filepath in GB."""
        try:
            if os.path.exists(self.core_storage_filepath):
                file_size_bytes = os.path.getsize(self.core_storage_filepath)
                return file_size_bytes / (1024**3) # Bytes to GB
        except OSError as e:
            print(f"HAM: Error getting file size for {self.core_storage_filepath}: {e}")
        return 0.0 # Default to 0 if file doesn't exist or error

    def _simulate_disk_lag_and_check_limit(self) -> bool:
        """
        Checks simulated disk usage against limits and simulates lag if thresholds are met.
        Returns True if it's okay to save, False if disk full limit is hit.
        """
        if not self.resource_awareness_service:
            return True # No service, no simulated limits to check

        disk_config = self.resource_awareness_service.get_simulated_disk_config()
        if not disk_config:
            return True # No disk config in service, no limits to check

        current_usage_gb = self._get_current_disk_usage_gb()
        total_simulated_disk_gb = disk_config.get('space_gb', float('inf'))

        # Hard Limit Check:
        # A more accurate check would estimate the size of the data *about to be written*.
        # For now, we check if current usage already exceeds or is very close to the total.
        # If self.core_memory_store is large and not yet saved, current_usage_gb might be small.
        # This check is primarily for when the file already exists and is large.
        if current_usage_gb >= total_simulated_disk_gb:
            print(f"HAM: CRITICAL - Simulated disk full! Usage: {current_usage_gb:.2f}GB, Limit: {total_simulated_disk_gb:.2f}GB. Save operation aborted.")
            return False # Prevent save

        # Lag Simulation:
        warning_thresh_gb = total_simulated_disk_gb * (disk_config.get('warning_threshold_percent', 80) / 100.0)
        critical_thresh_gb = total_simulated_disk_gb * (disk_config.get('critical_threshold_percent', 95) / 100.0)

        lag_to_apply_seconds = 0.0
        base_delay = self.BASE_SAVE_DELAY_SECONDS # A small base delay for I/O simulation

        if current_usage_gb >= critical_thresh_gb:
            lag_factor = disk_config.get('lag_factor_critical', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            print(f"HAM: WARNING - Simulated disk usage ({current_usage_gb:.2f}GB) is at CRITICAL level (>{critical_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")
        elif current_usage_gb >= warning_thresh_gb:
            lag_factor = disk_config.get('lag_factor_warning', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            print(f"HAM: INFO - Simulated disk usage ({current_usage_gb:.2f}GB) is at WARNING level (>{warning_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")

        if lag_to_apply_seconds > 0:
            import time # Import time locally for this function
            time.sleep(lag_to_apply_seconds)

        return True # OK to save

    def _save_core_memory_to_file(self) -> bool: # Added return type bool
        """Saves the core memory store to a JSON file, respecting simulated disk limits."""

        if not self._simulate_disk_lag_and_check_limit():
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
                for mem_id, data_pkg in self.core_memory_store.items():
                    serializable_store[mem_id] = {
                        "timestamp": data_pkg["timestamp"],
                        "data_type": data_pkg["data_type"],
                        "encrypted_package_b64": data_pkg["encrypted_package"].decode('latin-1'), # latin-1 for bytes
                        "metadata": data_pkg.get("metadata", {})
                    }
                json.dump({"next_memory_id": self.next_memory_id, "store": serializable_store}, f, indent=2)
            return True # Save successful
        except Exception as e:
            print(f"Error saving core memory to file: {e}")
            return False # Save failed

    def _load_core_memory_from_file(self):
        if not os.path.exists(self.core_storage_filepath):
            print("Core memory file not found. Initializing an empty store and saving.")
            self.core_memory_store = {}
            self.next_memory_id = 1
            self._save_core_memory_to_file() # Create the file with an empty store
            return

        try:
            with open(self.core_storage_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.next_memory_id = data.get("next_memory_id", 1)
                serializable_store = data.get("store", {})
                self.core_memory_store = {}
                for mem_id, data_pkg_b64 in serializable_store.items():
                    self.core_memory_store[mem_id] = {
                        "timestamp": data_pkg_b64["timestamp"],
                        "data_type": data_pkg_b64["data_type"],
                        "encrypted_package": data_pkg_b64["encrypted_package_b64"].encode('latin-1'),
                        "metadata": data_pkg_b64.get("metadata", {})
                    }
            print(f"Core memory loaded from {self.core_storage_filepath}. Next ID: {self.next_memory_id}")
        except Exception as e:
            print(f"Error loading core memory from file: {e}. Starting with an empty store.")
            self.core_memory_store = {}
            self.next_memory_id = 1

    # --- Public API Methods ---
    def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[DialogueMemoryEntryMetadata] = None) -> Optional[str]:
        """
        Stores a new experience into the HAM.
        The raw_data is processed (abstracted, checksummed, compressed, encrypted)
        and then stored.

        Args:
            raw_data: The raw data of the experience (e.g., text string, dict).
            data_type (str): Type of the data (e.g., "dialogue_text", "sensor_reading").
                             If "dialogue_text" (or contains it), text abstraction is applied.
            metadata (Optional[DialogueMemoryEntryMetadata]): Additional metadata for the experience.
                Should conform to DialogueMemoryEntryMetadata. A 'sha256_checksum' will be added.

        Returns:
            Optional[str]: The generated memory ID if successful, otherwise None.
        """
        print(f"HAM: Storing experience of type '{data_type}'")

        # Ensure metadata is a dict for internal processing, even if None is passed.
        # The type hint guides towards DialogueMemoryEntryMetadata, but internally it's handled as Dict[str, Any]
        # for flexibility if direct dicts are passed (though discouraged by type hint).
        current_metadata: Dict[str, Any] = dict(metadata) if metadata else {}


        if "dialogue_text" in data_type: # More inclusive check for user_dialogue_text, ai_dialogue_text
            if not isinstance(raw_data, str):
                print(f"Error: raw_data for {data_type} must be a string.")
                return None
            abstracted_gist = self._abstract_text(raw_data)
            # Gist itself should be serializable (dict of strings/lists)
            data_to_process = json.dumps(abstracted_gist).encode('utf-8')
        else:
            # For other data types, placeholder: just try to convert to string and encode
            # This part needs to be properly implemented for each data type
            try:
                data_to_process = str(raw_data).encode('utf-8')
            except Exception as e:
                print(f"Error encoding raw_data for type {data_type}: {e}")
                return None

        # Add checksum to metadata BEFORE compression/encryption
        sha256_checksum = hashlib.sha256(data_to_process).hexdigest()
        current_metadata['sha256_checksum'] = sha256_checksum

        try:
            compressed_data = self._compress(data_to_process)
            encrypted_data = self._encrypt(compressed_data)
        except Exception as e:
            print(f"Error during SL processing (compress/encrypt/checksum): {e}")
            return None

        memory_id = self._generate_memory_id()
        data_package: HAMDataPackageInternal = {
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "encrypted_package": encrypted_data, # This is bytes
            "metadata": current_metadata # Use the processed current_metadata
        }
        self.core_memory_store[memory_id] = data_package

        save_successful = self._save_core_memory_to_file() # Persist after each store

        if save_successful:
            print(f"HAM: Stored experience {memory_id}")
            return memory_id
        else:
            # If save failed (e.g., simulated disk full), revert adding to in-memory store
            # and potentially log that the experience was not truly stored due to simulated limit.
            print(f"HAM: Failed to save core memory to file for experience {memory_id}. Reverting in-memory store for this item.")
            if memory_id in self.core_memory_store:
                del self.core_memory_store[memory_id]
            # Note: self.next_memory_id was already incremented. This could lead to skipped IDs
            # if not handled, but for simulation, it might be acceptable or reset on reload.
            # Alternatively, decrement self.next_memory_id here if strict ID sequence is vital.
            return None

    def recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]:
        """
        Recalls an abstracted gist of an experience by its memory ID.
        The data is retrieved, decrypted, decompressed, and checksum verified.
        The abstracted gist is then rehydrated (for text) or returned as is.

        Args:
            memory_id (str): The ID of the memory to recall.

        Returns:
            Optional[HAMRecallResult]: A HAMRecallResult object if successful,
                                       None if recall fails at any stage.
        """
        print(f"HAM: Recalling gist for memory_id '{memory_id}'")
        data_package = self.core_memory_store.get(memory_id)
        if not data_package:
            print(f"Error: Memory ID {memory_id} not found.")
            return None

        try:
            decrypted_data = self._decrypt(data_package["encrypted_package"])
            if not decrypted_data:
                print("Error: Decryption failed.")
                return None

            decompressed_data_bytes = self._decompress(decrypted_data)
            if not decompressed_data_bytes:
                print("Error: Decompression failed.")
                return None

            # Verify checksum AFTER decryption and decompression
            stored_checksum = data_package.get("metadata", {}).get('sha256_checksum') # type: ignore
            if stored_checksum:
                current_checksum = hashlib.sha256(decompressed_data_bytes).hexdigest()
                if current_checksum != stored_checksum:
                    print(f"CRITICAL WARNING: Checksum mismatch for memory ID {memory_id}! Data may be corrupted.")
                    # Optionally, could return a specific error or flag instead of proceeding
                    # For now, we'll proceed but the warning is logged.
            else:
                print(f"Warning: No checksum found in metadata for memory ID {memory_id}.")


            decompressed_data_str = decompressed_data_bytes.decode('utf-8')

        except Exception as e:
            print(f"Error during SL retrieval (decrypt/decompress/checksum): {e}")
            # return f"Error processing memory {memory_id}." -> Changed to return None
            return None

        rehydrated_content: Any
        if "dialogue_text" in data_package["data_type"]: # Match more inclusive check
            try:
                abstracted_gist = json.loads(decompressed_data_str)
                rehydrated_content = self._rehydrate_text_gist(abstracted_gist)
            except json.JSONDecodeError:
                print("Error: Could not decode abstracted gist. Data might be corrupted or not text.")
                return None
            except Exception as e:
                print(f"Error rehydrating text gist: {e}")
                return None
        else:
            # For other data types, just return the decompressed string for now
            rehydrated_content = decompressed_data_str

        return HAMRecallResult(
            id=memory_id,
            timestamp=data_package["timestamp"],
            data_type=data_package["data_type"],
            rehydrated_gist=rehydrated_content,
            metadata=data_package.get("metadata", {}) # type: ignore
        )

    def query_core_memory(self,
                          keywords: Optional[List[str]] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None,
                          data_type_filter: Optional[str] = None,
                          metadata_filters: Optional[Dict[str, Any]] = None,
                          user_id_for_facts: Optional[str] = None,
                          limit: int = 5,
                          sort_by_confidence: bool = False
                          ) -> List[HAMRecallResult]:
        """
        Enhanced query function.
        Filters by data_type, metadata_filters (exact matches), user_id (for facts), and date_range.
        Optional keyword search on metadata string.
        Does NOT search encrypted content for keywords in this version.
        """
        print(f"HAM: Querying core memory (type: {data_type_filter}, meta_filters: {metadata_filters}, keywords: {keywords})")

        # Candidate selection: Iterate through all memories. Could be optimized with indexing.
        # For now, iterate and then filter.

        candidate_items_with_id = []
        # Sort by memory_id (which implies rough chronological order, newest first)
        # This helps if limit is applied before full sorting by confidence, to get recent items.
        sorted_memory_ids = sorted(self.core_memory_store.keys(), reverse=True)

        for mem_id in sorted_memory_ids:
            item = self.core_memory_store[mem_id]
            item_metadata = item.get("metadata", {})
            match = True

            if data_type_filter:
                # Allow partial match for data_type_filter (e.g., "learned_fact_" matches all learned facts)
                if not item.get("data_type", "").startswith(data_type_filter):
                    match = False

            if match and date_range:
                try:
                    item_dt = datetime.fromisoformat(item["timestamp"])
                    start_date, end_date = date_range
                    # Ensure timezone consistency for comparison
                    if item_dt.tzinfo is None:
                        # If stored timestamp is naive, assume UTC for comparison
                        item_dt = item_dt.replace(tzinfo=timezone.utc)
                    if not (start_date <= item_dt <= end_date):
                        match = False
                except (ValueError, TypeError): # If timestamp is not valid ISO format or other error
                    match = False # Or log error and continue

            if match and metadata_filters:
                for key, value in metadata_filters.items():
                    # Support nested keys like "original_source_info.type" if needed, but simple for now
                    if item_metadata.get(key) != value:
                        match = False
                        break

            if match and user_id_for_facts and data_type_filter and data_type_filter.startswith("learned_fact"):
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

        # Sort by confidence if requested (primarily for facts)
        if sort_by_confidence and data_type_filter and data_type_filter.startswith("learned_fact"):
            candidate_items_with_id.sort(key=lambda x: x["metadata"].get("confidence", 0.0), reverse=True)

        # Apply limit
        results: List[HAMRecallResult] = candidate_items_with_id[:limit]

        print(f"HAM: Query returned {len(results)} results (limit was {limit}).")
        return results

if __name__ == '__main__':
    print("--- HAMMemoryManager Test ---")
    # Ensure a clean state for testing if file exists from previous run
    test_file_name = "ham_test_memory.json"
    if os.path.exists(os.path.join(HAMMemoryManager().storage_dir, test_file_name)):
        os.remove(os.path.join(HAMMemoryManager().storage_dir, test_file_name))

    ham = HAMMemoryManager(core_storage_filename=test_file_name)

    # Test storing experiences
    print("\n--- Storing Experiences ---")
    ts_now = datetime.now(timezone.utc).isoformat() # Added timezone
    # Provide metadata that aligns better with DialogueMemoryEntryMetadata
    exp1_metadata: DialogueMemoryEntryMetadata = {"speaker": "user", "timestamp": ts_now, "user_id": "test_user", "session_id": "s1"} # type: ignore
    exp1_id = ham.store_experience("Hello Miko! This is a test dialogue.", "dialogue_text", exp1_metadata)

    exp2_metadata: DialogueMemoryEntryMetadata = {"speaker": "system", "timestamp": ts_now, "source": "developer_log"} # type: ignore
    exp2_id = ham.store_experience("Miko learned about HAM today.", "dialogue_text", exp2_metadata)

    exp3_metadata: Dict[str, Any] = {"type": "puzzle_solution"} # Generic metadata
    exp3_id = ham.store_experience({"value": 42, "unit": "answer"}, "generic_data", exp3_metadata) # type: ignore

    print(f"Stored IDs: {exp1_id}, {exp2_id}, {exp3_id}")

    # Test recalling gists
    print("\n--- Recalling Gists ---")
    if exp1_id:
        recalled_exp1 = ham.recall_gist(exp1_id)
        print(f"Recalled exp1: {json.dumps(recalled_exp1, indent=2) if recalled_exp1 else 'None'}")
    if exp3_id:
        recalled_exp3 = ham.recall_gist(exp3_id)
        print(f"Recalled exp3: {json.dumps(recalled_exp3, indent=2) if recalled_exp3 else 'None'}")

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
    if os.path.exists(ham_reloaded.core_storage_filepath):
        os.remove(ham_reloaded.core_storage_filepath)
    print(f"\nCleaned up {ham_reloaded.core_storage_filepath}")
    print("--- Test Complete ---")
