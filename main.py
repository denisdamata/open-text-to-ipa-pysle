#!/usr/bin/env python3
"""
Main entry point for the Open Text to IPA PYSLE application.
Creates a Tkinter window with a two-panel layout:
- Left: input text area (user pastes text)
- Right: output text area (displays IPA transcription)
- One 'Transcribe' button below the input area
"""

from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
import klembord
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from transcriber import transcrever_texto_com_estilos


def enable_xauthority_wildcard_support():
    from Xlib import xauth

    original_get_best_auth = xauth.Xauthority.get_best_auth
    # Xwayland may store Xauthority entries with an empty display number.
    family_wild = 0xFFFF

    def get_best_auth(
        authority,
        family,
        address,
        display_number,
        types=(b"MIT-MAGIC-COOKIE-1",),
    ):
        try:
            return original_get_best_auth(
                authority, family, address, display_number, types
            )
        except xauth.error.XNoAuthError:
            for entry_family, entry_address, entry_number, name, data in (
                authority
            ):
                if (
                    entry_family in (family, family_wild)
                    and (
                        entry_family == family_wild
                        or entry_address == address
                    )
                    and not entry_number
                    and name in types
                ):
                    return name, data
            raise

    xauth.Xauthority.get_best_auth = get_best_auth


enable_xauthority_wildcard_support()


def escape_rtf(text):
    escaped = []
    for character in text:
        if character in "{}\\":
            escaped.append("\\" + character)
        elif character == "\n":
            escaped.append("\\line ")
        elif character == "\t":
            escaped.append("\\tab ")
        elif ord(character) > 127:
            encoded = character.encode("utf-16-le")
            for offset in range(0, len(encoded), 2):
                code_unit = int.from_bytes(encoded[offset:offset + 2], "little")
                if code_unit >= 0x8000:
                    code_unit -= 0x10000
                escaped.append(f"\\u{code_unit}?")
        else:
            escaped.append(character)
    return "".join(escaped)


def build_clipboard_content(widget, selection_start, selection_end):
    plain_text = widget.get(selection_start, selection_end)
    html_parts = []
    rtf_parts = []
    cursor = selection_start
    bold_ranges = widget.tag_ranges("non_ipa")

    for tag_start, tag_end in zip(bold_ranges[::2], bold_ranges[1::2]):
        bold_start = (
            selection_start
            if widget.compare(tag_start, "<", selection_start)
            else tag_start
        )
        bold_end = (
            selection_end
            if widget.compare(tag_end, ">", selection_end)
            else tag_end
        )
        if widget.compare(bold_start, ">=", selection_end):
            break
        if widget.compare(bold_end, "<=", cursor):
            continue
        if widget.compare(bold_start, "<", cursor):
            bold_start = cursor

        if widget.compare(cursor, "<", bold_start):
            text = widget.get(cursor, bold_start)
            html_parts.append(escape(text))
            rtf_parts.append(escape_rtf(text))
        if widget.compare(bold_start, "<", bold_end):
            text = widget.get(bold_start, bold_end)
            html_parts.append(f"<strong>{escape(text)}</strong>")
            rtf_parts.append(f"\\b {escape_rtf(text)}\\b0 ")
            cursor = bold_end

    if widget.compare(cursor, "<", selection_end):
        text = widget.get(cursor, selection_end)
        html_parts.append(escape(text))
        rtf_parts.append(escape_rtf(text))

    html = (
        '<html><body><div style="white-space:pre-wrap">'
        + "".join(html_parts)
        + "</div></body></html>"
    )
    rtf = (
        r"{\rtf1\ansi\deff0\uc1"
        r"{\fonttbl{\f0\fnil Arial;}}\pard\f0\fs20 "
        + "".join(rtf_parts)
        + "}"
    )
    encoded_text = plain_text.encode("utf-8")
    return {
        "UTF8_STRING": encoded_text,
        "text/plain;charset=utf-8": encoded_text,
        "text/plain": encoded_text,
        "text/html": html.encode("utf-8"),
        "text/rtf": rtf.encode("ascii"),
    }


def add_text_context_menu(widget, editable=False, copy_command=None):
    menu = tk.Menu(widget, tearoff=False)
    copy = copy_command or (lambda: widget.event_generate("<<Copy>>"))

    if editable:
        menu.add_command(label="Undo", command=lambda: widget.event_generate("<<Undo>>"))
        menu.add_command(label="Redo", command=lambda: widget.event_generate("<<Redo>>"))
        menu.add_separator()

        menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))

        def paste():
            try:
                clipboard_text = widget.clipboard_get()
            except tk.TclError:
                return
            if not clipboard_text:
                return

            try:
                selection_start = widget.index("sel.first")
                selection_end = widget.index("sel.last")
            except tk.TclError:
                selection_start = selection_end = widget.index(tk.INSERT)

            widget.edit_separator()
            widget.delete(selection_start, selection_end)
            widget.insert(selection_start, clipboard_text)
            widget.mark_set(
                tk.INSERT, f"{selection_start}+{len(clipboard_text)} chars"
            )
            widget.see(tk.INSERT)
            widget.edit_separator()

        menu.add_command(label="Paste", command=paste)
        menu.add_separator()

    menu.add_command(label="Copy", command=copy)

    def select_all():
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set(tk.INSERT, "end-1c")

    shortcuts = {
        "<Control-a>": select_all,
        "<Control-c>": copy,
    }
    if editable:
        shortcuts.update({
            "<Control-x>": lambda: widget.event_generate("<<Cut>>"),
            "<Control-v>": paste,
            "<Control-z>": lambda: widget.event_generate("<<Undo>>"),
            "<Control-y>": lambda: widget.event_generate("<<Redo>>"),
            "<Control-Shift-z>": lambda: widget.event_generate("<<Redo>>"),
        })

    def run_shortcut(action):
        action()
        return "break"

    for sequence, command in shortcuts.items():
        widget.bind(sequence, lambda event, action=command: run_shortcut(action))

    def show_menu(event):
        widget.focus_set()
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


