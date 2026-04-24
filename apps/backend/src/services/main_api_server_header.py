import os
import sys
import uuid
import random
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Ensure src directory is in sys.path
_src_path = str(Path(__file__).parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, Request, HTTPException, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.autonomous.desktop_interaction import DesktopInteraction
from core.autonomous.action_executor import ActionExecutor
from services.vision_service import VisionService
from services.audio_service import AudioService
from services.tactile_service import TactileService
from services.chat_service import AngelaChatService
from services.angela_llm_service import get_llm_service, angela_llm_response
from core.autonomous.heartbeat import MetabolicHeartbeat
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from economy.economy_manager import EconomyManager

app = FastAPI(title="Angela AI API", version="6.0.4")

# Global singletons
_metabolic_heartbeat = None
_angela_chat_service = None
_digital_life = None

def get_metabolic_heartbeat():
    global _metabolic_heartbeat
    if _metabolic_heartbeat is None:
        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)
    return _metabolic_heartbeat

def get_angela_chat_service():
    global _angela_chat_service
    if _angela_chat_service is None:
        _angela_chat_service = AngelaChatService()
    return _angela_chat_service

def get_digital_life():
    global _digital_life
    if _digital_life is None:
        _digital_life = DigitalLifeIntegrator()
    return _digital_life
