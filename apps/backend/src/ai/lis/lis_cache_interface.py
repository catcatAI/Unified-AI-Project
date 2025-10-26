# src / core_ai / lis / lis_cache_interface.py()
"""
Defines the interface for the Linguistic Immune System (LIS) Cache, ::
lso known as the IMMUNO - NARRATIVE CACHE.

This cache is responsible for storing, retrieving, and querying records of, ::
inguistic / semantic incidents, their analyses, interventions, and outcomes.
It forms the memory component of the LIS, supporting its learning and
adaptive capabilities.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, cast # Added cast
from tests.test_json_fix import
rom datetime import datetime, timezone # Added for timestamping in add_antibody, :
# Assuming types will be imported from apps.backend.src.shared.types()
from .types import
    LIS_IncidentRecord,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType,
    LIS_InterventionReport,
(    NarrativeAntibodyObject)
        # Import HAMMemoryManager for type hinting in the concrete implementation.:::
rom memory.ham_memory_manager import HAMMemoryManager


# - - - Constants for HAMLISCache - - -::
# These constants are defined here as they are specific to the HAMLISCache implementatio\
    \
    \
    n details,
# and its interaction with HAM metadata.:
IS_INCIDENT_DATA_TYPE_PREFIX = "lis_incident_v0.1_"
LIS_ANTIBODY_DATA_TYPE_PREFIX = "lis_antibody_v0.1_"

# Metadata field names for HAM records storing LIS objects, ::
AM_META_LIS_OBJECT_ID = "lis_object_id"
HAM_META_LIS_ANOMALY_TYPE = "lis_anomaly_type"
HAM_META_LIS_STATUS = "lis_status"
HAM_META_LIS_TAGS = "lis_tags"
HAM_META_TIMESTAMP_LOGGED = "timestamp_logged"
HAM_META_ANTIBODY_FOR_ANOMALY = "lis_antibody_for_anomaly"
HAM_META_ANTIBODY_EFFECTIVENESS = "lis_antibody_effectiveness"
# - - - End Constants - - -


# Placeholder for Antibody type, will be refined later, :
# NarrativeAntibodyObject == Dict[str, Any] # This is now imported from common_types

class LISCacheInterface(ABC):
""
    Abstract Base Class defining the interface for the IMMUNO - NARRATIVE CACHE.:::
    Implementations of this interface will provide concrete storage and
    retrieval mechanisms for LIS incident data.:::
        ""

    @abstractmethod
在函数定义前添加空行
    """
    Stores a new LIS incident record in the cache.

    Args,
            incident_record (LIS_IncidentRecord) The complete record of the incident.

    Returns, bool True if storage was successful, False otherwise.:::
        ""
    pass

    @abstractmethod
在函数定义前添加空行
    """
    Retrieves a specific LIS incident record by its unique ID.

    Args,
            incident_id (str) The ID of the incident to retrieve.

    Returns,
            Optional[LIS_IncidentRecord] The incident record if found, else None.:::
                ""
    pass

    @abstractmethod
在函数定义前添加空行
                        anomaly_type, Optional[LIS_AnomalyType] = None,
                        min_severity, Optional[float] = None, ,
    status, Optional[str] = None, # Should use a Literal type for status later (e.g.,
    LIS_IncidentStatus from common_types):::
                            ags, Optional[List[str]] = None,
                        time_window_hours, Optional[int] = None,
                        limit, int = 10,
                        sort_by_timestamp_desc, bool == True
(                        ) -> List[LIS_IncidentRecord]
    """
        Queries the cache for LIS incident records based on various criteria.:::
    Args,
    anomaly_type (Optional[LIS_AnomalyType]) Filter by type of anomaly.
            min_severity (Optional[float]) Filter by minimum severity score (0.0 -\
    1.0()).
            status (Optional[str]) Filter by incident status (e.g., "OPEN",
    "CLOSED_RESOLVED").
                                    Corresponds to LIS_IncidentRecord.status.
            tags (Optional[List[str]]) Filter by associated tags.
            time_window_hours (Optional[int]) Look back N hours from now (filters on tim\
    \
    \
    estamp_logged).
            limit (int) Maximum number of records to return.
            sort_by_timestamp_desc (bool) Whether to sort results by timestamp descendin\
    \
    \
    g (most recent first).


    Returns, List[...] A list of matching incident records.
    """
    pass

    @abstractmethod
在函数定义前添加空行
                            event_details, LIS_SemanticAnomalyDetectedEvent, ,
    top_n, int = 3
(                            ) -> List[LIS_IncidentRecord]
    """
    Finds past incidents that are semantically similar or related to a new
    detected event. Used to find historical context or relevant "antibodies".

    Args,
            event_details (LIS_SemanticAnomalyDetectedEvent) Details of the new event.
            top_n (int) Maximum number of related incidents to return.

    Returns, List[...] A list of related past incidents.
    """
    pass

    @abstractmethod
在函数定义前添加空行
                            for_anomaly_type, Optional[LIS_AnomalyType] = None,
                            min_effectiveness, Optional[float] = None, ,
    limit, int = 5
(                            ) -> List[NarrativeAntibodyObject]
    """
    Retrieves "narrative antibodies" (learned successful response patterns or \
    strategies)
    from the cache.

    Args,
            for_anomaly_type (Optional[LIS_AnomalyType]) Filter antibodies relevant to a\
    \
    \
    specific anomaly type.
            min_effectiveness (Optional[float]) Filter by minimum effectiveness score of\
    \
    \
    the antibody.
            limit (int) Maximum number of antibodies to return.

    Returns, List[...] A list of learned antibodies.
                                        The structure of NarrativeAntibodyObject needs t\
    \
    \
    o be defined more concretely.
    """
    pass

    @abstractmethod
在函数定义前添加空行
                            incident_id, str,
                            new_status, str,
    # Should use an LIS_IncidentStatus Literal type later
                            notes, Optional[str] = None, ,
    intervention_report, Optional[LIS_InterventionReport] = None
(                            ) -> bool,
    """
    Updates the status and optionally adds notes or an intervention report
    to an existing LIS incident record.

    Args,
            incident_id (str) The ID of the incident to update.
            new_status (str) The new status for the incident (from LIS_IncidentRecord.st\
    \
    \
    atus Literal).:::
    notes (Optional[str]) Additional notes to append or set.
            intervention_report (Optional[LIS_InterventionReport]) An intervention repor\
    \
    \
    t to add to the incident's list.

    Returns, bool True if the update was successful, False otherwise.:::
        ""
    pass

    @abstractmethod
