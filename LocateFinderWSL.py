#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2025 Arrow Święch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

# LocateFinderWSL
## UI wrapper for locate linux command for Windows

## Requirements
wsl running default ubuntu

locate command installed `sudo apt install locate`

drives mounted in wsl
` sudo mount -t drvfs D: /mnt/d `

the filesystem needs to be indexed `sudo updatedb`
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import locale
import threading
from queue import Queue
import time

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class LocateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WSL Locate Search")

        # Configure root window to expand
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Make results row expandable

        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.columnconfigure(0, weight=1)  # Make search entry expand

        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Search button
        self.search_button = ttk.Button(search_frame, text="Search", command=self.start_search)
        self.search_button.grid(row=0, column=1)

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Checkboxes for options
        self.ignore_case = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Ignore case", variable=self.ignore_case).grid(row=0, column=0, padx=5)

        self.exist_only = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Existing files only", variable=self.exist_only).grid(row=0, column=1,
                                                                                                  padx=5)

        self.basename_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Filename only (no directories)", variable=self.basename_only).grid(row=0,
                                                                                                                column=2,
                                                                                                                padx=5)

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results")
        results_frame.grid(row=2, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results list with scrollbar
        self.results_list = tk.Listbox(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_list.yview)
        self.results_list.configure(yscrollcommand=scrollbar.set)

        self.results_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Status bar
        self.status_var = tk.StringVar()
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        self.progress_bar.grid_remove()  # Hide initially

        status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        status_bar.grid(row=4, column=0, sticky="ew", pady=(5, 0))

        # Bind events
        self.results_list.bind('<Double-Button-1>', self.open_selected_file)
        self.search_entry.bind('<Return>', lambda e: self.start_search())

        # Queue for thread communication
        self.queue = Queue()

        # Set minimum window size
        self.root.minsize(600, 400)

        # Start queue checker
        self.check_queue()

    def start_search(self):
        search_term = self.search_var.get()
        if not search_term:
            self.status_var.set("Please enter a search term")
            return

        # Clear previous results and show progress
        self.results_list.delete(0, tk.END)
        self.progress_bar.grid()
        self.progress_bar.start(10)
        self.search_button.configure(state='disabled')
        self.status_var.set("Searching...")

        # Start search in background thread
        thread = threading.Thread(target=self.perform_search, args=(search_term,))
        thread.daemon = True
        thread.start()

    def perform_search(self, search_term):
        try:
            # Build locate command
            cmd = ['wsl', 'locate']
            if self.ignore_case.get():
                cmd.append('--ignore-case')
            if self.exist_only.get():
                cmd.append('--existing')
            if self.basename_only.get():
                cmd.append('--basename')
            cmd.append(search_term)

            # Run locate command
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            paths = result.stdout.strip().split('\n')

            # Filter out empty results
            paths = [p for p in paths if p]

            # Put results in queue
            self.queue.put(('results', paths))

        except Exception as e:
            self.queue.put(('error', str(e)))

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()

                if msg_type == 'results':
                    # Add results to listbox
                    for path in data:
                        self.results_list.insert(tk.END, path)
                    self.status_var.set(f"Found {len(data)} results")
                    self.progress_bar.stop()
                    self.progress_bar.grid_remove()
                    self.search_button.configure(state='normal')

                elif msg_type == 'error':
                    self.status_var.set(f"Error: {data}")
                    self.progress_bar.stop()
                    self.progress_bar.grid_remove()
                    self.search_button.configure(state='normal')

        except Exception:
            pass  # Queue is empty

        # Schedule next check
        self.root.after(100, self.check_queue)

    def open_selected_file(self, event):
        selection = self.results_list.curselection()
        if not selection:
            return

        wsl_path = self.results_list.get(selection[0])

        try:
            # Run wslpath to convert the path
            result = subprocess.run(['wsl', 'wslpath', '-w', wsl_path],
                                    capture_output=True, text=True, encoding='utf-8')
            windows_path = result.stdout.strip()

            # Open in Windows Explorer
            subprocess.run(['explorer.exe', '/select,', windows_path])

        except subprocess.CalledProcessError as e:
            self.status_var.set(f"Error opening file: {e}")


def main():
    root = tk.Tk()
    app = LocateGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()