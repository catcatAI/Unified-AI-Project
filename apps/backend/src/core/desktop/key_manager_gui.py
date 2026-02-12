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
from typing import Dict, Optional, List
import json
import logging
logger = logging.getLogger(__name__)


class KeyManagerGUI:
    """Key Manager GUI Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔑 Angela AI - API Key Manager")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # Try to set icon
        try:
            icon_path = Path(__file__).parent.parent.parent.parent / "resources" / "angela_icon.png"
            try:
                from PIL import Image, ImageTk
                icon = Image.open(icon_path)
                icon = icon.resize((32, 32))
                photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, photo)
            except (FileNotFoundError, ImportError, OSError) as e:
                # 圖標加載失敗，使用默認圖標
                logger.debug(f"圖標加載失敗（可忽略）: {e}")
                pass
        except Exception as e:
            logger.debug(f"圖標路徑解析失敗（可忽略）: {e}")
            pass
        
        # Providers configuration
        self.providers = {
            'openai': {
                'name': 'OpenAI',
                'env_var': 'OPENAI_API_KEY',
                'icon': '🤖',
                'description': 'GPT-3.5, GPT-4, GPT-4o models',
                'required': True
            },
            'anthropic': {
                'name': 'Anthropic',
                'env_var': 'ANTHROPIC_API_KEY',
                'icon': '🧠',
                'description': 'Claude 3 models (Haiku, Sonnet, Opus)',
                'required': False
            },
            'google': {
                'name': 'Google',
                'env_var': 'GEMINI_API_KEY',
                'icon': '🔍',
                'description': 'Gemini 1.5 Pro/Flash models',
                'required': False
            },
            'azure_openai': {
                'name': 'Azure OpenAI',
                'env_var': 'AZURE_OPENAI_API_KEY',
                'icon': '☁️',
                'description': 'Azure-hosted OpenAI models',
                'required': False
            },
            'cohere': {
                'name': 'Cohere',
                'env_var': 'COHERE_API_KEY',
                'icon': '📝',
                'description': 'Cohere Command models',
                'required': False
            },
            'huggingface': {
                'name': 'Hugging Face',
                'env_var': 'HUGGINGFACE_API_KEY',
                'icon': '🤗',
                'description': 'HF Inference API',
                'required': False
            },
            'ollama': {
                'name': 'Ollama (Local)',
                'env_var': 'OLLAMA_HOST',
                'icon': '🦙',
                'description': 'Local Ollama server (default: http://localhost:11434)',
                'required': False,
                'default_value': 'http://localhost:11434'
            },
            'llamacpp': {
                'name': 'llama.cpp (Local)',
                'env_var': 'LLAMACPP_BASE_URL',
                'icon': '🦙',
                'description': 'Local llama.cpp server (default: http://localhost:8080)',
                'required': False,
                'default_value': 'http://localhost:8080'
            }
        }
        
        # Current key status
        self.key_status: Dict[str, Dict] = {}
        self.env_vars = {}
        
        self._scan_keys()
        self._create_widgets()
        self._refresh_display()
    
    def _scan_keys(self):
        """Scan for existing keys in all sources"""
        # Load .env file
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
        except ImportError:
            pass
        
        for provider_id, config in self.providers.items():
            env_var = config['env_var']
            
            # Check environment variable
            value = os.getenv(env_var)
            if value:
                self.key_status[provider_id] = {
                    'configured': True,
                    'source': f'Environment Variable ({env_var})',
                    'secure': True,
                    'warning': None
                }
                self.env_vars[env_var] = value
            else:
                self.key_status[provider_id] = {
                    'configured': False,
                    'source': None,
                    'secure': False,
                    'warning': f'Not configured. Set {env_var} environment variable.'
                }
        
        # Also check config file
        self._check_config_file()
    
    def _check_config_file(self):
        """Check for keys in config file"""
        config_paths = [
            Path(__file__).parent.parent.parent.parent / "configs" / "api_keys.yaml",
            Path(__file__).parent.parent.parent.parent / "configs" / "config.yaml",
            Path.cwd() / "api_keys.yaml"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Check various possible structures
                    models = config.get('models', {})
                    for model_id, model_config in models.items():
                        if isinstance(model_config, dict):
                            provider = model_config.get('provider', '').lower()
                            if provider in self.providers:
                                if not self.key_status[provider]['configured']:
                                    self.key_status[provider] = {
                                        'configured': True,
                                        'source': f'Config File ({config_path.name})',
                                        'secure': False,
                                        'warning': f'Key found in config file. For better security, move to environment variable.'
                                    }
                except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                    # 配置文件讀取失敗，跳過
                    logger.debug(f"配置文件讀取失敗（可忽略）: {e}")
                    pass
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Title
        title_frame = tk.Frame(self.root, padx=20, pady=10)
        title_frame.pack(fill='x')
        
        tk.Label(
            title_frame,
            text="🔑 API Key Manager",
            font=('Arial', 20, 'bold')
        ).pack(anchor='w')
        
        tk.Label(
            title_frame,
            text="Manage your API keys securely. Keys are never displayed on screen.",
            font=('Arial', 10),
            fg='gray'
        ).pack(anchor='w', pady=(5, 0))
        
        # Security notice
        security_frame = tk.Frame(self.root, bg='#fff3cd', padx=20, pady=10)
        security_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            security_frame,
            text="🔒 Security Notice:",
            font=('Arial', 11, 'bold'),
            bg='#fff3cd',
            fg='#856404'
        ).pack(anchor='w')
        
        tk.Label(
            security_frame,
            text="• Environment variables are the most secure option\n"
                 "• This tool only shows whether keys are configured, not the actual values\n"
                 "• Never commit API keys to version control",
            font=('Arial', 9),
            bg='#fff3cd',
            fg='#856404',
            justify='left'
        ).pack(anchor='w', pady=(5, 0))
        
        # Main content frame
        content_frame = tk.Frame(self.root, padx=20, pady=10)
        content_frame.pack(fill='both', expand=True)
        
        # Provider list
        self.provider_frame = tk.LabelFrame(
            content_frame,
            text="API Providers",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        self.provider_frame.pack(fill='both', expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(self.provider_frame)
        scrollbar = ttk.Scrollbar(self.provider_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        button_frame = tk.Frame(self.root, padx=20, pady=15)
        button_frame.pack(fill='x', side='bottom')
        
        tk.Button(
            button_frame,
            text="➕ Add New Key",
            command=self._add_key_dialog,
            font=('Arial', 11),
            bg='#28a745',
            fg='white',
            padx=20,
            pady=8
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="🔄 Refresh",
            command=self._refresh_display,
            font=('Arial', 11),
            padx=20,
            pady=8
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="📖 Help",
            command=self._show_help,
            font=('Arial', 11),
            padx=20,
            pady=8
        ).pack(side='left')
        
        tk.Button(
            button_frame,
            text="Close",
            command=self.root.destroy,
            font=('Arial', 11),
            padx=20,
            pady=8
        ).pack(side='right')
    
    def _refresh_display(self):
        """Refresh the provider display"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Re-scan keys
        self._scan_keys()
        
        # Create provider entries
        for i, (provider_id, config) in enumerate(self.providers.items()):
            self._create_provider_row(i, provider_id, config)
    
    def _create_provider_row(self, index: int, provider_id: str, config: Dict):
        """Create a row for a provider"""
        row = tk.Frame(self.scrollable_frame, padx=5, pady=5)
        row.pack(fill='x', pady=2)
        
        # Alternating background
        if index % 2 == 0:
            row.configure(bg='#f8f9fa')
        else:
            row.configure(bg='white')
        
        # Icon and name
        icon_label = tk.Label(
            row,
            text=config['icon'],
            font=('Arial', 20),
            bg=row['bg']
        )
        icon_label.pack(side='left', padx=(0, 10))
        
        # Info frame
        info_frame = tk.Frame(row, bg=row['bg'])
        info_frame.pack(side='left', fill='x', expand=True)
        
        # Name
        name_text = config['name']
        if config.get('required'):
            name_text += ' *'
        
        tk.Label(
            info_frame,
            text=name_text,
            font=('Arial', 12, 'bold'),
            bg=row['bg']
        ).pack(anchor='w')
        
        # Description
        tk.Label(
            info_frame,
            text=config['description'],
            font=('Arial', 9),
            fg='gray',
            bg=row['bg']
        ).pack(anchor='w')
        
        # Status frame
        status_frame = tk.Frame(row, bg=row['bg'])
        status_frame.pack(side='right', padx=(10, 0))
        
        status = self.key_status[provider_id]
        
        if status['configured']:
            # Configured - show checkmark
            tk.Label(
                status_frame,
                text='✅ Configured',
                font=('Arial', 10),
                fg='green',
                bg=row['bg']
            ).pack(anchor='e')
            
            # Source
            source_text = status['source']
            if not status['secure']:
                source_text += ' ⚠️'
            
            tk.Label(
                status_frame,
                text=source_text,
                font=('Arial', 8),
                fg='orange' if not status['secure'] else 'green',
                bg=row['bg']
            ).pack(anchor='e')
            
            # Warning if any
            if status.get('warning'):
                tk.Label(
                    status_frame,
                    text=status['warning'][:50] + '...' if len(status['warning']) > 50 else status['warning'],
                    font=('Arial', 8),
                    fg='red',
                    bg=row['bg'],
                    wraplength=250
                ).pack(anchor='e')
        else:
            # Not configured
            tk.Label(
                status_frame,
                text='❌ Not Configured',
                font=('Arial', 10),
                fg='red',
                bg=row['bg']
            ).pack(anchor='e')
            
            if status.get('warning'):
                tk.Label(
                    status_frame,
                    text=status['warning'][:50] + '...',
                    font=('Arial', 8),
                    fg='orange',
                    bg=row['bg']
                ).pack(anchor='e')
        
        # Buttons
        btn_frame = tk.Frame(row, bg=row['bg'])
        btn_frame.pack(side='right', padx=(10, 0))
        
        if status['configured']:
            tk.Button(
                btn_frame,
                text='Edit',
                command=lambda p=provider_id: self._edit_key_dialog(p),
                font=('Arial', 9)
            ).pack(side='left', padx=(0, 5))
            
            tk.Button(
                btn_frame,
                text='Remove',
                command=lambda p=provider_id: self._remove_key(p),
                font=('Arial', 9),
                fg='red'
            ).pack(side='left')
        else:
            tk.Button(
                btn_frame,
                text='Add Key',
                command=lambda p=provider_id: self._edit_key_dialog(p),
                font=('Arial', 9),
                bg='#28a745',
                fg='white'
            ).pack(side='left')
    
    def _add_key_dialog(self):
        """Open dialog to add a new key"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add API Key")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Select Provider:",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        # Provider selection
        provider_var = tk.StringVar()
        provider_combo = ttk.Combobox(
            dialog,
            textvariable=provider_var,
            values=[f"{c['icon']} {c['name']}" for c in self.providers.values()],
            state='readonly',
            font=('Arial', 11)
        )
        provider_combo.pack(pady=5, padx=20, fill='x')
        provider_combo.current(0)
        
        # Key entry
        tk.Label(
            dialog,
            text="API Key:",
            font=('Arial', 12, 'bold')
        ).pack(pady=(20, 5))
        
        key_entry = tk.Entry(dialog, font=('Arial', 11), show='•', width=50)
        key_entry.pack(pady=5, padx=20)
        
        # Show/hide toggle
        show_var = tk.BooleanVar()
        tk.Checkbutton(
            dialog,
            text="Show key",
            variable=show_var,
            command=lambda: key_entry.configure(show='' if show_var.get() else '•')
        ).pack()
        
        # Storage method
        tk.Label(
            dialog,
            text="Storage Method:",
            font=('Arial', 12, 'bold')
        ).pack(pady=(20, 5))
        
        storage_var = tk.StringVar(value='env')
        tk.Radiobutton(
            dialog,
            text="Environment Variable (Recommended - Most Secure)",
            variable=storage_var,
            value='env'
        ).pack(anchor='w', padx=20)
        tk.Radiobutton(
            dialog,
            text=".env File",
            variable=storage_var,
            value='dotenv'
        ).pack(anchor='w', padx=20)
        
        # Buttons
        btn_frame = tk.Frame(dialog, pady=20)
        btn_frame.pack()
        
        def save():
            key = key_entry.get().strip()
            if not key:
                messagebox.showerror("Error", "Please enter an API key")
                return
            
            provider_display = provider_var.get()
            provider_id = None
            for pid, c in self.providers.items():
                if provider_display.endswith(c['name']):
                    provider_id = pid
                    break
            
            if not provider_id:
                return
            
            storage = storage_var.get()
            env_var = self.providers[provider_id]['env_var']
            
            try:
                if storage == 'env':
                    # Try to set environment variable (only for current session)
                    os.environ[env_var] = key
                    
                    # Show instructions for permanent setup
                    msg = f"Key saved to current session.\n\n"
                    msg += f"To make it permanent, add to your system environment:\n"
                    msg += f"{env_var}=sk-...\n\n"
                    msg += f"Or create a .env file with this content."
                    
                    messagebox.showinfo("Key Saved", msg)
                
                elif storage == 'dotenv':
                    # Save to .env file
                    env_path = Path.cwd() / '.env'
                    
                    # Read existing content
                    lines = []
                    if env_path.exists():
                        with open(env_path, 'r') as f:
                            lines = f.readlines()
                    
                    # Remove existing entry if present
                    lines = [l for l in lines if not l.startswith(f"{env_var}=")]
                    
                    # Add new entry
                    lines.append(f"{env_var}={key}\n")
                    
                    # Write back
                    with open(env_path, 'w') as f:
                        f.writelines(lines)
                    
                    messagebox.showinfo("Key Saved", f"Key saved to {env_path}")
                
                dialog.destroy()
                self._refresh_display()
                
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                messagebox.showerror("Error", f"Failed to save key: {e}")

        
        tk.Button(
            btn_frame,
            text="Save",
            command=save,
            font=('Arial', 11),
            bg='#28a745',
            fg='white',
            padx=30
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Arial', 11),
            padx=30
        ).pack(side='left', padx=5)
    
    def _edit_key_dialog(self, provider_id: str):
        """Open dialog to edit an existing key"""
        config = self.providers[provider_id]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {config['name']} Key")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text=f"Edit {config['icon']} {config['name']} API Key",
            font=('Arial', 14, 'bold')
        ).pack(pady=20)
        
        # Current status
        status = self.key_status[provider_id]
        tk.Label(
            dialog,
            text=f"Currently: {status['source']}" if status['configured'] else "Not configured",
            font=('Arial', 10),
            fg='green' if status['configured'] else 'red'
        ).pack()
        
        # New key entry
        tk.Label(
            dialog,
            text="New API Key (leave empty to keep current):",
            font=('Arial', 11)
        ).pack(pady=(20, 5))
        
        key_entry = tk.Entry(dialog, font=('Arial', 11), show='•', width=50)
        key_entry.pack(pady=5, padx=20)
        
        show_var = tk.BooleanVar()
        tk.Checkbutton(
            dialog,
            text="Show key",
            variable=show_var,
            command=lambda: key_entry.configure(show='' if show_var.get() else '•')
        ).pack()
        
        # Buttons
        btn_frame = tk.Frame(dialog, pady=20)
        btn_frame.pack()
        
        def save():
            key = key_entry.get().strip()
            if key:
                # Update key (same logic as add)
                env_var = config['env_var']
                os.environ[env_var] = key
                
                # Also update .env
                env_path = Path.cwd() / '.env'
                lines = []
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                lines = [l for l in lines if not l.startswith(f"{env_var}=")]
                lines.append(f"{env_var}={key}\n")
                with open(env_path, 'w') as f:
                    f.writelines(lines)
                
                messagebox.showinfo("Success", "Key updated successfully!")
            
            dialog.destroy()
            self._refresh_display()
        
        tk.Button(
            btn_frame,
            text="Save",
            command=save,
            font=('Arial', 11),
            bg='#28a745',
            fg='white',
            padx=30
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Arial', 11),
            padx=30
        ).pack(side='left', padx=5)
    
    def _remove_key(self, provider_id: str):
        """Remove a key"""
        config = self.providers[provider_id]
        
        if messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove the {config['name']} key?\n\n"
            f"This will remove it from the current session and .env file."
        ):
            env_var = config['env_var']
            
            # Remove from environment
            if env_var in os.environ:
                del os.environ[env_var]
            
            # Remove from .env
            env_path = Path.cwd() / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                lines = [l for l in lines if not l.startswith(f"{env_var}=")]
                with open(env_path, 'w') as f:
                    f.writelines(lines)
            
            self._refresh_display()
            messagebox.showinfo("Success", f"{config['name']} key removed.")
    
    def _show_help(self):
        """Show help dialog"""
        help_text = """
Angela AI - API Key Manager Help

🔒 Security Best Practices:

1. Environment Variables (Most Secure)
   - Set in your OS or shell profile
   - Never exposed in code or files
   - Example: export OPENAI_API_KEY=sk-...

2. .env File (Good)
   - Stored in local file, not committed
   - Add .env to .gitignore!
   - Easy to manage multiple keys

3. Config File (Acceptable)
   - Stored in YAML/JSON config
   - Less secure, but convenient
   - Never commit to version control!

📝 Setting Environment Variables:

Linux/macOS:
    export OPENAI_API_KEY=sk-...
    export ANTHROPIC_API_KEY=sk-ant-...

Windows (CMD):
    set OPENAI_API_KEY=sk-...

Windows (PowerShell):
    $env:OPENAI_API_KEY="sk-..."

Windows (System):
    System Properties → Environment Variables

⚠️  Never share your API keys or commit them to Git!
        """
        
        messagebox.showinfo("Help", help_text)
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = KeyManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
