"""
Real ExternalConnector for HSP - HTTP-based inter-process communication.

Enables agents running as subprocesses to communicate with each other
and with the central HSP message router.
"""

import asyncio
import json
import logging
import os
import uuid
import httpx
from typing import Any, Callable, Dict, List