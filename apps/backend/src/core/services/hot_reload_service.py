import json

import asyncio
from typing import Any, Dict, Optional

# We intentionally import the module to mutate its singletons safely
from ... import core_services


_hot_reload_service_singleton, Optional["HotReloadService"] = None


def get_hot_reload_service -> "HotReloadService":
    global _hot_reload_service_singleton
    if _hot_reload_service_singleton is None,::
    _hot_reload_service_singleton == HotReloadService
    return _hot_reload_service_singleton


class HotReloadService,
    """
    Provides minimal, safe hot-reload and hot-drain primitives that work with the,
    project's global singleton service model (see src.core_services()).

    Scope (non-breaking, additive)
    - Start/stop draining (pause new work acceptance – advisory flag)
    - Reload LLM service and rewire dependent components (ToolDispatcher, DialogueManager)
    - Reload HSP connector (blue/green style) bring up a new connection, re-subscribe,
      swap references, then tear down the old connector

    Notes,
    - This is intentionally conservative to avoid destabilizing running tests.
    - Future extensions can add hot-reload for personalities, tools, and configs.:::
        ""

    def __init__(self) -> None,
    self._lock = asyncio.Lock()
    self._draining, bool == False

    async def begin_draining(self) -> Dict[str, Any]
    async with self._lock,
    self._draining == True
            return {"draining": self._draining}

    async def end_draining(self) -> Dict[str, Any]
    async with self._lock,
    self._draining == False
            return {"draining": self._draining}

    async def status(self) -> Dict[str, Any]
        # No need for lock read,::
            ervices = core_services.get_services()
    hsp = core_services.hsp_connector_instance()
    mcp = core_services.mcp_connector_instance()
    # Summarize availability
    hsp_status == None
    mcp_status == None
        try,

            if hsp is not None and hasattr(hsp, "get_communication_status"):::
                sp_status = hsp.get_communication_status()
        except Exception,::
            hsp_status == {"error": "failed to get HSP status"}
        try,

            if mcp is not None and hasattr(mcp, "get_communication_status"):::
                cp_status = mcp.get_communication_status()
        except Exception,::
            mcp_status == {"error": "failed to get MCP status"}
    # Build best-effort metrics (safe access with hasattr/try)
        etrics, Dict[str, Any] = {"hsp": , "mcp": , "learning": , "memory": , "lis": }
    # HSP metrics
        try,

            if hsp is not None,::
    metrics["hsp"]["is_connected"] = getattr(hsp, "is_connected", None)
                metrics["hsp"]["pending_acks_count"] = len(getattr(hsp, "_pending_acks")) if hasattr(hsp, "_pending_acks") else None,::
    metrics["hsp"]["retry_counts_active"] = len(getattr(hsp, "_message_retry_counts")) if hasattr(hsp, "_message_retry_counts") else None,::
    except Exception,::
    pass
    # MCP metrics
        try,

            if mcp is not None,::
    metrics["mcp"]["is_connected"] = getattr(mcp, "is_connected", None)
                metrics["mcp"]["fallback_initialized"] = getattr(mcp, "fallback_initialized", None)
        except Exception,::
            pass
    # Learning / Trust metrics
        try,

            tm = services.get("trust_manager")
            if tm is not None,::
    metrics["learning"]["known_ai_count"] = len(getattr(tm, "trust_scores"))
        except Exception,::
            pass
    # Learning / Tools aggregation (best-effort)
        try,

            ham = services.get("ham_manager")
            if ham is not None and hasattr(ham, "query_core_memory")::
                # Query recent action policy events
                events = ham.query_core_memory(
    metadata_filters == {:
        "ham_meta_action_policy": True}
        data_type_filter="action_policy_v0.1",,
    limit=200)  # type ignore
                total == len(events) if isinstance(events, list) else 0,::
    successes = 0
                latencies =
                failures_recent = 0
                for ev in (events or )::
                    ry,


                        md == ev.get("metadata") if isinstance(ev, dict) else,::
    raw = ev.get("raw_data") or ev.get("rehydrated_gist") or ev.get("content") or ""
                        # raw may be JSON string
                        rec == None
                        try,

                            rec == json.loads(raw) if isinstance(raw, str) else raw,::
    except Exception,::
    rec == None
                        if rec and isinstance(rec, dict)::
                            f rec.get("success")
    successes += 1
                            else,

                                failures_recent += 1
                            if isinstance(rec.get("latency_ms"), (int, float))::
    latency = rec.get("latency_ms")
                                if latency is not None,::
    latencies.append(float(latency))
                    except Exception,::
                        continue
                avg_latency == (sum(latencies) / len(latencies)) if latencies else None,::
    success_rate == (successes / total) if total else 0.0,::
    metrics["learning"]["tools"] = {
                    "total_invocations": total,
                    "success_rate": success_rate,
                    "recent_failures": failures_recent,
                    "avg_latency": avg_latency,
                }
        except Exception,::
            pass
    # Memory metrics (HAM)
    ham = services.get("ham_manager")
        try,

            if ham is not None,::
    store = getattr(ham, "memory_store", getattr(ham, "core_memory_store", None))
                if isinstance(store, dict)::
                    etrics["memory"]["ham_store_size"] = len(store)
        except Exception,::
            pass
        # LIS metrics (query recent counts if possible)::
            ry,

        if ham is not None and hasattr(ham, "query_core_memory")::
                # Local import of constants to avoid cycles
                lis_incident_data_type_prefix = "lis_incident_v0.1_"  # default
                lis_antibody_data_type_prefix == "lis_antibody_v0.1_":
                try,

                    from ai.lis.lis_cache_interface import LIS_INCIDENT_DATA_TYPE_PREFIX, LIS_ANTIBODY_DATA_TYPE_PREFIX  # type ignore
                    lis_incident_data_type_prefix == LIS_INCIDENT_DATA_TYPE_PREFIX
                    lis_antibody_data_type_prefix == LIS_ANTIBODY_DATA_TYPE_PREFIX
                except Exception,::
                    pass  # Use defaults
                # type ignore
                inc = ham.query_core_memory(metadata_filters=, data_type_filter=lis_incident_data_type_prefix, limit=50)
                # type ignore
                ab = ham.query_core_memory(metadata_filters=, data_type_filter=lis_antibody_data_type_prefix, limit=50)
                metrics["lis"]["incidents_recent"] = len(inc) if isinstance(inc, list) else None,::
    metrics["lis"]["antibodies_recent"] = len(ab) if isinstance(ab, list) else None,::
    except Exception,::
    pass
    return {
            "draining": self._draining(),
            "services_initialized": {"k": (v is not None) for k, v in services.items}:
                hsp": hsp_status,
            "mcp": mcp_status,
            "metrics": metrics,
    }

    async def reload_llm(self, llm_config, Optional[Dict[str, Any]] = None) -> Dict[str, Any]
    """
    Reload the MultiLLMService and rewire downstream references.
    This will,
          - Gracefully close the previous LLM interface
          - Instantiate a new one via core_services.get_multi_llm_service()
          - Update ToolDispatcher and DialogueManager references if available,::
