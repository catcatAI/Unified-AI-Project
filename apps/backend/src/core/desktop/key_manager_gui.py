"""
Key Manager GUI - Cross-Platform API Key Management

A simple GUI for managing Angela AI API keys.
Supports: Environment variables, .env files, config files

Features:
- View configured keys (without exposing values)
- Add/Update keys
- Switch between storage methods
- Security warnings
- Privacy protection (never displays actual key values)

Requirements: tkinter (built-in)
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict