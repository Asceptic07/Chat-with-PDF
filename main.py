import customtkinter as ctk
import threading
import json
import os
from datetime import datetime
from tkinter import filedialog
from backend_rag import RAGHelper

# Set Appearance Mode
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

HISTORY_FILE = "chat_history.json"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Local RAG Chat - Enhanced")
        self.geometry("1100x700")

        # Initialize Backend
        self.rag = RAGHelper()
        self.current_history = []
        self.current_session_name = None

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar (Left) ===
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="RAG Document AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Upload Button
        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="+ New Chat (Upload PDF)", command=self.upload_pdf)
        self.upload_btn.grid(row=1, column=0, padx=20, pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame, mode="indeterminate", width=200)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=10)
        self.progress_bar.grid_remove()

        # Status Label
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Ready", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=20, pady=5)

        # Divider
        self.separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="gray30")
        self.separator.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # History Dashboard
        self.history_label = ctk.CTkLabel(self.sidebar_frame, text="Past Conversations", anchor="w")
        self.history_label.grid(row=5, column=0, padx=20, sticky="w")
        
        self.history_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.history_scroll.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")

        # === Main Chat Area (Right) ===
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a") # Darker background for contrast
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # VISUAL UPGRADE: Replaced Textbox with ScrollableFrame for Bubbles
        self.chat_display = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_display.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ask a question about the document...", height=40, font=("Roboto", 14))
        self.entry.grid(row=0, column=0, padx=(0, 20), sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=100, height=40, command=self.send_message, fg_color="#1f6aa5")
        self.send_btn.grid(row=0, column=1)

        self.load_history_list()

    # --- File Upload & Overview ---
    def upload_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        self.clear_chat()
        self.current_history = []
        
        self.status_label.configure(text="Processing PDF...", text_color="orange")
        self.upload_btn.configure(state="disabled")
        self.progress_bar.grid() 
        self.progress_bar.start()

        threading.Thread(target=self._process_pdf_thread, args=(file_path,), daemon=True).start()

    def _process_pdf_thread(self, file_path):
        try:
            self.rag.load_document(file_path)
            self.after(0, lambda: self.status_label.configure(text="Generating Summary..."))
            overview_text = self.rag.get_document_overview()
            self.after(0, self._finish_upload, file_path, overview_text)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _finish_upload(self, file_path, overview):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.upload_btn.configure(state="normal")
        self.status_label.configure(text="Index Ready", text_color="#2CC985")
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.current_session_name = f"{filename} ({timestamp})"
        
        welcome_msg = f"Document '{filename}' uploaded successfully.\n\nHere is a summary:\n{overview}"
        self._append_message("System", welcome_msg)
        
        self.save_current_session()
        self.load_history_list()

    def _show_error(self, error_message):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.upload_btn.configure(state="normal")
        self.status_label.configure(text="Error", text_color="red")
        self._append_message("System", f"Error: {error_message}")

    # --- Chat Logic ---
    def send_message(self, event=None):
        user_input = self.entry.get()
        if not user_input:
            return

        self._append_message("You", user_input)
        self.entry.delete(0, "end")
        self.send_btn.configure(state="disabled")
        self.save_current_session()

        threading.Thread(target=self._get_answer_thread, args=(user_input,), daemon=True).start()

    def _get_answer_thread(self, query):
        try:
            response = self.rag.ask_question(query)
            self.after(0, lambda: self._handle_bot_response(response))
        except Exception as e:
            self.after(0, self._append_message, "System", f"Error: {str(e)}")
        finally:
            self.after(0, lambda: self.send_btn.configure(state="normal"))

    def _handle_bot_response(self, response):
        self._append_message("Bot", response)
        self.save_current_session()

    # === THE NEW BUBBLE LOGIC ===
    def _append_message(self, sender, message):
        self.current_history.append({"sender": sender, "message": message})
        # 1. Determine Colors and Alignment based on sender
        if sender == "You":
            bubble_color = "#2b2b2b"  # Dark gray for user (or switch to blue if preferred)
            text_color = "white"
            anchor = "e" # East (Right)
            justify = "left"
        elif sender == "Bot":
            bubble_color = "#1f6aa5" # Blue for Bot
            text_color = "white"
            anchor = "w" # West (Left)
            justify = "left"
        else: # System
            bubble_color = "transparent"
            text_color = "orange"
            anchor = "center"
            justify = "center"

        # 2. Create a Frame (The Bubble)
        msg_frame = ctk.CTkFrame(self.chat_display, fg_color=bubble_color, corner_radius=15)
        msg_frame.pack(pady=5, padx=10, anchor=anchor)

        # 3. Add Text inside the Bubble
        # We use a label with wrapping enabled
        msg_label = ctk.CTkLabel(
            msg_frame, 
            text=message, 
            text_color=text_color, 
            wraplength=600, # Wrap text if it gets too long
            font=("Roboto", 14), 
            justify=justify
        )
        msg_label.pack(padx=15, pady=10)

        # 4. Auto-scroll to bottom
        # We need to wait a split second for the widget to draw before scrolling
        self.chat_display._parent_canvas.yview_moveto(1.0)

    def clear_chat(self):
        # Destroy all existing bubbles
        for widget in self.chat_display.winfo_children():
            widget.destroy()

    # --- History Management ---
    def save_current_session(self):
        if not self.current_session_name:
            return

        new_entry = {
            "session_name": self.current_session_name,
            "messages": self.current_history
        }

        try:
            data = []
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []

            session_exists = False
            for i, session in enumerate(data):
                if session.get("session_name") == self.current_session_name or session.get("session") == self.current_session_name:
                    data[i] = new_entry
                    session_exists = True
                    break
            
            if not session_exists:
                data.append(new_entry)
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
            # Update memory
            if {"sender": "You", "message": "temp"} not in self.current_history:
                 pass # Logic already handled in _append_message, just strictly saving here

        except Exception as e:
            print(f"Failed to save history: {e}")

    def load_history_list(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        if not os.path.exists(HISTORY_FILE):
            return
            
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                
            for session in reversed(data):
                name = session.get("session_name") or session.get("session") or "Unknown Session"
                btn = ctk.CTkButton(
                    self.history_scroll, 
                    text=name, 
                    fg_color="transparent", 
                    border_width=1, 
                    anchor="w", 
                    text_color="gray80",
                    height=40,
                    command=lambda s=session: self.load_old_session(s)
                )
                btn.pack(fill="x", pady=2)
        except Exception as e:
            print(f"Error loading history list: {e}")

    def load_old_session(self, session_data):
        self.clear_chat()
        self.current_history = session_data.get("messages", [])
        self.current_session_name = session_data.get("session_name") or session_data.get("session")
        
        self.status_label.configure(text="Viewing History", text_color="orange")
        
        # Re-populate chat bubbles
        for msg in self.current_history:
            # We call the new bubble function directly
            sender = msg["sender"]
            text = msg["message"]
            
            # Recreate the bubble logic manually here so we don't duplicate memory
            if sender == "You":
                color = "#2b2b2b"
                anchor = "e"
            elif sender == "Bot":
                color = "#1f6aa5"
                anchor = "w"
            else:
                color = "transparent"
                anchor = "center"
            
            msg_frame = ctk.CTkFrame(self.chat_display, fg_color=color, corner_radius=15)
            msg_frame.pack(pady=5, padx=10, anchor=anchor)
            
            lbl = ctk.CTkLabel(msg_frame, text=text, wraplength=600, font=("Roboto", 14), justify="left")
            lbl.pack(padx=15, pady=10)

        self.entry.configure(placeholder_text="Re-upload PDF to continue chatting.")
        self.send_btn.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()