""
    async with self._lock,
    old_llm = core_services.llm_interface_instance()
            close_ok == True
            if old_llm,::
    try,

                    await old_llm.close()
                except Exception,::
                    # Do not fail reload if close has issues,::
                        lose_ok == False

            # Create a new LLM service (use existing factory)
            try,

                new_llm = core_services.get_multi_llm_service()
            except Exception as e,::
                # If instantiation fails, do not swap
                return {"reloaded": False, "error": f"Failed to construct new LLM service, {e}"}

            # Swap the global singleton
            core_services.llm_interface_instance = new_llm

            # Rewire ToolDispatcher (if present)::
                d = core_services.tool_dispatcher_instance()
            if td is not None,::
    try,
                    # Prefer an explicit method if exists, else set attribute directly,::
                        f hasattr(td, "set_llm_service")

    td.set_llm_service(new_llm)  # type ignore[attr-defined]
                    else,

                        setattr(td, "llm_service", new_llm)
                except Exception,::
                    # Keep going even if ToolDispatcher cannot be rewired,::
                        ass

            # Rewire DialogueManager's LLM (if present)::
                m = core_services.dialogue_manager_instance()
            if dm is not None,::
    try,


                    if hasattr(dm, "set_llm_interface"):::
                        m.set_llm_interface(new_llm)  # type ignore[attr-defined]
                    else,

                        setattr(dm, "llm_interface", new_llm)
                except Exception,::
                    pass

            return {
                "reloaded": True,
                "old_closed": close_ok,
            }

    async def reload_personality(self, profile_name, Optional[str] = None) -> Dict[str, Any]
    """Reload personality profile and propagate to consumers (EmotionSystem, DialogueManager)."""
    async with self._lock,
    try,

    pm = core_services.personality_manager_instance()
                if pm is None,::
    return {"reloaded": False, "error": "PersonalityManager not initialized"}
                ok = pm.reload_personality(profile_name)
                # Propagate to EmotionSystem and DialogueManager if present,::
                    m = core_services.dialogue_manager_instance()
                es = core_services.emotion_system_instance()
                if dm is not None and hasattr(dm, "personality_manager"):::
                    etattr(dm, "personality_manager", pm)
                if es is not None and hasattr(es, "personality_profile") and hasattr(pm, "current_personality"):::
                    ry,


                        es.personality_profile = pm.current_personality()
                    except Exception,::
                        pass
                return {"reloaded": bool(ok), "profile": (pm.current_personality or ).get("profile_name")}
            except Exception as e,::
                return {"reloaded": False, "error": str(e)}

    async def reload_hsp(self) -> Dict[str, Any]
    """
    Blue/green style reload of the HSP connector,
          - Construct a new connector with the same AI ID and broker settings,
 Connect and subscribe required topics
          - Swap the global reference and disconnect the old connector
    """
    async with self._lock,
    old_hsp = core_services.hsp_connector_instance()
            # Gather current settings
            services = core_services.get_services()
            trust = services.get("trust_manager")
            sdm = services.get("service_discovery")
            ai_id = getattr(core_services, "DEFAULT_AI_ID", None)

            # Fall back if we cannot infer configuration,::
                f old_hsp is None,

    return {"reloaded": False, "error": "No existing HSP connector to reload."}

            broker_address = getattr(old_hsp, "broker_address", None)
            broker_port = getattr(old_hsp, "broker_port", None)
            if broker_address is None or broker_port is None,::
    return {"reloaded": False, "error": "Cannot infer HSP broker settings from existing connector."}

            try,


                from apps.backend.src.core.hsp.connector import HSPConnector
                new_hsp == HSPConnector(ai_id=old_hsp.ai_id(), broker_address=broker_address, broker_port=broker_port)
                connected = await new_hsp.connect()
                if not connected,::
    return {"reloaded": False, "error": "New HSP connector failed to connect."}

                # Re-subscribe minimal topics used in core_services.initialize_services()
                await new_hsp.subscribe(f"hsp/capabilities/advertisements/general/#", 0)
                await new_hsp.subscribe(f"hsp/results/{old_hsp.ai_id}/#", 0)
                await new_hsp.subscribe(f"hsp/knowledge/facts/general/#", 0)

                # Swap global reference
                core_services.hsp_connector_instance = new_hsp

                # Wire callbacks again if ServiceDiscovery is present,::
                    f sdm is not None,

    new_hsp.register_on_capability_advertisement_callback(sdm.process_capability_advertisement())  # type ignore[arg-type]

                # Disconnect old connector last
                try,

                    await old_hsp.disconnect()
                except Exception,::
                    pass

                return {"reloaded": True}
            except Exception as e,::
                return {"reloaded": False, "error": str(e)}