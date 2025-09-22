#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Desktop Launcher
Simple GUI launcher using tkinter for easy access to all modes
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import subprocess

try:
    from duckbot.ai_startup_interface import AIStartupInterface, StartupMode
    STARTUP_AVAILABLE = True
except ImportError:
    STARTUP_AVAILABLE = False

class DesktopLauncher:
    """Desktop GUI launcher for DuckBot"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DuckBot Desktop Launcher")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')

        self.startup_interface = AIStartupInterface() if STARTUP_AVAILABLE else None
        self.running_processes = {}

        self.setup_ui()
        self.load_modes()

    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 DuckBot Desktop Launcher",
            font=('Arial', 24, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(expand=True)

        # Status Bar
        status_frame = tk.Frame(self.root, bg='#34495e', height=40)
        status_frame.pack(fill='x', padx=5, pady=2)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="System Ready",
            font=('Arial', 10),
            bg='#34495e',
            fg='white'
        )
        self.status_label.pack(side='left', padx=10)

        # API Status
        self.api_frame = tk.Frame(status_frame, bg='#34495e')
        self.api_frame.pack(side='right', padx=10)

        # Notebook for categories
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Control Panel
        control_frame = tk.Frame(self.root, bg='#ecf0f1', height=60)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)

        # Buttons
        btn_frame = tk.Frame(control_frame, bg='#ecf0f1')
        btn_frame.pack(expand=True)

        tk.Button(
            btn_frame,
            text="Setup API Keys",
            command=self.setup_api_keys,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Refresh Status",
            command=self.refresh_status,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="View Logs",
            command=self.view_logs,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="System Info",
            command=self.show_system_info,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

    def load_modes(self):
        """Load startup modes into categories"""
        if not self.startup_interface:
            return

        # Clear existing tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        # Group modes by category
        categories = {}
        for mode in self.startup_interface.startup_modes:
            if mode.category not in categories:
                categories[mode.category] = []
            categories[mode.category].append(mode)

        # Create tabs for each category
        for category, modes in categories.items():
            frame = tk.Frame(self.notebook, bg='white')
            self.notebook.add(frame, text=category)

            # Create scrollable frame
            canvas = tk.Canvas(frame, bg='white')
            scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='white')

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Add mode cards
            for i, mode in enumerate(modes):
                self.create_mode_card(scrollable_frame, mode, i)

            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        self.update_api_status()

    def create_mode_card(self, parent, mode: StartupMode, index: int):
        """Create a card for a startup mode"""
        # Check requirements
        requirements = self.startup_interface.check_api_requirements(mode)
        can_launch = all(requirements.values())
        missing_apis = [api for api, available in requirements.items() if not available]

        # Card frame
        card_frame = tk.Frame(
            parent,
            bg='white',
            relief='raised',
            bd=1,
            highlightbackground='#bdc3c7',
            highlightthickness=1
        )
        card_frame.pack(fill='x', padx=10, pady=5)

        # Content frame
        content_frame = tk.Frame(card_frame, bg='white')
        content_frame.pack(fill='x', padx=10, pady=10)

        # Header
        header_frame = tk.Frame(content_frame, bg='white')
        header_frame.pack(fill='x')

        # Status indicator
        status_color = '#2ecc71' if can_launch else '#e74c3c'
        status_canvas = tk.Canvas(header_frame, width=12, height=12, bg='white', highlightthickness=0)
        status_canvas.pack(side='left', padx=(0, 5))
        status_canvas.create_oval(2, 2, 10, 10, fill=status_color, outline='')

        # Title
        title_label = tk.Label(
            header_frame,
            text=mode.name,
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(side='left', fill='x', expand=True)

        # AI indicator
        if mode.ai_powered:
            ai_label = tk.Label(
                header_frame,
                text="🤖",
                font=('Arial', 12),
                bg='white'
            )
            ai_label.pack(side='right')

        # Description
        desc_label = tk.Label(
            content_frame,
            text=mode.description,
            font=('Arial', 10),
            bg='white',
            fg='#7f8c8d',
            wraplength=700,
            justify='left'
        )
        desc_label.pack(fill='x', pady=(5, 0))

        # Requirements and port info
        info_frame = tk.Frame(content_frame, bg='white')
        info_frame.pack(fill='x', pady=(5, 0))

        if mode.port:
            port_label = tk.Label(
                info_frame,
                text=f"Port: {mode.port}",
                font=('Arial', 9),
                bg='white',
                fg='#3498db'
            )
            port_label.pack(side='left')

        if missing_apis:
            req_label = tk.Label(
                info_frame,
                text=f"Requires: {', '.join(missing_apis)}",
                font=('Arial', 9),
                bg='white',
                fg='#e74c3c'
            )
            req_label.pack(side='right')

        # Launch button
        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(fill='x', pady=(10, 0))

        btn_color = '#2ecc71' if can_launch else '#95a5a6'
        btn_text = 'Launch' if can_launch else 'Setup Required'

        launch_btn = tk.Button(
            btn_frame,
            text=btn_text,
            command=lambda m=mode: self.launch_mode(m),
            bg=btn_color,
            fg='white',
            font=('Arial', 10, 'bold'),
            state='normal' if can_launch else 'disabled'
        )
        launch_btn.pack(side='right')

        if can_launch:
            details_btn = tk.Button(
                btn_frame,
                text='Details',
                command=lambda m=mode: self.show_mode_details(m),
                bg='#3498db',
                fg='white',
                font=('Arial', 9)
            )
            details_btn.pack(side='right', padx=(0, 5))

    def launch_mode(self, mode: StartupMode):
        """Launch a startup mode"""
        try:
            self.status_label.config(text=f"Launching {mode.name}...")
            self.root.update()

            # Use the startup interface to launch
            if self.startup_interface:
                self.startup_interface.launch_mode(mode.id)

            messagebox.showinfo("Launch Started", f"{mode.name} launch initiated!")

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch {mode.name}: {e}")
            self.status_label.config(text="Launch failed")

    def show_mode_details(self, mode: StartupMode):
        """Show detailed information about a mode"""
        details = f"Mode: {mode.name}\n\n"
        details += f"Description: {mode.description}\n\n"
        details += f"Category: {mode.category}\n"
        details += f"AI-Powered: {'Yes' if mode.ai_powered else 'No'}\n"

        if mode.port:
            details += f"Port: {mode.port}\n"

        requirements = self.startup_interface.check_api_requirements(mode)
        if requirements:
            details += f"\nAPI Requirements:\n"
            for api, available in requirements.items():
                status = "✅" if available else "❌"
                details += f"  {status} {api.title()}\n"

        messagebox.showinfo("Mode Details", details)

    def setup_api_keys(self):
        """Setup API keys dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup API Keys")
        dialog.geometry("400x350")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()

        # API Key fields
        keys = [
            ("Gemini API Key", "gemini_api_key", True),
            ("OpenRouter API Key", "openrouter_api_key", True),
            ("Z.ai API Key", "zai_api_key", True),
            ("Z.ai Coding Plan", "zai_coding_plan", False)
        ]

        entries = {}
        for i, (label, key, is_password) in enumerate(keys):
            tk.Label(
                dialog,
                text=label + ":",
                font=('Arial', 10),
                bg='white'
            ).grid(row=i, column=0, sticky='w', padx=20, pady=10, columnspan=2)

            entry = tk.Entry(
                dialog,
                font=('Arial', 10),
                show='*' if is_password else '',
                width=30
            )
            entry.grid(row=i, column=2, padx=20, pady=10)
            entries[key] = entry

            # Load current value
            if self.startup_interface:
                current_value = getattr(self.startup_interface.api_keys, key, None)
                if current_value:
                    entry.insert(0, current_value)

        # Buttons
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.grid(row=len(keys), column=0, columnspan=3, pady=20)

        def save_keys():
            try:
                for key, entry in entries.items():
                    value = entry.get().strip()
                    setattr(self.startup_interface.api_keys, key, value or None)

                self.startup_interface._save_config()
                self.update_api_status()
                self.load_modes()
                messagebox.showinfo("Success", "API keys saved successfully!")
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API keys: {e}")

        tk.Button(
            btn_frame,
            text="Save",
            command=save_keys,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=5)

    def update_api_status(self):
        """Update API status indicators"""
        if not self.startup_interface:
            return

        # Clear existing indicators
        for widget in self.api_frame.winfo_children():
            widget.destroy()

        apis = [
            ("Gemini", self.startup_interface.api_keys.gemini_api_key),
            ("OpenRouter", self.startup_interface.api_keys.openrouter_api_key),
            ("Z.ai", self.startup_interface.api_keys.zai_api_key)
        ]

        for api_name, has_key in apis:
            color = '#2ecc71' if has_key else '#e74c3c'
            label = tk.Label(
                self.api_frame,
                text=api_name,
                font=('Arial', 8),
                bg='#34495e',
                fg=color
            )
            label.pack(side='left', padx=5)

    def refresh_status(self):
        """Refresh system status"""
        self.status_label.config(text="Refreshing status...")
        self.root.update()
        self.update_api_status()
        self.status_label.config(text="System Ready")

    def view_logs(self):
        """Open logs directory"""
        try:
            import subprocess
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer', 'logs'])
            else:  # macOS/Linux
                subprocess.Popen(['open', 'logs'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open logs: {e}")

    def show_system_info(self):
        """Show system information"""
        info = "DuckBot Desktop Launcher\n\n"
        info += f"Python Version: {sys.version.split()[0]}\n"
        info += f"Platform: {sys.platform}\n"
        info += f"Working Directory: {os.getcwd()}\n"

        if self.startup_interface:
            info += f"\nConfiguration File: {self.startup_interface.config_file}\n"
            info += f"Available Modes: {len(self.startup_interface.startup_modes)}\n"

            api_count = sum([
                bool(self.startup_interface.api_keys.gemini_api_key),
                bool(self.startup_interface.api_keys.openrouter_api_key),
                bool(self.startup_interface.api_keys.zai_api_key)
            ])
            info += f"API Keys Configured: {api_count}/3"

        messagebox.showinfo("System Information", info)

    def run(self):
        """Run the desktop launcher"""
        self.root.mainloop()

def main():
    """Main entry point"""
    if not STARTUP_AVAILABLE:
        print("❌ AI startup interface not available")
        return

    launcher = DesktopLauncher()
    launcher.run()

if __name__ == "__main__":
    main()