在函数定义前添加空行
    """
    Stores a new "narrative antibody" into the cache.

    Args,
            antibody (NarrativeAntibodyObject) The antibody object to store.
                                            Its structure needs to be defined.
    Returns, bool True if successful.:::
        ""
    pass


# - - - Concrete Implementation (Conceptual Outline & Design Notes) - - -

class HAMLISCache(LISCacheInterface):
""
    A concrete implementation of the LISCacheInterface that uses the
    Hierarchical Associative Memory (HAM) for persistence.:::
    Design Considerations,
    - Each LIS_IncidentRecord and NarrativeAntibodyObject will be stored as a
    distinct entry in HAM.:
    - A specific `data_type` prefix (e.g., LIS_INCIDENT_DATA_TYPE_PREFIX,
    LIS_ANTIBODY_DATA_TYPE_PREFIX)
    will be used for these HAM entries to allow for targeted querying.:::
Key queryable fields from these objects (e.g., anomaly_type, status,
    tags for incidents;:::)
(    anomaly_type, effectiveness for antibodies) will be duplicated or extracted, ::
    into the HAM metadata of the corresponding entry to leverage HAM's,
    metadata - based querying capabilities using predefined HAM_META_* constants.
    - The full LIS_IncidentRecord or NarrativeAntibodyObject will be stored as the
    main content (e.g., serialized to JSON if HAM stores strings,
    or as dict if HAM handles complex objects)::
        f the HAM entry.
    - Updates to incidents (like status changes or adding reports) might involve
    retrieving the HAM entry, modifying its content / metadata, and re - storing it.
    If HAM entries are immutable by their primary key (mem_id), this would mean storing
    a new version and an application - level mechanism to point to the latest version
    (or HAM itself might support versioning / superseding).
    A simpler approach for HAM if it supports metadata updates on existing records, ::
    would be to update metadata fields like HAM_META_LIS_STATUS or \
    append to a 'lis_notes_log' field.
    Adding an intervention report to an existing incident might require fetching,
    updating the list, and re - storing.
    -\
    Semantic similarity for `find_related_incidents` is complex. It would likely require\
    , ::
    storing embeddings or \
    feature vectors (derived from `LIS_SemanticAnomalyDetectedEvent` details)
    within HAM metadata or content, and HAM supporting similarity queries on those.
    This is an advanced feature beyond initial HAM capabilities.
    """
