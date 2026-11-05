#!/usr/bin/env python3
"""
Main entry point for the Open Text to IPA PYSLE application.
Creates a Tkinter window with a two-panel layout:
- Left: input text area (user pastes text)
- Right: output text area (displays IPA transcription)
- One 'Transcribe' button below the input area
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from transcriber import transcrever_texto


def add_text_context_menu(widget, include_edit_actions=False):
    menu = tk.Menu(widget, tearoff=False)
    if include_edit_actions:
        menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Select All", command=lambda: widget.tag_add("sel", "1.0", "end-1c"))

    def show_menu(event):
        widget.focus_set()
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


def main():
    # Create the main window
    root = tk.Tk()
    root.title("Open Text to IPA")
    root.geometry("800x500")
    icon = tk.PhotoImage(file=Path(__file__).with_name("icon.png"))
    root.iconphoto(True, icon)
    
    # Create a frame for the two panels
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Left panel: input text area and controls
    left_frame = ttk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
    left_frame.rowconfigure(0, weight=1)
    left_frame.columnconfigure(0, weight=1)

    input_frame = ttk.LabelFrame(left_frame, text="Input Text")
    input_frame.grid(row=0, column=0, sticky="nsew")
    
    # Text widget for input
    input_text = tk.Text(input_frame, wrap=tk.WORD, height=10, width=50)
    input_scrollbar = ttk.Scrollbar(
        input_frame, orient=tk.VERTICAL, command=input_text.yview
    )
    input_text.configure(yscrollcommand=input_scrollbar.set)
    input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
    input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
    
    controls_frame = ttk.Frame(left_frame)
    controls_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    # Mode selection (transcription only / word by word)
    mode_var = tk.StringVar(value="word by word")
    mode_frame = ttk.Frame(controls_frame)
    mode_frame.pack(fill=tk.X, padx=5, pady=5)
    
    mode_options = [
        ("Word by word", "word by word"),
        ("Transcription only", "transcription only")
    ]
    
    for i, (text, value) in enumerate(mode_options):
        radio = ttk.Radiobutton(
            mode_frame, 
            text=text,
            variable=mode_var,
            value=value
        )
        radio.grid(row=0, column=i, padx=5, sticky="w")
    
    # Syllable division checkbox
    syllabus_var = tk.BooleanVar(value=True)
    syllabus_checkbox = ttk.Checkbutton(
        controls_frame,
        text="Syllable division",
        variable=syllabus_var
    )
    syllabus_checkbox.pack(anchor=tk.W, padx=5, pady=5)
    
    # Transcribe button
    def on_transcribe():
        text = input_text.get("1.0", "end-1c")
        if not text.strip():
            return
            
        mode = mode_var.get()
        syllabus = syllabus_var.get()
        
        try:
            result = transcrever_texto(text, mode, syllabus)
        except Exception as e:
            result = f"[erro: {str(e)}]"

        output_text.configure(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, result)
        output_text.configure(state=tk.DISABLED)
    
    transcribe_button = ttk.Button(
        controls_frame,
        text="Transcribe", 
        command=on_transcribe
    )
    transcribe_button.pack(fill=tk.X, padx=5, pady=5)
    
    # Right panel: output text area
    output_frame = ttk.LabelFrame(main_frame, text="IPA Transcription")
    output_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
    
    # Text widget for output (read-only)
    output_text = tk.Text(
        output_frame, wrap=tk.WORD, height=10, width=50, state=tk.DISABLED
    )
    output_scrollbar = ttk.Scrollbar(
        output_frame, orient=tk.VERTICAL, command=output_text.yview
    )
    output_text.configure(yscrollcommand=output_scrollbar.set)
    output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
    output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)

    add_text_context_menu(input_text, include_edit_actions=True)
    add_text_context_menu(output_text)
    
    # Configure grid weights for resizing
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()