def update_scrollbar_visibility(scrollbar, first, last, padx):
    scrollbar.set(first, last)
    needs_scrollbar = float(first) > 0.0 or float(last) < 1.0
    if needs_scrollbar and not scrollbar.winfo_manager():
        scrollbar.grid(row=0, column=1, sticky="ns", padx=padx, pady=5)
    elif not needs_scrollbar and scrollbar.winfo_manager():
        scrollbar.grid_remove()


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
    text_font = tkfont.nametofont("TkTextFont").copy()
    text_font.configure(size=abs(int(text_font.cget("size"))) + 3)
    input_text = tk.Text(
        input_frame, wrap=tk.WORD, height=10, width=50,
        undo=True, autoseparators=True, maxundo=-1, font=text_font
    )
    input_scrollbar = ttk.Scrollbar(
        input_frame, orient=tk.VERTICAL, command=input_text.yview
    )
    input_frame.rowconfigure(0, weight=1)
    input_frame.columnconfigure(0, weight=1)
    input_text.configure(
        yscrollcommand=lambda first, last: update_scrollbar_visibility(
            input_scrollbar, first, last, (0, 5)
        )
    )
    input_text.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
    
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
    option_actions_frame = ttk.Frame(controls_frame)
    option_actions_frame.pack(fill=tk.X, padx=5, pady=5)

    syllabus_checkbox = ttk.Checkbutton(
        option_actions_frame,
        text="Syllable division",
        variable=syllabus_var
    )
    syllabus_checkbox.pack(side=tk.LEFT)

    def adjust_font_size(change):
        size = max(6, min(32, abs(int(text_font.cget("size"))) + change))
        text_font.configure(size=size)
        bold_font.configure(size=size)

    smaller_font_button = ttk.Button(
        option_actions_frame,
        text="A-",
        command=lambda: adjust_font_size(-1),
        width=4,
    )
    smaller_font_button.pack(side=tk.RIGHT, padx=(5, 0))

    larger_font_button = ttk.Button(
        option_actions_frame,
        text="A+",
        command=lambda: adjust_font_size(1),
        width=4,
    )
    larger_font_button.pack(side=tk.RIGHT)
    
    # Transcribe button
    def on_transcribe():
        text = input_text.get("1.0", "end-1c")
        if not text.strip():
            return
            
        mode = mode_var.get()
        syllabus = syllabus_var.get()
        
        try:
            result = transcrever_texto_com_estilos(text, mode, syllabus)
        except Exception as e:
            result = [(f"[erro: {str(e)}]", True)]

        output_text.configure(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        for fragment, is_non_ipa in result:
            output_text.insert(
                tk.END, fragment, "non_ipa" if is_non_ipa else ()
            )
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
    output_content_frame = ttk.Frame(output_frame)
    output_content_frame.pack(fill=tk.BOTH, expand=True)
    output_content_frame.rowconfigure(0, weight=1)
    output_content_frame.columnconfigure(0, weight=1)
    output_text = tk.Text(
        output_content_frame, wrap=tk.WORD, height=10, width=50,
        state=tk.DISABLED, font=text_font
    )
    bold_font = text_font.copy()
    bold_font.configure(weight="bold")
    output_text.tag_configure("non_ipa", font=bold_font)
    output_scrollbar = ttk.Scrollbar(
        output_content_frame, orient=tk.VERTICAL, command=output_text.yview
    )
    output_text.configure(
        yscrollcommand=lambda first, last: update_scrollbar_visibility(
            output_scrollbar, first, last, (0, 5)
        )
    )
    output_text.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)

    def copy_output_selection():
        try:
            selection_start = output_text.index("sel.first")
            selection_end = output_text.index("sel.last")
        except tk.TclError:
            return

        try:
            klembord.set(
                build_clipboard_content(
                    output_text, selection_start, selection_end
                )
            )
        except Exception as error:
            messagebox.showerror(
                "Clipboard error",
                f"Could not copy the selection:\n{error}",
                parent=root,
            )

    def copy_all_output():
        output_text.tag_add("sel", "1.0", "end-1c")
        copy_output_selection()

    def save_output(extension, file_type, export_filter=None):
        output = output_text.get("1.0", "end-1c")
        if not output:
            messagebox.showinfo(
                "Nothing to save",
                "Transcribe some text before saving the output.",
                parent=root,
            )
            return

        if extension == ".txt" and not messagebox.askyesno(
            "Plain Text Export",
            "TXT does not preserve bold formatting. Continue?",
            parent=root,
        ):
            return

        destination = filedialog.asksaveasfilename(
            parent=root,
            title=f"Save transcription as {file_type}",
            defaultextension=extension,
            initialfile=f"transcription{extension}",
            filetypes=((file_type, f"*{extension}"),),
        )
        if not destination:
            return

        destination_path = Path(destination)
        if destination_path.suffix.lower() != extension:
            destination_path = destination_path.with_name(
                destination_path.name + extension
            )

        try:
            if extension == ".txt":
                destination_path.write_text(output, encoding="utf-8")
                return

            office_command = shutil.which("libreoffice") or shutil.which("soffice")
            if office_command is None:
                messagebox.showerror(
                    "Export unavailable",
                    "LibreOffice is required to save as PDF, ODT, or DOCX. "
                    "Install LibreOffice and try again.",
                    parent=root,
                )
                return

            html = build_clipboard_content(
                output_text, "1.0", "end-1c"
            )["text/html"].decode("utf-8")
            html = html.replace("\n", "<br>\n")
            html = html.replace(
                "<html><body>",
                '<html><head><meta charset="utf-8"><style>'
                "@page { size: A4; margin: 20mm; }"
                "body { font-family: sans-serif; }"
                "</style></head><body>",
            ).replace(
                '<div style="white-space:pre-wrap">',
                '<div style="white-space:pre-wrap;'
                f'font-size:{abs(int(text_font.cget("size")))}pt">',
            )

            with tempfile.TemporaryDirectory(prefix="open-text-to-ipa-") as temp_dir:
                temp_path = Path(temp_dir)
                source_path = temp_path / "transcription.html"
                source_path.write_text(html, encoding="utf-8")
                profile_path = (temp_path / "lo-profile").as_uri()
                completed = subprocess.run(
                    [
                        office_command,
                        "--headless",
                        f"-env:UserInstallation={profile_path}",
                        "--convert-to",
                        export_filter,
                        "--outdir",
                        temp_dir,
                        str(source_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                converted_path = temp_path / f"transcription{extension}"
                if completed.returncode != 0 or not converted_path.is_file():
                    detail = completed.stderr.strip() or completed.stdout.strip()
                    raise RuntimeError(
                        detail or f"LibreOffice did not create a {file_type} file."
                    )
                shutil.copyfile(converted_path, destination_path)
        except (
            OSError,
            subprocess.SubprocessError,
            RuntimeError,
            tk.TclError,
        ) as error:
            messagebox.showerror(
                "Save failed",
                f"Could not save the transcription as {file_type}:\n{error}",
                parent=root,
            )

    def show_save_menu():
        save_menu.tk_popup(
            save_button.winfo_rootx(),
            save_button.winfo_rooty() + save_button.winfo_height(),
        )

    save_menu = tk.Menu(root, tearoff=False)
    save_menu.add_command(
        label="PDF",
        command=lambda: save_output(".pdf", "PDF", "pdf:writer_pdf_Export"),
    )
    save_menu.add_command(
        label="ODT",
        command=lambda: save_output(".odt", "ODT", "odt"),
    )
    save_menu.add_command(
        label="DOCX",
        command=lambda: save_output(".docx", "DOCX", "docx:Office Open XML Text"),
    )
    save_menu.add_command(
        label="🚨 No bold (TXT)",
        command=lambda: save_output(".txt", "Plain Text (TXT)"),
    )

    output_actions_frame = ttk.Frame(output_frame)
    output_actions_frame.pack(fill=tk.X, padx=5, pady=5)

    save_button = ttk.Button(
        output_actions_frame,
        text="💾",
        command=show_save_menu,
        width=3,
    )
    save_button.pack(side=tk.LEFT, padx=(0, 5))

    copy_all_button = ttk.Button(
        output_actions_frame,
        text="Copy All",
        command=copy_all_output,
    )
    copy_all_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

    add_text_context_menu(input_text, editable=True)
    add_text_context_menu(output_text, copy_command=copy_output_selection)
    
    # Configure grid weights for resizing
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()