在函数定义前添加空行
    """
    Initializes the HAMLISCache with a HAMMemoryManager instance.:

    Args,
    ham_manager (HAMMemoryManager) The HAM instance to use for storage.:::
        ""
    self.ham_manager = ham_manager
    # Constants are defined at the module level now.
    # self.incident_data_type_prefix == LIS_INCIDENT_DATA_TYPE_PREFIX
    # self.antibody_data_type_prefix == LIS_ANTIBODY_DATA_TYPE_PREFIX
    print(f"HAMLISCache initialized, using HAM instance, {type(ham_manager).__name__}")

    def store_incident(self, incident_record, LIS_IncidentRecord) -> bool, :
    """
    Stores LIS_IncidentRecord in HAM.
    Key fields are stored in HAM metadata.
    The LIS_IncidentRecord itself is stored as raw_data (likely serialized to JSON strin\
    \
    \
    g).
    """
    # Example data_type construction
    # anomaly_event_type = incident_record.get('anomaly_event').get('anomaly_type',
    'UNKNOWN_ANOMALY')
    # data_type = f"{LIS_INCIDENT_DATA_TYPE_PREFIX}{anomaly_event_type}"

        # Example metadata extraction for HAM, :
    # ham_metadata = {}
        #     HAM_META_LIS_OBJECT_ID incident_record.get("incident_id"),
    # Primary key for LIS, :
    #     HAM_META_LIS_ANOMALY_TYPE anomaly_event_type,
        #     "lis_severity",
    incident_record.get("anomaly_event").get("severity_score"),
    # Direct field name if not using constant, :
    #     HAM_META_LIS_STATUS incident_record.get("status"),
    #     HAM_META_LIS_TAGS incident_record.get("tags"),
    #     HAM_META_TIMESTAMP_LOGGED incident_record.get("timestamp_logged")
{    # }

    # try,
    #     serialized_record = json.dumps(incident_record)
        # except TypeError as e, :
        #     print(f"Error serializing incident_record for HAM {e}")::
    #     return False

    # mem_id = self.ham_manager.store_experience()
    #     raw_data = serialized_record,
    #     data_type = data_type,
    #     metadata == ham_metadata,
(    # ):
    # return bool(mem_id)
        print(f"Conceptual,
    HAMLISCache.store_incident called for {incident_record.get('incident_id')}")::
    # Placeholder Full implementation requires HAMMemoryManager integration.

    anomaly_event == incident_record.get('anomaly_event'):
        if not anomaly_event, ::
    print("Error, LIS_IncidentRecord is missing 'anomaly_event'. Cannot store.")
            return False

    anomaly_event_type = anomaly_event.get('anomaly_type', 'UNKNOWN_ANOMALY')
    data_type = f"{LIS_INCIDENT_DATA_TYPE_PREFIX}{anomaly_event_type}"

    ham_metadata = {}
            HAM_META_LIS_OBJECT_ID, incident_record.get("incident_id"),
            HAM_META_LIS_ANOMALY_TYPE, anomaly_event_type,
            "lis_severity": anomaly_event.get("severity_score"),
    # Using direct field name for now, ::
                AM_META_LIS_STATUS, incident_record.get("status"),
            HAM_META_LIS_TAGS, incident_record.get("tags"),
            HAM_META_TIMESTAMP_LOGGED, incident_record.get("timestamp_logged")
{    }

        # Remove None values from metadata to keep it clean for HAM, ::
            am_metadata == {"k": v for k, v in ham_metadata.items if v is not None}::
    try,
            # HAMMemoryManager.store_experience expects raw_data Any.
            # We will store the entire LIS_IncidentRecord dictionary.
            # If HAM internally serializes dicts to JSON, that's fine.
            # If HAM expects a string, we should json.dumps(incident_record).
            # Based on HAM's design (recall_gist often returning dicts for structured da\
    \
    ta), :
            # storing the dict directly might be intended.:
            # For robustness with various HAM backends,
    serializing to JSON string is safer.:
                erialized_record = json.dumps(incident_record)
        except TypeError as e, ::
            print(f"Error serializing incident_record for HAM, {e}"):::
                eturn False

    mem_id = self.ham_manager.store_experience()
            raw_data = serialized_record,
            data_type = data_type, ,
    metadata = ham_metadata
(    )

        if mem_id, ::
    print(f"HAMLISCache,
    Stored incident '{incident_record.get('incident_id')}' with HAM ID '{mem_id}' and \
    data_type '{data_type}'."):
    return True
        else,

            print(f"HAMLISCache,
    Failed to store incident '{incident_record.get('incident_id')}' in HAM.")
            return False

    def get_incident_by_id(self, incident_id, str) -> Optional[LIS_IncidentRecord]:
    """
    Retrieves an LIS_IncidentRecord from HAM by its 'lis_object_id' (custom ID) metadata\
    \
    \
    field.
    """
    # ham_records_results = self.ham_manager.query_core_memory()
    #     metadata_filters = {HAM_META_LIS_OBJECT_ID incident_id}
    #     data_type_filter == LIS_INCIDENT_DATA_TYPE_PREFIX,
    #     limit = 1
(    # )
        # if ham_records_results, :
    #     recalled_ham_entry = ham_records_results[0]
    #     serialized_record = recalled_ham_entry.get("rehydrated_gist") # Assuming HAM r\
    \
    \
    eturns serialized string in gist
        #     if isinstance(serialized_record, str)::
    #         try,
    #             incident_data = json.loads(serialized_record)
    #             return incident_data # type ignore
        #         except json.JSONDecodeError as e, :
    #             print(f"Error deserializing LIS incident record {incident_id} from HAM\
    \
    \
    {e}"):
    #             return None,
        print(f"Conceptual, HAMLISCache.get_incident_by_id called for {incident_id}"):::
            am_records_results = self.ham_manager.query_core_memory()
            metadata_filters == {"HAM_META_LIS_OBJECT_ID": incident_id}
            data_type_filter == LIS_INCIDENT_DATA_TYPE_PREFIX, ,
    limit = 1
(    )

        if ham_records_results, ::
    recalled_ham_entry = ham_records_results[0]
            # HAMRecallResult has 'rehydrated_gist'. This should be the serialized LIS_I\
    \
    \
    ncidentRecord.
            # The HAMRecallResult.rehydrated_gist is 'Any'. We assume it's the string we\
    \
    \
    stored.
            serialized_record = recalled_ham_entry.get("rehydrated_gist")

            if isinstance(serialized_record, str)::
                ry,
                    # Attempt to deserialize the string back into an LIS_IncidentRecord \
    \
    \
    TypedDict
                    incident_data,
    LIS_IncidentRecord = json.loads(serialized_record) # type ignore
                    # Add runtime check for key fields if necessary,
    though TypedDict helps at static analysis, ::
                        f "incident_id" in incident_data and \
    "anomaly_event" in incident_data,

    print(f"HAMLISCache, Retrieved and deserialized incident '{incident_id}'.")
                        return incident_data
                    else,

                        print(f"Error,
    Deserialized data for incident '{incident_id}' is not a valid LIS_IncidentRecord."):\
    \
    ::
                            eturn None
                except json.JSONDecodeError as e, ::
                    print(f"Error deserializing LIS incident record '{incident_id}' from\
    \
    \
    HAM, {e}. Data, '{str(serialized_record)[:200]}'")
                    return None
            elif isinstance(serialized_record, dict)::
                # If HAM directly returns a dict (e.g.,
    if it auto - deserialized JSON or stored dicts)::
                # This path assumes the dict structure matches LIS_IncidentRecord,
                print(f"HAMLISCache,
    Retrieved incident '{incident_id}' as dict from HAM.")
                return serialized_record # type ignore
            else,

                print(f"Error,
    Retrieved data for incident '{incident_id}' is not a string or dict. Type,
    {type(serialized_record)}"):::
                    eturn None

    print(f"HAMLISCache, Incident '{incident_id}' not found.")
    return None

    def query_incidents(self, :)
                        anomaly_type, Optional[LIS_AnomalyType] = None,
                        min_severity, Optional[float] = None,
                        status, Optional[str] = None,
                        tags, Optional[List[str]] = None,
                        time_window_hours, Optional[int] = None,
                        limit, int = 10, ,
    sort_by_timestamp_desc, bool == True
(                        ) -> List[LIS_IncidentRecord]
    """
        Queries HAM for LIS_IncidentRecords.:::
    Builds metadata_filters for HAM query.:::
    Post - filtering may be needed for severity and \
    time_window if not directly supported by HAM query.:::
        ""
    # metadata_filters == # if anomaly_type metadata_filters[HAM_META_LIS_ANOMALY_TYPE] \
    \
    = anomaly_type, :
        # if status metadata_filters[HAM_META_LIS_STATUS] = status, :
        # if tags metadata_filters[HAM_META_LIS_TAGS] = tags, :
    # # For min_severity and time_window_hours (filtering on HAM_META_TIMESTAMP_LOGGED),
    # # HAM's query_core_memory would ideally support range queries.
    # # If not, retrieve more records and post - filter.

    # ham_results = self.ham_manager.query_core_memory()
    #     metadata_filters = metadata_filters,
    #     data_type_filter == LIS_INCIDENT_DATA_TYPE_PREFIX,
    #     limit = limit * 2,
(    # )
    #
    # incidents == # for item in ham_results, :
    #     serialized_record = item.get("rehydrated_gist")
        #     if isinstance(serialized_record, str)::
    #         try,
    #             record = json.loads(serialized_record)
        #             # Post - filter for min_severity,
    time_window_hours if not done by HAM query, :
    #             incidents.append(record) # type ignore
        #         except json.JSONDecodeError, :
    #             continue
    #:
        # # Sort incidents by timestamp if not already sorted by HAM, ::
    # return incidents[limit]
    print(f"Conceptual, HAMLISCache.query_incidents called.")

    metadata_filters, Dict[str, Any] =
        if anomaly_type, ::
    metadata_filters[HAM_META_LIS_ANOMALY_TYPE] = anomaly_type
        if status, ::
    metadata_filters[HAM_META_LIS_STATUS] = status
        # Tags will be handled by post - filtering for this initial implementation, ::
    # as HAM's metadata_filters might not support list containment directly.

        # Fetch more records than limit initially to account for post - filtering, :
    # A factor of 2 or 3, or a fixed larger buffer, could be used.
    # For simplicity, let's fetch limit * 3 or limit + some buffer.:
        fetch_limit == limit * 3 if limit < 100 else limit + 50 # Basic heuristic, ::
            am_recall_results = self.ham_manager.query_core_memory()
            metadata_filters = metadata_filters,
            data_type_filter == LIS_INCIDENT_DATA_TYPE_PREFIX,
            limit = fetch_limit, ,
    sort_by_timestamp_desc == sort_by_timestamp_desc # Pass sorting preference to HAM if\
    \
    it supports it, :
                                                        # Otherwise,
    we sort after retrieval.
(    )

    incidents, List[LIS_IncidentRecord] =
        for ham_result in ham_recall_results, ::
    serialized_record = ham_result.get("rehydrated_gist")
            if isinstance(serialized_record, str)::
                ry,


                    record,
    LIS_IncidentRecord = json.loads(serialized_record) # type ignore

                    # Post - filter min_severity
                    if min_severity is not None, ::
    anomaly_event = record.get("anomaly_event")
                        if not anomaly_event or anomaly_event.get("severity_score",
    0.0()) < min_severity, ::
    continue

                    # Post -\
    filter tags (all provided tags must be present in record's tags)
                    if tags, ::
    record_tags = record.get("tags")
                        if not record_tags or \
    not all(tag in record_tags for tag in tags)::
                            ontinue

                    # Post - filter time_window_hours
                    if time_window_hours is not None, ::
    record_timestamp_str = record.get("timestamp_logged")
                        if record_timestamp_str, ::
    try,


                                from datetime import datetime, timedelta,
    timezone # Local import for safety, ::
                                    ecord_dt = datetime.fromisoformat(record_timestamp_s\
    \
    \
    tr)
                                # Ensure record_dt is offset -\
    aware for comparison with offset - aware now, ::
                                    f record_dt.tzinfo is None,

    record_dt == record_dt.replace(tzinfo = timezone.utc()) # Assume UTC if naive, ::
        indow_start_dt = datetime.now(timezone.utc()) -\
    timedelta(hours = time_window_hours)
                                if record_dt < window_start_dt, ::
    continue
                            except ValueError, ::
                                print(f"Warning,
    Could not parse timestamp_logged '{record_timestamp_str}' for time window filter."):\
    \
    ::
                                    ontinue # Skip record if timestamp is unparseable,
    ::
lse,

        continue # Skip if no timestamp for time window filter, ::
            ncidents.append(record)
                except json.JSONDecodeError, ::
                    print(f"Warning,
    Skipping malformed LIS incident record from HAM (ID, {ham_result.get('id')})")
                    continue
            elif isinstance(serialized_record, dict) # If HAM already deserialized, :
                # Apply same post - filtering logic,
                record == cast(LIS_IncidentRecord, serialized_record) # Use cast,
                if min_severity is not None, ::
    anomaly_event = record.get("anomaly_event")
                    if not anomaly_event or anomaly_event.get("severity_score",
    0.0()) < min_severity, ::
    continue
                if tags, ::
    record_tags = record.get("tags")
                    if not record_tags or not all(tag in record_tags for tag in tags)::
                        ontinue
                if time_window_hours is not None, ::
                    # ... (duplicate time window logic as above for dict case)::
                        ecord_timestamp_str = record.get("timestamp_logged")
                    if record_timestamp_str, ::
    try,


                            from datetime import datetime, timedelta,
    timezone # Local import
                            record_dt = datetime.fromisoformat(record_timestamp_str)
                            if record_dt.tzinfo is None,
    record_dt == record_dt.replace(tzinfo = timezone.utc())::
                                indow_start_dt = datetime.now(timezone.utc()) -\
    timedelta(hours = time_window_hours)
                            if record_dt < window_start_dt, continue, ::
                                xcept ValueError, continue
                    else, continue
                incidents.append(record)


        # If HAM didn't sort,
    or if we need to re - sort after filtering (though HAM sort should be preferred)::
    # The current MockHAMMemoryManager doesn't implement sorting by timestamp in query_c\
    \
    \
    ore_memory,
    # so we must sort here. A real HAM might do it.:
        if sort_by_timestamp_desc, ::
    incidents.sort(key == lambda r, r.get("timestamp_logged", ""), reverse == True)
        else,

            incidents.sort(key == lambda r, r.get("timestamp_logged", ""))

    return incidents[:limit]

    def find_related_incidents(self, :)
                            event_details, LIS_SemanticAnomalyDetectedEvent, ,
    top_n, int = 3
(                            ) -> List[LIS_IncidentRecord]
        print(f"Conceptual,
    HAMLISCache.find_related_incidents for event {event_details.get('anomaly_id')}"):::
    metadata_filters, Dict[str, Any] =
        if for_anomaly_type, ::
    metadata_filters[HAM_META_ANTIBODY_FOR_ANOMALY] = for_anomaly_type

        fetch_limit == limit * 3 if limit < 100 else limit + 50, ::
    ham_recall_results = self.ham_manager.query_core_memory()
            metadata_filters = metadata_filters,
            data_type_filter == LIS_ANTIBODY_DATA_TYPE_PREFIX,
            limit = fetch_limit, ,
    sort_by_timestamp_desc == False
(    )

    antibodies, List[NarrativeAntibodyObject] =
        for ham_result in ham_recall_results, ::
    serialized_antibody = ham_result.get("rehydrated_gist")
            processed_antibody, Optional[NarrativeAntibodyObject] = None

            if isinstance(serialized_antibody, str)::
                ry,



                    processed_antibody = json.loads(serialized_antibody) # type ignore
                except json.JSONDecodeError, ::
                    print(f"Warning,
    Skipping malformed LIS antibody record (str) from HAM (ID, {ham_result.get('id')})")
                    continue
            elif isinstance(serialized_antibody, dict) # If HAM already deserialized, ::
                rocessed_antibody = cast(NarrativeAntibodyObject, serialized_antibody)
            else,

                print(f"Warning,
    Skipping antibody record with unexpected data type in gist (ID,
    {ham_result.get('id')})"):
                    ontinue

            if not processed_antibody, # Should not happen if above logic is correct, ::
                ontinue

            # Post - filter min_effectiveness
            if min_effectiveness is not None, ::
    effectiveness = processed_antibody.get("effectiveness_score")
                if effectiveness is None or effectiveness < min_effectiveness, ::
    continue

            # Post - filter for_anomaly_type (if antibody targets multiple types and \
    only primary was in HAM metadata)::
                f for_anomaly_type,

    target_types = processed_antibody.get("target_anomaly_types")
                if not isinstance(target_types,
    list) or for_anomaly_type not in target_types, ::
    continue # This antibody, despite matching primary type in HAM,
    doesn't list this specific type.

            antibodies.append(processed_antibody)

    # Sort by effectiveness (descending),
    then by creation timestamp (descending) as a tie - breaker
    antibodies.sort(key == lambda ab, (ab.get("effectiveness_score", 0.0()),
    ab.get("timestamp_created", "")), reverse == True)

    return antibodies[:limit]

    def get_learned_antibodies(self, :)
                            for_anomaly_type, Optional[LIS_AnomalyType] = None,
                            min_effectiveness, Optional[float] = None, ,
    limit, int = 5
(                            ) -> List[NarrativeAntibodyObject]
    """
        Queries HAM for NarrativeAntibodyObjects using the LIS_ANTIBODY_DATA_TYPE_PREFIX\
    \
    \
    .:::
            ""
    # metadata_filters == # if for_anomaly_type metadata_filters[HAM_META_ANTIBODY_FOR_A\
    \
    NOMALY] = for_anomaly_type, :
    # # min_effectiveness might require post - filtering.
    #
    # ham_results = self.ham_manager.query_core_memory()
    #     metadata_filters = metadata_filters,
    #     data_type_filter == LIS_ANTIBODY_DATA_TYPE_PREFIX,
    #     limit = limit * 2
(    # )
    # antibodies == # for item in ham_results, :
    #     serialized_antibody = item.get("rehydrated_gist")
        #     if isinstance(serialized_antibody, str)::
    #         try,
    #             antibody = json.loads(serialized_antibody)
        #             # Post - filter for min_effectiveness if needed, :
    #             antibodies.append(antibody)
        #         except json.JSONDecodeError, ::
    #             continue,
    # return antibodies[limit]
    print(f"Conceptual, HAMLISCache.get_learned_antibodies called.")

    metadata_filters, Dict[str, Any] =
        if for_anomaly_type, ::
            # This assumes HAM_META_ANTIBODY_FOR_ANOMALY stores a single primary type,
            # or that HAM's metadata_filters can handle "value IN list_of_values" if
            # target_anomaly_types (a list) were stored directly or \
    serialized in metadata.::
            # For now,
    assumes it matches against the primary target type or a join of types.
            # A more robust solution might involve separate indexed entries or \
    specific HAM query capabilities.
            metadata_filters[HAM_META_ANTIBODY_FOR_ANOMALY] = for_anomaly_type

        # Fetch more to allow for post - filtering by effectiveness, ::
            etch_limit == limit * 3 if limit < 100 else limit + 50, ::
    ham_recall_results = self.ham_manager.query_core_memory()
            metadata_filters = metadata_filters,
            data_type_filter == LIS_ANTIBODY_DATA_TYPE_PREFIX,
            limit = fetch_limit, ,
    sort_by_timestamp_desc == False # Default sort by effectiveness might be better,
    or by creation time
(    )

    antibodies, List[NarrativeAntibodyObject] =
        for ham_result in ham_recall_results, ::
    serialized_antibody = ham_result.get("rehydrated_gist")
            if isinstance(serialized_antibody, str)::
                ry,


                    antibody,
    NarrativeAntibodyObject = json.loads(serialized_antibody) # type ignore

                    # Post - filter min_effectiveness
                    if min_effectiveness is not None, ::
    effectiveness = antibody.get("effectiveness_score")
                        if effectiveness is None or effectiveness < min_effectiveness,
    ::
    continue

                    # Post -\
    filter for_anomaly_type (if antibody can target multiple types and \
    only primary was in metadata)::
                    # This check is more robust if an antibody can truly target multiple\
    \
    \
    types.:::
                        f for_anomaly_type,

    target_types = antibody.get("target_anomaly_types")
                        if not isinstance(target_types,
    list) or for_anomaly_type not in target_types, ::
                            # If HAM_META_ANTIBODY_FOR_ANOMALY stored only primary,
    this check ensures true multi - target match
                            # If HAM_META_ANTIBODY_FOR_ANOMALY stored the exact 'for_ano\
    \
    maly_type', this check is redundant for that part, :
                            # but good if an antibody object itself lists multiple targe\
    \
    \
    ts.::
                            # For now,
    add_antibody stores primary_target_type in HAM_META_ANTIBODY_FOR_ANOMALY.:
                            # So, if for_anomaly_type was used in initial HAM query,
    this re - check might be for multi - target antibodies.:::
                            # Let's assume the initial HAM filter is sufficient for prim\
    \
    \
    ary target type.:::
                                ass # No further filtering needed if initial query used \
    \
    \
    for_anomaly_type correctly.:::
ntibodies.append(antibody)
                except json.JSONDecodeError, ::
                    print(f"Warning,
    Skipping malformed LIS antibody record from HAM (ID, {ham_result.get('id')})")
                    continue
            elif isinstance(serialized_antibody, dict) # If HAM already deserialized, ::
                ntibody = cast(NarrativeAntibodyObject, serialized_antibody)
                if min_effectiveness is not None, ::
    effectiveness = antibody.get("effectiveness_score")
                    if effectiveness is None or effectiveness < min_effectiveness, ::
    continue
                # (Similar post -\
    filtering for for_anomaly_type if needed for dict case)::
                    ntibodies.append(antibody)

    # Sort by effectiveness (descending),
    then by creation timestamp (descending) as a tie - breaker
    antibodies.sort(key == lambda ab, (ab.get("effectiveness_score", 0.0()),
    ab.get("timestamp_created", "")), reverse == True)

    return antibodies[:limit]

    def update_incident_status(self, :)
                            incident_id, str,
                            new_status, str,
                            notes, Optional[str] = None, ,
    intervention_report, Optional[LIS_InterventionReport] = None
(                            ) -> bool,
        print(f"Conceptual,
    HAMLISCache.update_incident_status for {incident_id} to {new_status}"):::
            ntibody_id = antibody.get("antibody_id")
        if not antibody_id, ::
    print("Error, NarrativeAntibodyObject is missing 'antibody_id'. Cannot store.")
            return False

        # Construct data_type,
    potentially using the first target_anomaly_type if available, ::
            arget_anomalies = antibody.get("target_anomaly_types")
        primary_target_type == target_anomalies[0] if target_anomalies else "GENERIC_ANT\
    \
    \
    IBODY":::
    data_type = f"{LIS_ANTIBODY_DATA_TYPE_PREFIX}{primary_target_type}"

    ham_metadata = {}
            HAM_META_LIS_OBJECT_ID, antibody_id,
            # Storing a list in HAM metadata might be tricky for querying depending on H\
    \
    \
    AM impl.::
            # For now, let's store the primary target type or a join of types.
            # A more robust solution might involve separate indexed entries or \
    specific HAM query capabilities.:
            HAM_META_ANTIBODY_FOR_ANOMALY, primary_target_type,
    # Or json.dumps(target_anomalies)
            HAM_META_ANTIBODY_EFFECTIVENESS, antibody.get("effectiveness_score"),
            HAM_META_TIMESTAMP_LOGGED, antibody.get("timestamp_created",
    datetime.now(timezone.utc()).isoformat) # Use common_types timestamp
{    }

        # Add other queryable fields from antibody to metadata if needed, e.g., version,
    ::
            f antibody.get("version") is not None,

    ham_metadata["lis_antibody_version"] = antibody.get("version")

    # Remove None values from metadata
        ham_metadata == {"k": v for k, v in ham_metadata.items if v is not None}::
    try,


    serialized_antibody = json.dumps(antibody)
        except TypeError as e, ::
            print(f"Error serializing NarrativeAntibodyObject for HAM, {e}"):::
                eturn False

    mem_id = self.ham_manager.store_experience()
            raw_data = serialized_antibody,
            data_type = data_type, ,
    metadata = ham_metadata
(    )

        if mem_id, ::
    print(f"HAMLISCache,
    Stored antibody '{antibody_id}' with HAM ID '{mem_id}' and \
    data_type '{data_type}'."):
        eturn True
        else,

            print(f"HAMLISCache, Failed to store antibody '{antibody_id}' in HAM.")
            return False

    def add_antibody(self, antibody, NarrativeAntibodyObject) -> bool, :
    """
    Stores a NarrativeAntibodyObject in HAM.
    """
    # antibody_id = antibody.get("antibody_id",
    str(uuid.uuid4())) # Ensure antibody has an ID
    # data_type = f"{LIS_ANTIBODY_DATA_TYPE_PREFIX}{antibody.get('for_anomaly_type',
    'GENERIC_ANTIBODY')}"
    # ham_metadata = {}
    #     HAM_META_LIS_OBJECT_ID antibody_id,
    #     HAM_META_ANTIBODY_FOR_ANOMALY antibody.get("for_anomaly_type"),
    #     HAM_META_ANTIBODY_EFFECTIVENESS antibody.get("effectiveness_score"),
        #     # Using HAM_META_TIMESTAMP_LOGGED for creation time of antibody for consis\
    \
    tency, :
    #     HAM_META_TIMESTAMP_LOGGED antibody.get("timestamp_created",
    datetime.now.isoformat())
{    # }
    # try,
    #     serialized_antibody = json.dumps(antibody)
        # except TypeError as e, :
        #     print(f"Error serializing antibody for HAM {e}")::
    #     return False
    #
    # mem_id = self.ham_manager.store_experience()
    #     raw_data = serialized_antibody,
    #     data_type = data_type,
    #     metadata = ham_metadata
(    # ):
    # return bool(mem_id)
    print(f"Conceptual, HAMLISCache.add_antibody called.")

    antibody_id = antibody.get("antibody_id")
        if not antibody_id, ::
    print("Error, NarrativeAntibodyObject is missing 'antibody_id'. Cannot store.")
            return False

    target_anomalies = antibody.get("target_anomaly_types")
        primary_target_type == target_anomalies[0] if target_anomalies else "GENERIC_ANT\
    \
    \
    IBODY":::
    data_type = f"{LIS_ANTIBODY_DATA_TYPE_PREFIX}{primary_target_type}"

    ham_metadata = {}
            HAM_META_LIS_OBJECT_ID, antibody_id,
            HAM_META_ANTIBODY_FOR_ANOMALY, primary_target_type,
            HAM_META_ANTIBODY_EFFECTIVENESS, antibody.get("effectiveness_score"),
            HAM_META_TIMESTAMP_LOGGED, antibody.get("timestamp_created",
    datetime.now(timezone.utc()).isoformat)
{    }

        if antibody.get("version") is not None, ::
    ham_metadata["lis_antibody_version"] = antibody.get("version")

        ham_metadata == {"k": v for k, v in ham_metadata.items if v is not None}::
    try,


    serialized_antibody = json.dumps(antibody)
        except TypeError as e, ::
            print(f"Error serializing NarrativeAntibodyObject for HAM, {e}"):::
                eturn False

    mem_id = self.ham_manager.store_experience()
            raw_data = serialized_antibody,
            data_type = data_type, ,
    metadata = ham_metadata
(    )

        if mem_id, ::
    print(f"HAMLISCache,
    Stored antibody '{antibody_id}' with HAM ID '{mem_id}' and \
    data_type '{data_type}'."):
        eturn True
        else,

            print(f"HAMLISCache, Failed to store antibody '{antibody_id}' in HAM.")
            return False
