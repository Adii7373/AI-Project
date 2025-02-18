  # Import required libraries
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tkinter import BOTH, FLAT, GROOVE, LEFT, RIDGE, RIGHT, VERTICAL, WORD, X, Y, Image, TclError, messagebox, END, SEL_FIRST, SEL_LAST, Tk, Frame, Label, Button, Text, Entry, Scrollbar, Canvas, Toplevel, StringVar, Radiobutton
from tensorflow.keras.utils import to_categorical
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from tkinter import ttk

# Database setup
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    surname TEXT,
    class_name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Add default admin if not exists
cursor.execute("INSERT OR IGNORE INTO admin (email, password) VALUES (?, ?)", ("Aditya123", "12345678*"))

# Add a test user if no users exist (for testing)
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO users (email, password, name, surname, class_name) 
        VALUES (?, ?, ?, ?, ?)
    """, ("test@example.com", "password123", "Test", "User", "Class A"))

conn.commit()

def toggle_password(entry, toggle_btn):
    if entry.cget("show") == "*":
        entry.config(show="")
        toggle_btn.config(text="👁️")
    else:
        entry.config(show="*")
        toggle_btn.config(text="🔒")

# Functions for User Login
def register():
    email = entry_email.get()
    password = entry_password.get()
    name = entry_name.get()
    surname = entry_surname.get()
    class_name = entry_class.get()

    if email == "" or password == "" or name == "" or surname == "" or class_name == "":
        messagebox.showerror("Error", "All fields are required!")
    else:
        try:
            cursor.execute("INSERT INTO users (email, password, name, surname, class_name) VALUES (?, ?, ?, ?, ?)", 
                           (email, password, name, surname, class_name))
            conn.commit()
            messagebox.showinfo("Success", "Registration Successful!")
            show_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Email already exists!")

def user_login():
    email = entry_email.get()
    password = entry_password.get()
    if email == "" or password == "":
        messagebox.showerror("Error", "All fields are required!")
    else:
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            show_ai_dashboard(user[0], user[3])  # Pass user id and name to dashboard
        else:
            messagebox.showerror("Error", "Invalid credentials!")
def admin_login():
    email = admin_email.get()
    password = admin_password.get()
    if email == "" or password == "":
        messagebox.showerror("Error", "All fields are required!")
    else:
        cursor.execute("SELECT * FROM admin WHERE email = ? AND password = ?", (email, password))
        admin = cursor.fetchone()
        if admin:
            show_admin_dashboard()
        else:
            messagebox.showerror("Error", "Invalid Admin credentials!")


def show_admin_dashboard():
    for widget in root.winfo_children():
        widget.destroy()

    # Color scheme
    PRIMARY_COLOR = "#1a237e"  # Dark Blue
    SECONDARY_COLOR = "#0d47a1"
    BG_COLOR = "#f5f5f5"
    CARD_BG = "#ffffff"
    TEXT_COLOR = "#263238"
    SUCCESS_COLOR = "#00c853"
    WARNING_COLOR = "#ff9800"
    DANGER_COLOR = "#f44336"

    # Configure root window
    root.configure(bg=BG_COLOR)
    root.geometry("1400x900")
    root.title("Admin Dashboard - AI Learning Assistant")

    # Create main container
    main_frame = Frame(root, bg=BG_COLOR)
    main_frame.pack(fill=BOTH, expand=True)

    # Header with gradient effect
    header_frame = Frame(main_frame, bg=PRIMARY_COLOR, height=80)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    # Admin header with title and logout button
    Label(
        header_frame,
        text="Admin Dashboard",
        font=("Helvetica", 24, "bold"),
        bg=PRIMARY_COLOR,
        fg="white"
    ).pack(side=LEFT, padx=40, pady=20)

    Button(
        header_frame,
        text="🚪 Logout",
        command=show_login,
        font=("Helvetica", 12, "bold"),
        bg=DANGER_COLOR,
        fg="white",
        relief=FLAT,
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(side=RIGHT, padx=40, pady=20)

    # Content area
    content_frame = Frame(main_frame, bg=BG_COLOR)
    content_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    # Statistics Cards Row
    stats_frame = Frame(content_frame, bg=BG_COLOR)
    stats_frame.pack(fill=X, pady=(0, 30))

    def create_stat_card(title, value, icon, color):
        card = Frame(stats_frame, bg=CARD_BG, relief=GROOVE, bd=1)
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=10)
        
        icon_label = Label(
            card,
            text=icon,
            font=("Helvetica", 24),
            bg=CARD_BG,
            fg=color
        )
        icon_label.pack(pady=(20,5))
        
        value_label = Label(
            card,
            text=str(value),  # Convert value to string
            font=("Helvetica", 24, "bold"),
            bg=CARD_BG,
            fg=color
        )
        value_label.pack()
        
        title_label = Label(
            card,
            text=title,
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR
        )
        title_label.pack(pady=(5,20))

    # Get statistics from database
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM history")
    total_queries = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) 
        FROM history 
        WHERE date(timestamp) = date('now')
    """)
    active_users_today = cursor.fetchone()[0]

    # Create statistics cards
    create_stat_card("Total Users", total_users, "👥", SUCCESS_COLOR)
    create_stat_card("Total Queries", total_queries, "💭", WARNING_COLOR)
    create_stat_card("Active Users Today", active_users_today, "📊", PRIMARY_COLOR)

    # User List Section
    user_list_frame = Frame(content_frame, bg=CARD_BG, relief=GROOVE, bd=1)
    user_list_frame.pack(fill=BOTH, expand=True, pady=(20, 0))

    # User list header
    list_header = Frame(user_list_frame, bg=PRIMARY_COLOR, height=50)
    list_header.pack(fill=X)
    list_header.pack_propagate(False)

    Label(
        list_header,
        text="User Management",
        font=("Helvetica", 16, "bold"),
        bg=PRIMARY_COLOR,
        fg="white"
    ).pack(pady=10)

    # Create table headers
    headers_frame = Frame(user_list_frame, bg=CARD_BG)
    headers_frame.pack(fill=X, padx=20, pady=10)

    headers = ["Name", "Email   ", "Class", "Total Queries", "Last Active", "Actions"]
    for header in headers:
        Label(
            headers_frame,
            text=header,
            font=("Helvetica", 12, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            width=15,
            anchor="w"
        ).pack(side=LEFT, padx=10)

    # Create scrollable frame for user list
    user_canvas = Canvas(user_list_frame, bg=CARD_BG)
    scrollbar = Scrollbar(user_list_frame, orient=VERTICAL, command=user_canvas.yview)
    scrollable_frame = Frame(user_canvas, bg=CARD_BG)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all"))
    )

    user_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    user_canvas.configure(yscrollcommand=scrollbar.set)

    # Get all users with their statistics using a simpler query first
    cursor.execute("""
        SELECT 
            u.id,
            u.name,
            u.email,
            u.class_name,
            COALESCE(h.query_count, 0) as query_count,
            h.last_active
        FROM users u
        LEFT JOIN (
            SELECT 
                user_id,
                COUNT(*) as query_count,
                MAX(timestamp) as last_active
            FROM history
            GROUP BY user_id
        ) h ON u.id = h.user_id
        ORDER BY u.name
    """)
    
    users = cursor.fetchall()
    
    # Debug print to check if users are being fetched
    print(f"Number of users found: {len(users)}")
    for user in users:
        print(f"User data: {user}")

    # Display users
    for user in users:
        user_frame = Frame(scrollable_frame, bg=CARD_BG)
        user_frame.pack(fill=X, padx=20, pady=5)

        # User details
        Label(user_frame, text=str(user[1] or "N/A"), font=("Helvetica", 12), bg=CARD_BG, width=15, anchor="w").pack(side=LEFT, padx=10)
        Label(user_frame, text=str(user[2] or "N/A"), font=("Helvetica", 12), bg=CARD_BG, width=15, anchor="w").pack(side=LEFT, padx=10)
        Label(user_frame, text=str(user[3] or "N/A"), font=("Helvetica", 12), bg=CARD_BG, width=15, anchor="w").pack(side=LEFT, padx=10)
        Label(user_frame, text=str(user[4] or 0), font=("Helvetica", 12), bg=CARD_BG, width=15, anchor="w").pack(side=LEFT, padx=10)
        Label(user_frame, text=str(user[5] or "Never"), font=("Helvetica", 12), bg=CARD_BG, width=15, anchor="w").pack(side=LEFT, padx=10)

        # Action buttons
        actions_frame = Frame(user_frame, bg=CARD_BG)
        actions_frame.pack(side=LEFT, padx=10)

        Button(
            actions_frame,
            text="View History",
            command=lambda u_id=user[0], u_name=user[1]: view_user_history(u_id, u_name),
            font=("Helvetica", 10),
            bg=PRIMARY_COLOR,
            fg="white",
            relief=FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=LEFT, padx=5)

        Button(
            actions_frame,
            text="Delete User",
            command=lambda u_id=user[0]: delete_user(u_id),
            font=("Helvetica", 10),
            bg=DANGER_COLOR,
            fg="white",
            relief=FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=LEFT, padx=5)

    # Pack scrollbar and canvas
    scrollbar.pack(side=RIGHT, fill=Y)
    user_canvas.pack(side=LEFT, fill=BOTH, expand=True)

    # Configure canvas scrolling
    user_canvas.bind('<Configure>', lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all")))
    scrollable_frame.bind('<Configure>', lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all")))

    # Main content area with tabs
    notebook = ttk.Notebook(content_frame)
    notebook.pack(fill=BOTH, expand=True)

    # Users Tab
    users_frame = Frame(notebook, bg=CARD_BG)
    notebook.add(users_frame, text="Users Management")

    # Users table
    users_table_frame = Frame(users_frame, bg=CARD_BG)
    users_table_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

    # Search and filter bar
    search_frame = Frame(users_table_frame, bg=CARD_BG)
    search_frame.pack(fill=X, pady=(0, 20))

    search_entry = Entry(
        search_frame,
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg=TEXT_COLOR,
        relief=FLAT,
        bd=1
    )
    search_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10), ipady=5)

    def search_users():
        search_term = search_entry.get().strip()
        # Clear existing user frames
        for widget in users_list.winfo_children():
            if widget != header_frame:
                widget.destroy()
                
        # Modified query with search
        if search_term:
            cursor.execute("""
                SELECT users.id, users.name, users.surname, users.email, users.class_name,
                       COUNT(history.id) as query_count,
                       MAX(history.timestamp) as last_active
                FROM users
                LEFT JOIN history ON users.id = history.user_id
                WHERE users.name LIKE ? OR users.email LIKE ? OR users.class_name LIKE ?
                GROUP BY users.id
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute("""
                SELECT users.id, users.name, users.surname, users.email, users.class_name,
                       COUNT(history.id) as query_count,
                       MAX(history.timestamp) as last_active
                FROM users
                LEFT JOIN history ON users.id = history.user_id
                GROUP BY users.id
            """)
        
        display_users(cursor.fetchall())

    Button(
        search_frame,
        text="🔍 Search",
        command=search_users,
        font=("Helvetica", 12),
        bg=PRIMARY_COLOR,
        fg="white",
        relief=FLAT,
        padx=20,
        pady=5,
        cursor="hand2"
    ).pack(side=LEFT)

    # Users list
    users_list = Frame(users_table_frame, bg=CARD_BG)
    users_list.pack(fill=BOTH, expand=True)

    # Table headers
    headers = ["ID", "Name", "Email", "Class", "Queries", "Last Active", "Actions"]
    header_frame = Frame(users_list, bg=PRIMARY_COLOR)
    header_frame.pack(fill=X)

    for header in headers:
        Label(
            header_frame,
            text=header,
            font=("Helvetica", 12, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            padx=20,
            pady=10
        ).pack(side=LEFT, expand=True)

    def display_users(users_data):
        # Clear existing user frames (except header)
        for widget in users_list.winfo_children():
            if widget != header_frame:
                widget.destroy()

        for user in users_data:
            user_frame = Frame(users_list, bg=CARD_BG)
            user_frame.pack(fill=X, pady=1)
            
            # Combine name and surname
            full_name = f"{user[1]} {user[2]}" if user[2] else user[1]
            
            # Display user data
            values = [
                user[0],  # ID
                full_name,  # Full Name
                user[3],  # Email
                user[4],  # Class
                user[5] if user[5] else 0,  # Query Count
                user[6] if user[6] else "Never"  # Last Active
            ]
            
            for value in values:
                Label(
                    user_frame,
                    text=str(value),
                    font=("Helvetica", 12),
                    bg=CARD_BG,
                    fg=TEXT_COLOR,
                    padx=20,
                    pady=10
                ).pack(side=LEFT, expand=True)
            
            # Actions buttons
            actions_frame = Frame(user_frame, bg=CARD_BG)
            actions_frame.pack(side=LEFT, expand=True)
            
            Button(
                actions_frame,
                text="📝",
                command=lambda u=user[0], n=full_name: view_user_history(u, n),
                font=("Helvetica", 12),
                bg=WARNING_COLOR,
                fg="white",
                relief=FLAT,
                padx=10,
                cursor="hand2"
            ).pack(side=LEFT, padx=5)
            
            Button(
                actions_frame,
                text="❌",
                command=lambda u=user[0]: delete_user(u),
                font=("Helvetica", 12),
                bg=DANGER_COLOR,
                fg="white",
                relief=FLAT,
                padx=10,
                cursor="hand2"
            ).pack(side=LEFT, padx=5)

    # Initial display of users
    cursor.execute("""
        SELECT users.id, users.name, users.surname, users.email, users.class_name,
               COUNT(history.id) as query_count,
               MAX(history.timestamp) as last_active
        FROM users
        LEFT JOIN history ON users.id = history.user_id
        GROUP BY users.id
    """)
    display_users(cursor.fetchall())

    # Analytics Tab
    analytics_frame = Frame(notebook, bg=CARD_BG)
    notebook.add(analytics_frame, text="Analytics")

    Label(
        analytics_frame,
        text="Analytics Dashboard",
        font=("Helvetica", 16, "bold"),
        bg=CARD_BG,
        fg=TEXT_COLOR
    ).pack(pady=20)

    # System Logs Tab
    logs_frame = Frame(notebook, bg=CARD_BG)
    notebook.add(logs_frame, text="System Logs")

    log_text = Text(
        logs_frame,
        wrap=WORD,
        font=("Courier", 12),
        bg=CARD_BG,
        fg=TEXT_COLOR,
        relief=FLAT
    )
    log_text.pack(fill=BOTH, expand=True, padx=20, pady=20)

    # Sample logs
    log_text.insert(END, "System Logs:\n\n")
    log_text.insert(END, "[INFO] System started successfully\n")
    log_text.insert(END, "[INFO] Database connection established\n")

    log_text.configure(state="disabled")

def view_user_history(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    Label(root, text=f"{user_name}'s History", font=("Arial", 24, "bold")).pack(pady=20)

    chat_log = Text(root, height=20, width=80, font=("Arial", 14), wrap=WORD)
    chat_log.tag_config("history", foreground="purple")
    chat_log.pack(pady=10, padx=20)

    # Fetch and display user history
    history = cursor.execute("SELECT id, query FROM history WHERE user_id = ?", (user_id,)).fetchall()
    if history:
        for item in history:
            chat_log.insert(END, f"Query ID: {item[0]}, Query: {item[1]}\n", "history")
    else:
        chat_log.insert(END, "No history found for this user.\n", "history")

    # Buttons for history
    Button(root, text="Delete Query",
           command=lambda: delete_query(user_id, chat_log),
           bg="red", fg="white", font=("Arial", 14)).pack(pady=10)

    Button(root, text="Back", command=show_admin_dashboard, bg="blue", fg="white", font=("Arial", 14)).pack(pady=20)


def delete_user(user_id):
    """
    Deletes a user and their history from the database.
    """
    confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this user and their history?")
    if confirm:
        cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "User and their history have been deleted successfully!")
        show_admin_dashboard()


def delete_query(user_id, chat_log):
    """
    Deletes the last query of a user from the database.
    """
    last_query = cursor.execute("SELECT id FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if last_query:
        cursor.execute("DELETE FROM history WHERE id = ?", (last_query[0],))
        conn.commit()
        messagebox.showinfo("Deleted", "Last query has been deleted successfully!")
        # Refresh history view
        view_user_history(user_id, "")
    else:
        messagebox.showerror("Error", "No queries to delete!")


def create_admin_login_form():
    """
    Displays the admin login form.
    """

    Label(root, text="Admin Login Form", font=("Arial", 24, "bold"), bg="Yellow").pack(pady=10)

    global admin_email, admin_password

    frame = Frame(root, bg="lightblue")
    frame.pack(pady=50)

    Label(frame, text="Admin Email", font=("Arial", 14), bg="lightblue").grid(row=0, column=0, pady=10, padx=10)
    admin_email = Entry(frame, width=25, font=("Arial", 14))
    admin_email.grid(row=0, column=1, pady=10, padx=10)

    Label(frame, text="Password", font=("Arial", 14), bg="lightblue").grid(row=1, column=0, pady=10, padx=10)
    admin_password = Entry(frame, width=25, font=("Arial", 14), show="*")
    admin_password.grid(row=1, column=1, pady=10, padx=10)

    toggle_btn = Button(frame, text="🔒", command=lambda: toggle_password(admin_password, toggle_btn), relief=FLAT, bg="lightblue")
    toggle_btn.grid(row=1, column=2, padx=5)

    Button(frame, text="Login", command=admin_login, bg="green", fg="white", font=("Arial", 14)).grid(row=2, column=0, columnspan=3, pady=20)
    Button(frame, text="Back to User Login", command=show_login, bg="blue", fg="white", font=("Arial", 14)).grid(row=3, column=0, columnspan=3)


# Functions for the AI dashboard
# Functions for the AI dashboard 


def show_ai_dashboard(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    # Modern color scheme
    PRIMARY_COLOR = "#2962ff"  # Vibrant Blue
    SECONDARY_COLOR = "#00c853"  # Fresh Green
    BG_COLOR = "#f5f5f5"  # Light Gray
    CARD_BG = "#ffffff"  # White
    TEXT_COLOR = "#263238"  # Dark Gray
    ACCENT_COLOR = "#ff3d00"  # Bright Orange

    # Configure root window
    root.configure(bg=BG_COLOR)
    root.geometry("1400x900")
    root.title("AI Learning Assistant")

    # Create main container
    main_frame = Frame(root, bg=BG_COLOR)
    main_frame.pack(fill=BOTH, expand=True)

    # Create modern header with gradient effect
    header_frame = Frame(main_frame, bg=PRIMARY_COLOR, height=120)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    # Welcome message with modern typography
    Label(
        header_frame,
        text=f"Welcome, {user_name}!",
        font=("Helvetica", 28, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(side=LEFT, padx=40, pady=35)

    # Navigation buttons frame
    nav_frame = Frame(header_frame, bg=PRIMARY_COLOR)
    nav_frame.pack(side=RIGHT, padx=40, pady=35)

    # Create styled button function
    def create_nav_button(text, command, color):
        return Button(
            nav_frame,
            text=text,
            command=command,
            font=("Helvetica", 12, "bold"),
            bg=color,
            fg="white",
            relief=FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=color,
            activeforeground="white"
        )

    # Add navigation buttons
    history_btn = create_nav_button("📊 History", 
        lambda: show_history_dashboard(user_id, user_name), 
        SECONDARY_COLOR
    )
    history_btn.pack(side=LEFT, padx=10)

    logout_btn = create_nav_button("🚪 Logout", show_login, ACCENT_COLOR)
    logout_btn.pack(side=LEFT, padx=10)

    # Create content area
    content_frame = Frame(main_frame, bg=BG_COLOR)
    content_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    # Left panel - Chat Interface
    chat_frame = Frame(content_frame, bg=CARD_BG, relief=GROOVE, bd=1)
    chat_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 20))

    # Chat header
    chat_header = Frame(chat_frame, bg=PRIMARY_COLOR, height=50)
    chat_header.pack(fill=X)
    chat_header.pack_propagate(False)

    Label(
        chat_header,
        text="AI Assistant Chat",
        font=("Helvetica", 14, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(pady=12)

    # Chat display
    chat_display = Text(
        chat_frame,
        wrap=WORD,
        font=("Helvetica", 12),
        bg=CARD_BG,
        fg=TEXT_COLOR,
        padx=20,
        pady=20,
        relief=FLAT,
        height=20
    )
    chat_display.pack(fill=BOTH, expand=True, padx=2, pady=2)
    
    # Configure tags for different message types
    chat_display.tag_configure("user", foreground="#2962ff", font=("Helvetica", 12, "bold"))
    chat_display.tag_configure("ai_prefix", foreground="#00c853", font=("Helvetica", 12, "bold"))
    chat_display.tag_configure("ai_response", foreground="#263238", font=("Helvetica", 12))
    
    # Custom scrollbar
    scrollbar = Scrollbar(chat_display)
    scrollbar.pack(side=RIGHT, fill=Y)
    chat_display.configure(yscrollcommand=scrollbar.set)
    scrollbar.configure(command=chat_display.yview)

    # Input area
    input_frame = Frame(chat_frame, bg=CARD_BG, height=100)
    input_frame.pack(fill=X, pady=2)

    # Modern input field
    user_input = Entry(
        input_frame,
        font=("Helvetica", 12),
        bg="#f8f9fa",
        fg=TEXT_COLOR,
        relief=FLAT,
        bd=1
    )
    user_input.pack(fill=X, expand=True, padx=20, pady=20, ipady=8)

    # Send button
    send_btn = Button(
        input_frame,
        text="Send ➤",
        command=lambda: process_input(user_input.get(), chat_display, user_input, user_id),
        font=("Helvetica", 12, "bold"),
        bg=PRIMARY_COLOR,
        fg="white",
        relief=FLAT,
        padx=30,
        pady=8,
        cursor="hand2"
    )
    send_btn.pack(side=RIGHT, padx=20, pady=(0, 20))

    # Right panel - Quick Actions
    actions_frame = Frame(content_frame, bg=CARD_BG, width=300, relief=GROOVE, bd=1)
    actions_frame.pack(side=RIGHT, fill=Y)
    actions_frame.pack_propagate(False)

    # Quick actions header
    actions_header = Frame(actions_frame, bg=PRIMARY_COLOR, height=50)
    actions_header.pack(fill=X)
    actions_header.pack_propagate(False)

    Label(
        actions_header,
        text="Quick Actions",
        font=("Helvetica", 14, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(pady=12)

    # Quick action buttons
    def create_action_button(text, icon, command):
        btn_frame = Frame(actions_frame, bg=CARD_BG)
        btn_frame.pack(fill=X, padx=20, pady=10)
        
        Button(
            btn_frame,
            text=f"{icon} {text}",
            command=command,
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            relief=FLAT,
            padx=10,
            pady=8,
            cursor="hand2",
            anchor="w",
            width=25
        ).pack(fill=X)

    def start_new_topic(chat_display):
        chat_display.configure(state="normal")
        chat_display.delete(1.0, END)
        chat_display.insert(END, "AI Assistant: Hello! What Java topic would you like to discuss?\n\n")
        chat_display.configure(state="disabled")

    def view_progress(user_id):
        cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
        total_questions = cursor.fetchone()[0]
        messagebox.showinfo("Learning Progress", 
            f"Your Progress:\n"
            f"Total Questions Asked: {total_questions}\n"
            f"Keep learning and asking questions to improve!")

    def show_practice_questions():
        practice_window = Toplevel()
        practice_window.title("Practice Questions")
        practice_window.geometry("800x600")
        practice_window.configure(bg="#f5f5f5")

        # Header with gradient effect
        header_frame = Frame(practice_window, bg="#2962ff", height=80)
        header_frame.pack(fill=X)
        header_frame.pack_propagate(False)

        Label(
            header_frame,
            text="Java Practice Exercises",
            font=("Helvetica", 24, "bold"),
            bg="#2962ff",
            fg="white"
        ).pack(pady=20)

        # Main content area
        content_frame = Frame(practice_window, bg="#f5f5f5")
        content_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

        practice_questions = [
            {
                "title": "Hello World Program",
                "description": "Write a simple Hello World program in Java",
                "hint": "Use System.out.println()",
                "difficulty": "Easy"
            },
            {
                "title": "Class Creation",
                "description": "Create a class with main method",
                "hint": "public class MyClass { public static void main(String[] args) { } }",
                "difficulty": "Easy"
            },
            {
                "title": "Variable Declaration",
                "description": "Declare variables of different data types",
                "hint": "int, double, String, boolean",
                "difficulty": "Easy"
            },
            {
                "title": "Object Creation",
                "description": "Create an object of a class",
                "hint": "ClassName objectName = new ClassName();",
                "difficulty": "Medium"
            },
            {
                "title": "Control Flow",
                "description": "Implement a basic if-else statement",
                "hint": "if (condition) { } else { }",
                "difficulty": "Medium"
            }
        ]

        def show_hint(hint_text):
            hint_window = Toplevel()
            hint_window.geometry("400x200")
            hint_window.title("Hint")
            hint_window.configure(bg="#f5f5f5")
            
            Label(
                hint_window,
                text="💡 Hint",
                font=("Helvetica", 16, "bold"),
                bg="#f5f5f5",
                fg="#2962ff"
            ).pack(pady=20)
            
            Label(
                hint_window,
                text=hint_text,
                font=("Helvetica", 12),
                bg="#f5f5f5",
                fg="#263238",
                wraplength=350
            ).pack(pady=10)

        for i, question in enumerate(practice_questions, 1):
            # Card frame for each question
            card = Frame(content_frame, bg="white", relief=GROOVE, bd=1)
            card.pack(fill=X, pady=10, ipady=10)
            
            # Difficulty badge
            difficulty_colors = {"Easy": "#00c853", "Medium": "#ff9800", "Hard": "#f44336"}
            difficulty_frame = Frame(card, bg=difficulty_colors[question["difficulty"]])
            difficulty_frame.pack(side=RIGHT, padx=20)
            
            Label(
                difficulty_frame,
                text=question["difficulty"],
                font=("Helvetica", 10, "bold"),
                bg=difficulty_colors[question["difficulty"]],
                fg="white",
                padx=10,
                pady=5
            ).pack()

            # Question number and title
            Label(
                card,
                text=f"{i}. {question['title']}",
                font=("Helvetica", 14, "bold"),
                bg="white",
                fg="#2962ff"
            ).pack(side=LEFT, padx=20)

            # Description
            Label(
                card,
                text=question["description"],
                font=("Helvetica", 12),
                bg="white",
                fg="#263238"
            ).pack(side=LEFT, padx=20)

            # Hint button
            Button(
                card,
                text="Show Hint",
                command=lambda h=question["hint"]: show_hint(h),
                font=("Helvetica", 10),
                bg="#e3f2fd",
                fg="#2962ff",
                relief=FLAT,
                padx=15,
                pady=5,
                cursor="hand2"
            ).pack(side=RIGHT, padx=20)

    def show_settings(root):
        settings_window = Toplevel()
        settings_window.title("Settings")
        settings_window.geometry("500x700")
        settings_window.configure(bg="#f5f5f5")

        # Header with gradient effect
        header_frame = Frame(settings_window, bg="#2962ff", height=80)
        header_frame.pack(fill=X)
        header_frame.pack_propagate(False)

        Label(
            header_frame,
            text="Settings",
            font=("Helvetica", 24, "bold"),
            bg="#2962ff",
            fg="white"
        ).pack(pady=20)

        # Main content area with cards
        content_frame = Frame(settings_window, bg="#f5f5f5")
        content_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

        def create_settings_card(title, options, icon):
            card = Frame(content_frame, bg="white", relief=GROOVE, bd=1)
            card.pack(fill=X, pady=10, ipady=15)
            
            # Card header
            header = Frame(card, bg="white")
            header.pack(fill=X, padx=20, pady=(15,20))
            
            Label(
                header,
                text=icon,
                font=("Helvetica", 20),
                bg="white",
                fg="#2962ff"
            ).pack(side=LEFT)
            
            Label(
                header,
                text=title,
                font=("Helvetica", 16, "bold"),
                bg="white",
                fg="#263238"
            ).pack(side=LEFT, padx=10)
            
            # Options
            options_frame = Frame(card, bg="white")
            options_frame.pack(fill=X, padx=20)
            
            for option in options:
                Button(
                    options_frame,
                    text=option,
                    font=("Helvetica", 12),
                    bg="#f8f9fa",
                    fg="#263238",
                    relief=FLAT,
                    padx=20,
                    pady=8,
                    cursor="hand2",
                    activebackground="#e3f2fd",
                    activeforeground="#2962ff"
                ).pack(side=LEFT, padx=5)

        # Theme settings
        create_settings_card("Theme", ["Light", "Dark", "System"], "🎨")
        
        # Font settings
        create_settings_card("Font Size", ["Small", "Medium", "Large"], "📝")
        
        # Language settings
        create_settings_card("Language", ["English", "Hindi", "Spanish"], "🌐")
        
        # Notification settings
        create_settings_card("Notifications", ["On", "Off"], "🔔")
        
        # Save button
        Button(
            settings_window,
            text="Save Changes",
            font=("Helvetica", 14, "bold"),
            bg="#2962ff",
            fg="white",
            relief=FLAT,
            padx=30,
            pady=10,
            cursor="hand2",
            activebackground="#1e88e5",
            activeforeground="white"
        ).pack(pady=30)

    create_action_button("Start New Topic", "🆕", lambda: start_new_topic(chat_display))
    create_action_button("View Progress", "📈", lambda: view_progress(user_id))
    create_action_button("Practice Questions", "✍️", show_practice_questions)

    # Bind Enter key to send message
    user_input.bind("<Return>", lambda event: process_input(user_input.get(), chat_display, user_input, user_id))

    # Set focus to input field
    user_input.focus_set()

    # Add initial greeting to chat
    chat_display.insert(END, "AI Assistant: Hello! How can I help you today?\n\n")
    chat_display.configure(state="disabled")

    # Questions and answers training 
    questions = [
       "what is a java or define a java",
        "what is the uses of java",
        "write a program of hello world",
        "what is the features of java",
        "what is the data types in java",
        "write a program of variable",
        "what is the operators in java",
        "what is the variable in java",
        "what is the constant",
        "write a program of unary operator",
        "write a program of arithmetic operator",
        "write a program of bitwsie operator",
        "write a program of logical operator",
        "what is the comments in java",
        "write a program of addition of two numbers using java",
        "write a program of addition of three numbers using java",
        "what is the structure of java program",
        "write a program of fibonacci using java",
        "write a program of palindrome number using java",
        "write a program of prime number using java",
        "write a program of sum of digits number using java",
        "write a program of reverse number using java",
        "what is the jdk tools in java",
        "what is command line argument",
         "what is the arrays in java",
         "what is the types of arrays",
         "write a program of one dimesional array",
         "write a program of two dimesional array ",
         "write a program of multidimesional array",
         "what is the string",
         "what is the basic syntax of java",
         "what is the main method in java",
         "what is the print statement in java",
         "what is the System.out.println in java",
         "what is the scanner class in java",
        "write a program of java print numbers",
        "how to declare variable in java",
        "what is the final variable in java",
        "what is the print or display variable in the java",
        "what is the java declare multiple variables in the java",
        "what is the java identifiers in java",
        "write a simple program of students display name,id,age,fee,grade",
        "what is the primitive data types in the java",
        "what is the java numbers in the java",
        "what is the integers types in the java",
        "write a program of byte using java",
        "write a program of java using short data type",
        "write a java program using int data type",
        "write a java program using long data type", 
        "write a java program using float data type",
        "write a java program using double data type",
        "write a java program using scientific numbers",
        "what is the boolean in the java",
        "how to display output in the java",
        " What is the class in Java? Provide an example.",
    " What is the object in Java? Demonstrate object creation with an example.",
    " How do you create multiple objects of the same class? Provide an example.",
    " How can you initialize object properties using a constructor?",
    " What is the difference between instance variables and local variables? Provide an example.",
    "How do you use the 'this' keyword in Java? Provide an example.",
    " What is the method overloading in Java? Provide an example.",
    " How can you access class attributes and methods using objects?",
    " How do you define and call instance methods in Java?",
    " What is the role of the 'new' keyword in Java?",
    "what is the if else statement in java",
    "how if else statement work in java",
    "write a program leap year using java",
    "what is the if else ladder statement",
    "write a Java program that takes a student's marks as input and determines their grade",
    "write a program positive and negative using java",
    "what is the  ternary operator in java",
    "what is the switch statement in java",
    "write a program of switch case and print weeks name using java eg. monday to sunday",
    "what is the break keyword in the java",
    "what is the default keyword in the java",
    "what is the loop in java",
    "what is the types of loops in java",
    "what is the do while loop in java",
    "write a simple program of while loop in java",
    "write a simple program of do while loop in java",
    "what is the for loop in java",
    "what is break statement in java",
    "what is continue statement in java",
    "what is the while loop in java",
    "what is the java methods in java",
    "what is the java parameters in java",
    "what is the arguments in java",
    "what is the return values in java",
    "what is the method overloading in java",
    "write a simple program of method overloading using java",
    "What is the methods scope in Java, and how does it affect variable visibility",
    "what is the java recursion in java",
    "what is the oop in java",
    "what is the classes in java",
    "what is the class in java",
    "how to create class in java",
    "what is the objects in java",
    "how to create objects in java",
    "what is the classes and objects in java",
    "how to create classes and objects in java",
    "what is the multiple objects in java",
    "what is the multiple classes in java",
    

        
         
        
    ]

    answers = [
       """
        # Java Introduction
        1] Java is a class-based, object-oriented, simple programming language.
        2] Java is a high-level language.
        3] Java makes writing, compiling, and debugging easy.
        4] It helps to create reusable code and modular programs.
        """,


"""
   # Uses of Java
        Java is a versatile, object-oriented programming language that is widely used across various domains. Here are some of the primary uses of Java:

### 1. **Web Development**
   - Java is used to build dynamic and scalable web applications.
   - Frameworks like **Spring**, **Hibernate**, and **JavaServer Faces (JSF)** are popular for backend development.
   - Servlets and JavaServer Pages (JSP) are used for server-side programming.

### 2. **Mobile App Development**
   - Java is the primary language for developing **Android applications**.
   - Android Studio, the official IDE for Android development, uses Java (along with Kotlin).

### 3. **Enterprise Applications**
   - Java is a cornerstone of enterprise software development.
   - Platforms like **Java EE (Jakarta EE)** provide APIs for building large-scale, distributed systems.
   - Used in banking, insurance, and e-commerce industries for robust and secure applications.

### 4. **Desktop Applications**
   - Java can be used to create cross-platform desktop applications using frameworks like **JavaFX** and **Swing**.
   - Tools like **Apache Poi** are used for working with Microsoft Office files.

### 5. **Big Data Technologies**
   - Java is heavily used in big data processing frameworks like **Hadoop**, **Apache Spark**, and **Apache Flink**.
   - Libraries like **Apache Mahout** and **Deeplearning4j** are used for machine learning and data analysis.

### 6. **Cloud-Based Applications**
   - Java is widely used in cloud computing and microservices architecture.
   - Platforms like **Google Cloud**, **AWS**, and **Microsoft Azure** support Java for building and deploying applications.

### 7. **Internet of Things (IoT)**
   - Java's platform independence makes it suitable for IoT devices.
   - Frameworks like **Eclipse IoT** and **Java ME (Micro Edition)** are used for IoT development.

### 8. **Scientific Applications**
   - Java is used in scientific computing and research due to its robustness and performance.
   - Libraries like **Apache Commons Math** and **JScience** are used for mathematical and scientific computations.

### 9. **Game Development**
   - Java is used to develop games, especially for Android platforms.
   - Game engines like **LibGDX** and **jMonkeyEngine** 
        
        """,

        """
        # Hello World Program
        public class Main {
            public static void main(String[] args) {
                System.out.println("Hello, World!");
            }
        }
        """,

        """
        # Features of Java
       
Java is a widely-used, versatile, and powerful programming language known for its simplicity, portability, and robustness. 
It was developed by Sun Microsystems (now owned by Oracle Corporation) in 1995. 
Below are the key **features of Java** that make it one of the most popular programming languages in the world:

---

### 1. **Platform Independence (Write Once, Run Anywhere - WORA)**
   - Java programs are platform-independent because they are compiled into **bytecode**, which can be executed on any platform with a **Java Virtual Machine (JVM)**.
   - This feature allows Java programs to run on any device or operating system (Windows, Linux, macOS, etc.) without modification.

---

### 2. **Object-Oriented Programming (OOP)**
   - Java is a purely object-oriented language (except for primitive data types).
   - It supports key OOP concepts such as:
     - **Encapsulation**: Bundling data and methods into a single unit (class).
     - **Inheritance**: Creating new classes from existing ones.
     - **Polymorphism**: Allowing objects to take multiple forms (e.g., method overriding).
     - **Abstraction**: Hiding implementation details and showing only functionality.

---

### 3. **Simple and Easy to Learn**
   - Java has a syntax similar to C and C++, but it eliminates complex features like pointers and multiple inheritance.
   - It is designed to be beginner-friendly and easy to understand.

---

### 4. **Robust and Secure**
   - **Robust**: Java has strong memory management, exception handling, and type-checking mechanisms, which make it reliable and less prone to crashes.
   - **Secure**: Java provides a secure runtime environment (JVM) with features like:
     - Bytecode verification.
     - Sandboxing (restricting applets from accessing system resources).
     - No explicit use of pointers, which prevents memory corruption.

---

### 5. **Multithreading**
   - Java has built-in support for **multithreading**, allowing concurrent execution of two or more threads for maximum utilization of CPU.
   - This is useful for developing highly responsive and interactive applications.

---

### 6. **Distributed Computing**
   - Java provides libraries and tools (e.g., **RMI**, **CORBA**, and **Java Networking API**) for building distributed applications.
   - It supports communication over the internet using protocols like HTTP and FTP.

---

### 7. **High Performance**
   - Java uses **Just-In-Time (JIT)** compilation, which converts bytecode into native machine code at runtime, improving performance.
   - While not as fast as low-level languages like C or C++, Java is still highly performant for most applications.

---

### 8. **Automatic Memory Management (Garbage Collection)**
   - Java has an automatic garbage collection mechanism that automatically deallocates memory for objects that are no longer in use.
   - This eliminates the need for manual memory management and reduces the risk of memory leaks.


        """,
        
        """
        # Data types 
        1] Data type is a term that refers to the kind of data used.
        2] Different data types in Java:
        - byte
        - short
        - int
        - long
        - float
        - double
        - boolean
        """,
        
        """
        # Variable Program
        public class Main {
            public static void main(String[] args) {
                int num1 = 50;
                int num2 = 15;
                int sum;
                sum = num1 + num2;
                System.out.println("Sum of numbers: " + sum);
            }
        }
        """,
        
        """
        # Operators in Java
        1] Unary operators:
        - + (unary plus operator)
        - - (unary minus operator)
        - ++ (Increment operator)
        - -- (Decrement operator)
        - ! (Logical complement operator)
        
        2] Arithmetic operators:
        - + (Additive operator)
        - - (Subtraction operator)
        - * (Multiplication operator)
        - / (Division operator)
        - % (Remainder operator)
        
        3] Bitwsie and Bit shift operators 
        - ~ (Unary operator)
        - << (Signed left shift)
        - >>> (Signed right shift)
        - & (Bitwsie AND)
        - ^ (Bitwise exclusive OR)
        - |  (Bitwsie inclusive OR)
        
        4] Logical operators:
         - &&  (Logical AND)
         - ||  (Logical OR)
        """,
        
        """
        # Variable 
        
    Variables are the containers for storing the data values or you can also call it a memory location name for the data. Every variable has a:

    Data Type – The kind of data that it can hold. For example, int, string, float, char, etc.
    Variable Name – To identify the variable uniquely within the scope.
    Value – The data assigned to the variable.
        """,
        
        """
        # Constant 
        
        1] A value which is fixed and does not change 
        
        2] during the execution of a program is called constants
        
        3] Constants values are fixed . 
        """,
        
        """
        # Program unary operator 
        public class unary{
            public static void main(String args[])
            {
                int a = 10;
                System.out.println(a++);
                System.out.println(++a);
                System.out.println(a--);
                System.out.println(--a);    
            }
        }
        """,
        
        """
        # Arithmetic operator
        
        public class Arithmetic
        {
            public static void main(String args[])
            {
                int a=20;
                int b= 10;
                
                System.out.println(a+b);
                System.out.println(a-b);
                System.out.println(a*b);
                System.out.println(a/b);
            
            }
        }
        """,
        
        """
        # Bitwise and Bit shift operators 
        public class Bitwise
        {
            public static void main(String args[])
            {
                int a=20;
                int b=10;
                int c=5;
                
                System.out.println(20<<2);
                System.out.println(20>>2);
                System.out.println(a<b&a<<c);
            }
        }
        """,
        
        """
        # Logical operator
        
        public class Logical
        {
            public static void main(String args[])
            {
                int a=10;
                int b=5;
                int c=20;
                
                System.out.println(a<b && a<c);
                System.out.println(a<b || a<c);
            }
        }
        
        """,
        
        """
        # Comments in Java
        
        1] Comments are non-executable statements and are ignored by java compiler.
        2] Comments increases the readability of the programs.
        3] Comments are an integral part of any program.
        4] There are three types of comments 
        
        5] 
           i] Line Comments:
            - It start with two forward slashes (//)
            -  and continue to the end of the current line.
            - Line comments are proved useful for supplying short explnations for variables.
            
            
           ii] Block Comments:
           - Java's multi-line or slash-star or traditional comments is a piece of text
           - enclosed in slash-star(/*)  and  star-slash(*/)
           
           Example: /* This is Multi line comment */
           
           
           iii] Javadoc Comments:
           - Javadoc comments are used to document the new classes
           - you create as a programmer.
           - i.e. provide information about the class for users of the class to read
           
           Example: /** Welcome in Java AI Teacher */        
        """,
        
        
        """
        # Addition of two numbers
        
                public class Main
        {
            public static void main(String args[])
            {
                int a=10;
                int b=5;
                int c = a+b;
                
                System.out.println("Addition is:"+ c);
            
            }
        }
        
        """,
        
        
        """
        # Addition of 3 numbers
        
                public class Main
        {
            public static void main(String args[])
            {
                int a=10;
                int b=5;
                int c=20;
                int d = a+b+c;
                
                System.out.println("Addition is:"+d);
            }
        }
        """,
        
        
        """
        # Structure of Java program 
        
        1] Documentation Section:
            This section is a set of comment lines giving the name of the 
            program, the author and the other details, which the programmer would
            like to refer.
          
            
        2] Package statements:
            In Java files, the first statement allowed is a package statement.
            this statement declares a package name and informs the compiler that
            
            for example: package employee;
            
            
       3]  Import statement:
            Similar to #include statement in c.
            
            for example , import employee.test;
            
            
       4]  Interface statement:
            An interface is like class but includes group of methods
            declaration. Interfaces are used when we want to implement
            mulitple inheritance feature.
            
            
       5]  Class Definition:
            Java program may contain many/multiple  class definition.
            classes are primary feature of java program. the classes in
            java are used to map real-world problems.
            
            
       6]   Main Method class :
            Java stand-alone program requires main method as starting
            point that is essential part of program main() method in java
            program creates object various classes and on reaching , end of the main
            the program terminate.
            
            
            First Java Program:
            public class Myprogram
            {
                public static void main(String args[])
                {
                    System.out.println("My First Java program");
                }
            }              
                
        """,
        
        
        """
        # Program of Fibonacci
        
        public class Fibonacci {
    public static void main(String[] args) {
        int n = 10; // Number of terms to display
        int first = 0, second = 1;

        System.out.println("Fibonacci Series up to " + n + " terms:");
        for (int i = 1; i <= n; i++) {
            System.out.print(first + " ");
            int next = first + second;
            first = second;
            second = next;
        }
    }
}

        """,
        
        
        """
        # Program of Palindrome 
        public class PalindromeCheck {
    public static void main(String[] args) {
        int number = 12321; // Number to check
        int originalNumber = number;
        int reverse = 0;

        while (number != 0) {
            int digit = number % 10;
            reverse = reverse * 10 + digit;
            number /= 10;
        }

        if (originalNumber == reverse) {
            System.out.println(originalNumber + " is a palindrome.");
        } else {
            System.out.println(originalNumber + " is not a palindrome.");
        }
    }
}

        """,
        
        
      """
      #Prime number 
      
      public class PrimeCheck {
    public static void main(String[] args) {
        int number = 29; // Number to check
        boolean isPrime = true;

        if (number <= 1) {
            isPrime = false;
        } else {
            for (int i = 2; i <= Math.sqrt(number); i++) {
                if (number % i == 0) {
                    isPrime = false;
                    break;
                }
            }
        }

        if (isPrime) {
            System.out.println(number + " is a prime number.");
        } else {
            System.out.println(number + " is not a prime number.");
        }
    }
}

      """,
      
      
      
      """
      # Sum of digits 
      
      public class SumOfDigits {
    public static void main(String[] args) {
        int number = 12345; // Number to find sum of digits
        int sum = 0;

        while (number != 0) {
            int digit = number % 10;
            sum += digit;
            number /= 10;
        }

        System.out.println("Sum of Digits: " + sum);
    }
}

      """  ,
      
      
      
      """
      # Reverse number
      
      public class ReverseNumber {
    public static void main(String[] args) {
        int number = 12345; // Number to reverse
        int reverse = 0;

        while (number != 0) {
            int digit = number % 10;
            reverse = reverse * 10 + digit;
            number /= 10;
        }

        System.out.println("Reversed Number: " + reverse);
    }
}

      """,
      
      """
      # JDK Tools in Java
      
      - The JDK is a software development environment which is used to
      develop java applications and applets.
      
      -JDK(Java Development Kit) provides environment to develop and run java
      applications.
      
      - The JDK comes with a set of tools that are used for developing and running
      java program it includes.
      
      
      1] Javac : It is a Java compiler.
      
      2] Java : It is a Java interpreter.
      
      3] Javah : It is for java c header files.
      
      4] jdb : It is a java debugger.
      
      5] AppletViewer: It is used for viewing the applet.
      
      6]  Javap: Java disassembler, which convert the byte code into program
      description.
      
      7]  Javadoc: It is used for creating HTML document. 
      """,
      
      """
      # Command Line
      
    -  Sometimes you will want to pass information into a program
      when you run it. This is accomplished by passing command line
      argument to main().
      
   -  A command line argument is the information that directly follows the program
      name on the command line when it is executed.
      
      
    - To access the command line arguments inside a java program is quite easy
    there are stored as strings in a string array passed to the args parameter of 
    main(). The first command line argument is stored at args[0] , the second 
    at args[1] , and so on.  
      """,
      
      """
      # Array in Java
      
     - An array is a group of similar type variables that are referred to by a
     common name. 
     
     - A specific element in an array is accessed by its index. Arrays offer a convenient
     means of grouping realted information.
     
     
     - Java provides a data structure, the array, which stores a fixed-sized sequential
     collection of elements of the same type. An array is used to stored a collection of 
     data. but it is often more useful to think of an array as a collection of variables
     of the same type.
     
     - Array is a contiguous fixed-length structure for storing multiple values of the 
     same type Array. 
      """,
      
      
      """
      # Types of array.
      
      1] Single Dimensional (1 D) Array
      
      - An array is a sequence of variables of the same data type. Array
       having only one subscript variable is called One-Dimensional array.
       
    
     - It is also called as Single-Dimensional array.
     
     
     - A one dimesional array is , essentiallly a list of similar type variables. to
     create an array, you first must create an array variable of the desired type.
     
     
     - To declare an array , you specify the name of the array and the data type, as you
     would for any other variable. Adding an empty set of brackets([]) indicates that the variable is an 
     array.
     
     
     2]  Multi Dimesional (2 D) Array
     
     - In Java, multi-dimesional arrays are actually arrays of arrays. These arrays
     look and act like regular multi-dimesional arrays.
     
     - to declare a multi- dimesional array variable, specify each additional index using another
     set of square brackets. for example, the following declares a two-dimesional array variable called
     twoD.
      """,
      
      
      """
      #One dimesional array

        import java.util*;
        class arraydemo
        {
            public static void main(String args[])
            {
                int a[] = {2,4,6,3,1};
                System.out.println("Number of elements in array+a.length);
                System.out.println("Elements in array a"+a.length);
                
                for(int i=0;i<a.length;i++)
                {
                    System.out.println(a[i]+ "\t")
                }
            }
        }
      """,
      
      """
      # Two dimesional array
      
      class Testarray
      {
          
          // creating two matrices
          
          int a[][] ={{1,3,4}, {3,4,5}};
          int b[][] = {{1,3,4},{3,4,5}};
          
          int c[][] = new int[2][3];
          
          // adding and printing addition of two matrices
          for(int i=0;i<2;i++)
          {
              for(int j=0;j<3;j++)
              {
                  c[i][j]=a[i][j]+ b[i][j];
                  System.out.print(c[i][j]+ "");
              }
              
              System.out.println();
          }
      }
      """,
      
      
      """
      # Multidimesional array
      
      class TwoDArray
      {
          public static void main(String args[])
          {
              int twoD[][]= new int[4][5];
              int i,j,k=0;
              for(i=0;i<4;i++)
              {
                  for(j=0;j<5;j++)
                  {
                      twoD[i][j] = k;
                      k++;
                  }
                  
                  for(i=0;i<4;i++)
                  {
                      for(j=0;j<5;j++)
                      
                      System.out.println(twoD[i][j]+"");
                      System.out.println();
                  }
              }
          }
      }
      """,
      
      
      """
      #String
      
      - The strings in java are treated as objects of type 'string' class.
      This class is present in the package java.lang.
      
      
      - This package contains two string classes:
       1. String class, and
       2. StringBuffer class.
       
       
       - The String class is used when we work with the string which cannot change whereas
       stringBuffer class is used when we want to mainpulate the contents of the string
      """,
      
      """
      
      # Basic Syntax of Java
      
      // This is a single-line comment

       /* This is a 
       multi-line comment */
 
     public class MyClass { // Class declaration

     public static void main(String[] args) { // Main method
        System.out.println("Hello, World!"); // Print statement
     }
     }
      """,
      
      
      """
      # Main method in java
      
      The main() method is required and you will see it in every Java program:
      
    public static void main(String[] args)

Any code inside the main() method will be executed. Don't worry about the keywords before and after it. You will get to know them bit by bit while reading this tutorial.

For now, just remember that every Java program has a class name which must match the filename, and that every program must contain the main() method
      """,
      
      
   """
   # Print statement in java
   System.out.println()

  Inside the main() method, we can use the println() method to print a line of text to the screen:

  public static void main(String[] args) {
   System.out.println("Hello World");
   }

   """,   
    
    
    """
   # System.out.println() in java
   System.out.println()

  Inside the main() method, we can use the println() method to print a line of text to the screen:

  public static void main(String[] args) {
   System.out.println("Hello World");
   }

   """,
   
   
   """
   # Scanner class in java
   
   The **Scanner** class in Java, part of the `java.util` package, 
   it is used to take input from various sources like the keyboard, 
   files, or strings. It provides methods to read and parse data of different types such as integers, floats, strings, and more.

 Example Program 
import java.util.Scanner;

public class ScannerExample {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in); // Create Scanner object
        System.out.println("Enter your name:");
        String name = scanner.nextLine(); // Read a string input
        System.out.println("Enter your age:");
        int age = scanner.nextInt(); // Read an integer input
        
        System.out.println("Hello " + name + ", you are " + age + " years old.");
        scanner.close(); // Close the scanner to prevent resource leak
    }
}
```

### Explanation
1. **`Scanner scanner = new Scanner(System.in);`**: Initializes the Scanner to take input from the keyboard.
2. **`scanner.nextLine();`**: Reads a full line of text.
3. **`scanner.nextInt();`**: Reads an integer.
4. **`scanner.close();`**: Closes the scanner to free resources.

This makes `Scanner` a versatile tool for handling user input.
   """,
   
   
   """
   
   # Print Numbers

  You can also use the println() method to print numbers.
  However, unlike text, we don't put numbers inside double quotes:

  Example

  public class Main {
  public static void main(String[] args) {
  System.out.println(3);
  System.out.println(358);
  System.out.println(50000);
  }
  }

""",

"""
# declaring variables in java
Declaring (Creating) Variables

To create a variable, you must specify the type and assign it a value:
Syntax

type variableName = value;

Where type is one of Java's types (such as int or String), and variableName is the name of the variable (such as x or name).
The equal sign is used to assign values to the variable.

To declare a variable that should store text, look at the following example:
Example

Create a variable called name of type String and assign it the value "John".
Then we use println() to print the name variable:

String name = "John";
System.out.println(name);

""",

"""
# Final variable in java


In Java, a final variable is a variable whose value cannot be changed once it has been initialized. It's essentially a constant.
Here's what you need to know:

    Declaration: To declare a final variable, use the final keyword before the variable's data type: 

Java

final int MAX_VALUE = 100; 

    Initialization:
    A final variable must be initialized either at the time of declaration or within a constructor if it's an instance variable.
    Benefits:
        Readability: Using final makes your code easier to understand by clearly indicating that a variable's value is constant.
        Security: It prevents accidental modification of values that should remain constant.
        Optimization: The compiler can sometimes optimize code that uses final variables. 
    Common Use Cases:
        Constants: final is frequently used to define constants like mathematical values (e.g., PI) or configuration settings.
        Immutable Objects: You can use final to create immutable objects, ensuring that their state cannot be changed after they are created. 


""",

"""
# Java print or display variable

Display Variables

The println() method is often used to display variables.

To combine both text and a variable, use the + character:


Example:

public class Main {
    public static void main(String[] args) {
        String name = "John";
        System.out.println("Hello " + name);
    }
}

""",


"""
# Multiple variables

Declare Many Variables

To declare more than one variable of the same type, you can use a comma-separated list:


public class Main {
  public static void main(String[] args) {
    int x = 5, y = 6, z = 50;
    System.out.println(x + y + z);
  }
}

""",


"""
# Java identifier

Identifiers

All Java variables must be identified with unique names.

These unique names are called identifiers.

Identifiers can be short names (like x and y) or more descriptive names (age, sum, totalVolume).

Note: It is recommended to use descriptive names in order to create understandable and maintainable code:



Example

public class Main {
  public static void main(String[] args) {
    // Good
    int minutesPerHour = 60;

    // OK, but not so easy to understand what m actually is
    int m = 60;
    
    System.out.println(minutesPerHour);
    System.out.println(m);
  }
}

""",


"""
# Student simple program

public class Main {
  public static void main(String[] args) {
    // Student data
    String studentName = "John Doe";
    int studentID = 15;
    int studentAge = 23;
    float studentFee = 75.25f;
    char studentGrade = 'B';
    
    // Print variables
    System.out.println("Student name: " + studentName);
    System.out.println("Student id: " + studentID);
    System.out.println("Student age: " + studentAge);
    System.out.println("Student fee: " + studentFee);
    System.out.println("Student grade: " + studentGrade);
  }
}

""",


"""
# Primitive data types


Primitive Data Types

A primitive data type specifies the type of a variable and the kind of values it can hold.

There are eight primitive data types in Java:
Data Type 	Description
byte 	    Stores whole numbers from -128 to 127
short 	    Stores whole numbers from -32,768 to 32,767
int 	    Stores whole numbers from -2,147,483,648 to 2,147,483,647
long 	    Stores whole numbers from -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807
float 	    Stores fractional numbers. Sufficient for storing 6 to 7 decimal digits
double 	    Stores fractional numbers. Sufficient for storing 15 to 16 decimal digits
boolean 	Stores true or false values
char 	    Stores a single character/letter or ASCII values
""",


"""
# Java numbers

Numbers

Primitive number types are divided into two groups:

Integer types stores whole numbers, positive or negative (such as 123 or -456), without decimals. Valid types are byte, short, int and long. Which type you should use, depends on the numeric value.

Floating point types represents numbers with a fractional part, containing one or more decimals. There are two types: float and double.
""",

"""
# Integers types

Integer Types
Byte

The byte data type can store whole numbers from -128 to 127. This can be used instead of int or other integer types to save memory when you are certain that the value will be within -128 and 127:
""",


"""
# Integers program

public class Main {
  public static void main(String[] args) {
    byte myNum = 100;
    System.out.println(myNum);  
  }
}

""",


"""
The short data type can store whole numbers from -32768 to 32767:

# short data type program

public class Main {
  public static void main(String[] args) {
    short myNum = 5000;
    System.out.println(myNum);  
  }
}

""",


"""
# Int data types program

The int data type can store whole numbers from -2147483648 to 2147483647. 
In general, and in our tutorial, the int data type is the preferred data type when we create variables with a numeric value.


public class Main {
  public static void main(String[] args) {
    int myNum = 100000;
    System.out.println(myNum);  
  }
}

""",

"""
# Long data type

The long data type can store whole numbers from -9223372036854775808 to 9223372036854775807. 
This is used when int is not large enough to store the value. Note that you should end the value with an "L":

public class Main {
  public static void main(String[] args) {
    long myNum = 15000000000L;
    System.out.println(myNum);  
  }
}

""",


"""
# floating data types program

You should use a floating point type whenever you need a number with a decimal, such as 9.99 or 3.14515.

The float and double data types can store fractional numbers. Note that you should end the value with an "f" for floats and "d" for doubles:


public class Main {
  public static void main(String[] args) {
    float myNum = 5.75f;
    System.out.println(myNum);  
  }
}

""",

"""
# double data type

public class Main {
  public static void main(String[] args) {
    double myNum = 19.99d;
    System.out.println(myNum);  
  }
}

""",

"""
# scientific numbers

public class Main {
  public static void main(String[] args) {
    double myNum = 19.99d;
    System.out.println(myNum);  
  }
}

""",


"""
# Boolean data type
Boolean Types

Very often in programming, you will need a data type that can only have one of two values, like:

    YES / NO
    ON / OFF
    TRUE / FALSE

For this, Java has a boolean data type, which can only take the values true or false:


Example of Boolean Type

public class IfElseTernaryExample {    
public static void main(String[] args) {    
    boolean isAdmin = true;    
    System.out.println(isAdmin);  
}    
}  
""",


"""
# display output in the java

In Java, you can display output using the `System.out.println()` method. Here's an example:

```java
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");  # This will print the text to the console
    }
}

- `System.out.println()` prints the message followed by a new line.
- You can use `System.out.print()` if you don't want a new line after the message.

For example:
```java
System.out.print("Hello");
System.out.print(" World!");
```
This will print "Hello World!" on the same line.

Let me know if you need further clarification!

""",

  """"
    # Defining a Class in Java
    
    class Car {
        String brand;
        int speed;
        
        void display() {
            System.out.println("Brand: " + brand);
            System.out.println("Speed: " + speed);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car();
            myCar.brand = "Toyota";
            myCar.speed = 120;
            myCar.display();
        }
    }
    """,
    
    """
    # Creating an Object in Java
    class Car {
        String brand = "Toyota";
        int speed = 120;
        
        void display() {
            System.out.println("Brand: " + brand);
            System.out.println("Speed: " + speed);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car();  # Object creation
            myCar.display();
        }
    }
    """,
    
    """
    # Creating Multiple Objects of the Same Class
    class Car {
        String brand;
        int speed;
        
        void display() {
            System.out.println("Brand: " + brand + ", Speed: " + speed);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car car1 = new Car();
            car1.brand = "Honda";
            car1.speed = 140;
            
            Car car2 = new Car();
            car2.brand = "BMW";
            car2.speed = 180;
            
            car1.display();
            car2.display();
        }
    }
    """,
    
    """"
    # Initializing Object Properties Using Constructor
    class Car {
        String brand;
        int speed;
        
        # Constructor
        Car(String b, int s) {  
            brand = b;
            speed = s;
        }
        
        void display() {
            System.out.println("Brand: " + brand + ", Speed: " + speed);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car("Honda", 150);
            myCar.display();
        }
    }
    """,
    
    """
    # Instance Variables vs. Local Variables
    class Example {
        int instanceVar = 10;  # Instance variable
        
        void method() {
            int localVar = 5;  # Local variable
            System.out.println("Instance Variable: " + instanceVar);
            System.out.println("Local Variable: " + localVar);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Example obj = new Example();
            obj.method();
        }
    }
    """,
    
    """ 
    # Using 'this' Keyword
    class Car {
        String brand;
        
        # Constructor using 'this' keyword
        Car(String brand) {
            this.brand = brand;
        }
        
        void display() {
            System.out.println("Brand: " + brand);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car("Tesla");
            myCar.display();
        }
    }
    """,
    
    """ 
    # Method Overloading
    class MathOperations {
        int add(int a, int b) {
            return a + b;
        }
        int add(int a, int b, int c) {
            return a + b + c;
        }
    }
    public class Main {
        public static void main(String[] args) {
            MathOperations obj = new MathOperations();
            System.out.println("Sum (2 numbers): " + obj.add(5, 10));
            System.out.println("Sum (3 numbers): " + obj.add(5, 10, 15));
        }
    }
    """,
    
    """ 
    # Accessing Class Attributes and Methods
    class Car {
        String brand = "Ford";
        
        void display() {
            System.out.println("Brand: " + brand);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car();
            myCar.display();
        }
    }
    """,
    
    """ 
    # Defining and Calling Instance Methods
    class Car {
        void start() {
            System.out.println("Car is starting...");
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car();
            myCar.start();
        }
    }
    """,
    
    """" 
    # Role of 'new' Keyword
    class Car {
        String brand;
        
        Car() {
            brand = "Tesla";
        }
        
        void display() {
            System.out.println("Brand: " + brand);
        }
    }
    public class Main {
        public static void main(String[] args) {
            Car myCar = new Car(); # 'new' keyword creates an object in memory
            myCar.display();
        }
    }
    """,
    
    """
    # If else statement
    
    In the realm of programming, decision-making plays a pivotal role in determining the flow of execution. Whether it's directing traffic in a complex intersection or navigating through various scenarios in a program, making decisions is essential.
    In Java, one of the fundamental constructs for decision-making is the 'if-else' statement. Let's delve into what 'if-else' statements are, how they work, and how they can be effectively utilized in Java programming.

The Java if statement is used to test the condition. It checks boolean condition: true or false. There are various types of if statement in Java.

    if statement
    if-else statement
    if-else-if ladder
    nested if statement
    """,
    
    """
    # How if else work 
    
    When the 'if-else' statement is encountered, the condition within the parentheses is evaluated. 
    If the condition evaluates to true, the block of code inside the 'if' block is executed.
    However, if the condition evaluates to false, the block of code inside the 'else' block is executed. 
    It allows the program to take different paths based on the outcome of the condition.
    
    Syntax:
    
    if (condition) {
    // Code executes if condition is true
} else {
    // Code executes if condition is false
}


Example:

int num = 10;
if (num > 0) {
    System.out.println("Positive number");
} else {
    System.out.println("Negative number or zero");
}

""",


"""
# Leap Year

public class LeapYearExample {    
public static void main(String[] args) {    
    int year=2020;    
    if(((year % 4 ==0) && (year % 100 !=0)) || (year % 400==0)){  
        System.out.println("LEAP YEAR");  
    }  
    else{  
        System.out.println("COMMON YEAR");  
    }  
}    
}
""",


"""
# If else ladder statement

The if-else-if ladder statement executes one condition from multiple statements.

Syntax:

    if(condition1){  
    //code to be executed if condition1 is true  
    }else if(condition2){  
    //code to be executed if condition2 is true  
    }  
    else if(condition3){  
    //code to be executed if condition3 is true  
    }  
    ...  
    else{  
    //code to be executed if all the conditions are false  
    }  
""",


"""
# Marks and grades

public class IfElseIfExample {  
public static void main(String[] args) {  
    int marks=65;  
      
    if(marks<50){  
        System.out.println("fail");  
    }  
    else if(marks>=50 && marks<60){  
        System.out.println("D grade");  
    }  
    else if(marks>=60 && marks<70){  
        System.out.println("C grade");  
    }  
    else if(marks>=70 && marks<80){  
        System.out.println("B grade");  
    }else{  
        System.out.println("Invalid!");  
    }  
}  
}  
""",


"""
# Positive and negative

    public class PositiveNegativeExample {    
    public static void main(String[] args) {    
        int number=-13;    
        if(number>0){  
        System.out.println("POSITIVE");  
        }else if(number<0){  
        System.out.println("NEGATIVE");  
        }else{  
        System.out.println("ZERO");  
       }  
    }    
    }    
""",


"""
# Ternary Operator

We can also use ternary operator (? :)
to perform the task of if...else statement.
It is a shorthand way to check the condition.
If the condition is true, the result of ? is returned. But, if the condition is false, the result of : is returned.


Example of Ternary Operator

public class IfElseTernaryExample {    
public static void main(String[] args) {    
    int number=13;    
    //Using ternary operator  
    String output=(number%2==0)?"even number":"odd number";    
    System.out.println(output);  
}    
}  
""",


"""
# Switch Statement

The switch statement in Java is a multi-way branch statement. In simple words, the Java switch statement executes one statement from multiple conditions.

It is an alternative to an if-else-if ladder statement. 
It provides an easy way to dispatch execution to different parts of code based on the value of the expression. 
The expression can be of type byte, short, char, int, long, enums, String, or wrapper classes (Integer, Short, Byte, Long).



Syntax of switch statement

switch(expression) {
  case x:
    // code block
    break;
  case y:
    // code block
    break;
  default:
    // code block
}

""",


"""
# Weeks names

public class Main {
  public static void main(String[] args) {
    int day = 4;
    switch (day) {
      case 1:
        System.out.println("Monday");
        break;
      case 2:
        System.out.println("Tuesday");
        break;
      case 3:
        System.out.println("Wednesday");
        break;
      case 4:
        System.out.println("Thursday");
        break;
      case 5:
        System.out.println("Friday");
        break;
      case 6:
        System.out.println("Saturday");
        break;
      case 7:
        System.out.println("Sunday");
        break;
    }
  }
}

""",


"""
# Break keyword 

When Java reaches a break keyword, it breaks out of the switch block.

This will stop the execution of more code and case testing inside the block.

When a match is found, and the job is done, it's time for a break. There is no need for more testing.


Example

public class BreakExample {
    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            if (i == 3) {
                System.out.println("Breaking the loop at i = " + i);
                break;  # Exits the loop when i = 3
            }
            System.out.println("i = " + i);
        }
    }
}

""",


"""
# Default keyword 



The default keyword specifies some code to run if there is no case match:

Example:

public class Main {
  public static void main(String[] args) {
    int day = 4;
    switch (day) {
      case 6:
        System.out.println("Today is Saturday");
        break;
      case 7:
        System.out.println("Today is Sunday");
        break;
      default:
        System.out.println("Looking forward to the Weekend");
    }    
  }
}

""",


"""
# Loops define
Loops can execute a block of code as long as a specified condition is reached.

Loops are handy because they save time, reduce errors, and they make code more readable.
""",


"""
# Types of loops 

In Java, there are four primary types of loops used for iterative operations. Each serves a specific purpose and is suited for different scenarios:

### 1. **`for` Loop**  
- **Purpose**: Used when the number of iterations is known in advance.  
- **Syntax**:  
  ```java
  for (initialization; condition; update) {
      // Code to execute
  }
  ```  
- **Example**:  
  ```java
  for (int i = 0; i < 5; i++) {
      System.out.println(i); // Prints 0 to 4
  }
  ```

---

### 2. **`while` Loop**  
- **Purpose**: Repeats code **while a condition is true**. The condition is checked **before** entering the loop.  
- **Syntax**:  
  ```java
  while (condition) {
      // Code to execute
  }
  ```  
- **Example**:  
  ```java
  int i = 0;
  while (i < 5) {
      System.out.println(i); // Prints 0 to 4
      i++;
  }
  ```

---

### 3. **`do-while` Loop**  
- **Purpose**: Similar to `while`, but the loop body executes **at least once** because the condition is checked **after** the loop.  
- **Syntax**:  
  ```java
  do {
      // Code to execute
  } while (condition);
  ```  
- **Example**:  
  ```java
  int i = 0;
  do {
      System.out.println(i); // Prints 0 to 4
      i++;
  } while (i < 5);
  ```

---

### 4. **Enhanced `for` Loop (for-each Loop)**  
- **Purpose**: Simplifies iteration over **arrays** and **collections** (e.g., `List`, `Set`).  
- **Syntax**:  
  ```java
  for (DataType element : collection) {
      // Code to execute
  }
  ```  
- **Example**:  
  ```java
  String[] fruits = {"Apple", "Banana", "Mango"};
  for (String fruit : fruits) {
      System.out.println(fruit); // Prints all elements
  }
  ```

---

### Key Differences:
| Loop Type         | When to Use                                                                 | Condition Checked       |
|-------------------|-----------------------------------------------------------------------------|-------------------------|
| `for`             | Known number of iterations (e.g., iterating a fixed number of times).       | Before loop execution.  |
| `while`           | Unknown iterations, but need to check condition before execution.          | Before loop execution.  |
| `do-while`        | Unknown iterations, but loop must run **at least once**.                    | After loop execution.   |
| Enhanced `for`    | Iterating over arrays/collections **without needing index manipulation**.   | Implicit (auto-handled).|

---

### Infinite Loops (Special Cases):
- **`while(true)`**:  
  ```java
  while (true) {
      // Runs forever unless broken with 'break'
  }
  ```
- **`for(;;)`**:  
  ```java
  for (;;) {
      // Runs forever unless broken with 'break'
  }
  ```

---

### Nested Loops:
Loops can be nested within each other (e.g., a `for` loop inside another `for` loop) to handle complex iterations, like traversing 2D arrays.

**Example**:  
```java
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        System.out.println(i + ", " + j);
    }
}
```

""",


"""
# do while loop
A `do-while` loop in Java is a control flow statement that executes a block of code at least once, and then repeatedly executes the block or not, depending on a given boolean condition at the end of the block.

Here’s the syntax for a `do-while` loop in Java:

```java
do {
    // block of code
} while (condition);
```

And here’s a quick example to illustrate how it works:

```java
public class Main {
    public static void main(String[] args) {
        int i = 1;

        do {
            System.out.println("The value of i is: " + i);
            i++;
        } while (i <= 5);
    }
}
```

In this example, the code inside the `do` block will execute, and then the condition (`i <= 5`) is checked. If the condition is true, the loop continues; otherwise, it stops.

This means the code inside the `do` block runs at least once regardless of whether the condition is initially true or not. If you have any specific use cases or further questions, feel free to ask!
""",


"""
# While Loop Simple Program 

Certainly! Here are separate examples for both the `while` loop and the `do-while` loop:

### `while` Loop Example

A `while` loop checks the condition before executing the block of code. If the condition is `true`, the code inside the loop is executed. This repeats until the condition becomes `false`.

```java
public class Main {
    public static void main(String[] args) {
        int i = 1;

        while (i <= 5) {
            System.out.println("The value of i is: " + i);
            i++;
        }
    }
}
```

In this example, the loop will print the value of `i` from 1 to 5. The condition `i <= 5` is checked before each iteration, ensuring the code inside the loop runs only when `i` is less than or equal to 5.

""",


"""
# Do while loop example


### `do-while` Loop Example

A `do-while` loop executes the block of code once before checking the condition. It will continue to execute the block as long as the condition is `true`.

```java
public class Main {
    public static void main(String[] args) {
        int i = 1;

        do {
            System.out.println("The value of i is: " + i);
            i++;
        } while (i <= 5);
    }
}
```


""",


"""
# For loop

A `for` loop in Java is a control flow statement that repeatedly executes a block of code a certain number of times, based on a condition. It's a compact way to iterate over a range of values.

Here’s the syntax for a `for` loop in Java:

```java
for (initialization; condition; update) {
    // block of code
}
```

- **initialization**: This part is executed once, at the start of the loop. It’s used to initialize loop variables.
- **condition**: This part is evaluated before each iteration of the loop. If it evaluates to `true`, the loop continues; if it evaluates to `false`, the loop stops.
- **update**: This part is executed at the end of each iteration. It’s typically used to update the loop variables.

Here’s a quick example to illustrate how a `for` loop works:

```java
public class Main {
    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            System.out.println("The value of i is: " + i);
        }
    }
}
```

In this example:
- **initialization**: `int i = 1;` (sets `i` to 1)
- **condition**: `i <= 5` (loop continues as long as `i` is less than or equal to 5)
- **update**: `i++` (increments `i` by 1 after each iteration)

The loop will print the value of `i` from 1 to 5. 

If you have any specific questions or need more examples, feel free to ask!
""",


"""
# Break statement 

In Java, the `break` statement is used to terminate the execution of a loop or a `switch` statement prematurely. When the `break` statement is encountered, the control of the program immediately exits the loop or `switch` block, and continues with the next statement following the loop or `switch`.

### Usage in Loops
When used inside a loop (`for`, `while`, or `do-while`), the `break` statement causes the loop to terminate immediately, and the program continues with the statement following the loop.

```java
for (int i = 0; i < 10; i++) {
    if (i == 5) {
        break; // Exit the loop when i is 5
    }
    System.out.println(i);
}
// Output: 0 1 2 3 4
```

In this example, the loop terminates when `i` equals 5, so the numbers 0 through 4 are printed.

### Usage in `switch` Statements
In a `switch` statement, the `break` statement is used to exit the `switch` block after a case is matched. Without `break`, the program would continue executing the following cases (this is called "fall-through").

```java
int day = 3;
switch (day) {
    case 1:
        System.out.println("Monday");
        break;
    case 2:
        System.out.println("Tuesday");
        break;
    case 3:
        System.out.println("Wednesday");
        break; // Exit the switch after this case
    default:
        System.out.println("Invalid day");
}
// Output: Wednesday
```

Here, the `break` statement ensures that only the matched case (`case 3`) is executed, and the `switch` block is exited afterward.

### Labeled `break`
Java also supports labeled `break` statements, which allow you to break out of nested loops. A label is an identifier followed by a colon (`:`), placed before a loop. When the `break` statement is used with a label, it terminates the labeled loop.

```java
outerLoop:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) {
            break outerLoop; // Exit the outer loop
        }
        System.out.println(i + " " + j);
    }
}
// Output:
// 0 0
// 0 1
// 0 2
// 1 0
```

In this example, the `break outerLoop;` statement exits the outer loop when `i` is 1 and `j` is 1.

### Key Points
- `break` is used to exit loops or `switch` statements.
- Without `break` in a `switch`, execution will "fall through" to the next case.
- Labeled `break` can be used to exit nested loops.

Using `break` effectively can help control the flow of your program and avoid unnecessary iterations or case executions.
""",


"""
# Continue Statement

In Java, the `continue` statement is used to skip the current iteration of a loop (`for`, `while`, or `do-while`) and proceed to the next iteration. When the `continue` statement is encountered, the remaining code in the loop body for the current iteration is skipped, and the loop's condition is re-evaluated for the next iteration.

### Key Points About `continue`
- It only applies to loops (`for`, `while`, `do-while`).
- It skips the rest of the loop body for the current iteration and moves to the next iteration.
- In a `for` loop, the update statement (e.g., `i++`) is still executed before the next iteration.

---

### Example: Using `continue` in a `for` Loop
```java
for (int i = 0; i < 5; i++) {
    if (i == 2) {
        continue; // Skip the rest of the loop body when i is 2
    }
    System.out.println(i);
}
// Output: 0 1 3 4
```

In this example:
- When `i` equals 2, the `continue` statement is executed.
- The `System.out.println(i)` statement is skipped for that iteration.
- The loop continues with the next iteration (`i = 3`).

---

### Example: Using `continue` in a `while` Loop
```java
int i = 0;
while (i < 5) {
    i++;
    if (i == 3) {
        continue; // Skip the rest of the loop body when i is 3
    }
    System.out.println(i);
}
// Output: 1 2 4 5
```

Here:
- When `i` equals 3, the `continue` statement skips the `System.out.println(i)` statement.
- The loop continues with the next iteration.

---

### Labeled `continue`
Java also supports labeled `continue` statements, which allow you to skip the current iteration of a specific (outer) loop in nested loops. A label is an identifier followed by a colon (`:`), placed before a loop.

#### Example: Labeled `continue`
```java
outerLoop:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) {
            continue outerLoop; // Skip to the next iteration of the outer loop
        }
        System.out.println(i + " " + j);
    }
}
// Output:
// 0 0
// 0 1
// 0 2
// 1 0
// 2 0
// 2 1
// 2 2
```

In this example:
- When `i` is 1 and `j` is 1, the `continue outerLoop;` statement skips the rest of the inner loop and moves to the next iteration of the outer loop (`i = 2`).

---

### When to Use `continue`
- Use `continue` when you want to skip specific iterations of a loop based on a condition.
- It is particularly useful when you want to avoid executing certain parts of the loop body for specific cases.

---

### Difference Between `break` and `continue`
| Feature          | `break`                              | `continue`                          |
|------------------|--------------------------------------|-------------------------------------|
| **Effect**        | Exits the loop or `switch` entirely. | Skips the current iteration and moves to the next one. |
| **Usage**         | Used in loops and `switch` statements. | Used only in loops.                |
| **Labeled Form**  | Can be used with labels to exit nested loops. | Can be used with labels to skip iterations in nested loops. |

---

### Summary
- The `continue` statement is used to skip the current iteration of a loop and proceed to the next iteration.
- It is useful for avoiding unnecessary computations or operations in specific cases.
- Labeled `continue` allows you to control nested loops more precisely.
""",


"""
# While loop

In Java, a `while` loop is a control flow statement that allows you to repeatedly execute a block of code as long as a specified condition is `true`. The loop continues to execute until the condition becomes `false`.

### Syntax:
```java
while (condition) {
    // Code to be executed
}
```

- **condition**: This is a boolean expression. If the condition evaluates to `true`, the code inside the loop is executed. If it evaluates to `false`, the loop terminates, and control passes to the next statement after the loop.

### Example:
```java
int count = 0;

while (count < 5) {
    System.out.println("Count is: " + count);
    count++;  // Increment the count by 1
}
```

### Explanation:
- The loop starts with `count` equal to `0`.
- The condition `count < 5` is checked before each iteration.
- As long as `count` is less than `5`, the loop body is executed.
- Inside the loop, the value of `count` is printed, and then `count` is incremented by `1`.
- When `count` reaches `5`, the condition `count < 5` becomes `false`, and the loop terminates.

### Output:
```
Count is: 0
Count is: 1
Count is: 2
Count is: 3
Count is: 4
```

### Key Points:
- The `while` loop is useful when you don't know in advance how many times the loop needs to execute.
- Be cautious of infinite loops, where the condition never becomes `false`. For example:
  ```java
  while (true) {
      // This will run forever unless you break out of it
  }
  ```
- You can use `break` to exit the loop prematurely or `continue` to skip the rest of the current iteration and proceed to the next iteration.

### Example with `break`:
```java
int count = 0;

while (true) {
    if (count >= 5) {
        break;  // Exit the loop when count is 5 or more
    }
    System.out.println("Count is: " + count);
    count++;
}
```

This will produce the same output as the previous example but uses a `break` statement to exit the loop.
""",


"""
# Methods in java

In Java, a **method** is a block of code that performs a specific task and can be called or invoked to execute that task.
Methods are used to organize code into reusable units, making programs more modular, readable, and maintainable.

### Syntax of a Method:
```java
access_modifier return_type method_name(parameter_list) {
    // Method body (code to be executed)
    return value; // Optional, depending on the return type
}
```

### Components of a Method:
1. **Access Modifier**:
   - Defines the visibility of the method (e.g., `public`, `private`, `protected`, or default).
   - Example: `public` means the method can be accessed from anywhere.

2. **Return Type**:
   - Specifies the type of value the method returns.
   - Use `void` if the method does not return any value.
   - Example: `int`, `String`, `double`, etc.

3. **Method Name**:
   - The name of the method, which should follow Java naming conventions (e.g., camelCase).
   - Example: `calculateSum`, `printMessage`.

4. **Parameter List**:
   - A list of input parameters (arguments) the method accepts, enclosed in parentheses `()`.
   - Parameters are optional; a method can have zero or more parameters.
   - Example: `(int a, int b)`.

5. **Method Body**:
   - The block of code that defines what the method does.
   - Enclosed in curly braces `{}`.

6. **Return Statement**:
   - Used to return a value from the method (if the return type is not `void`).
   - Example: `return a + b;`.

---

### Example of a Method:
```java
public int addNumbers(int a, int b) {
    int sum = a + b;
    return sum; // Returns the sum of a and b
}
```

- **Access Modifier**: `public`
- **Return Type**: `int`
- **Method Name**: `addNumbers`
- **Parameters**: `int a, int b`
- **Method Body**: Calculates the sum of `a` and `b` and returns it.

---

### Types of Methods in Java:
1. **Predefined Methods**:
   - Methods that are already defined in Java libraries.
   - Example: `System.out.println()`, `Math.sqrt()`, `String.length()`.

2. **User-Defined Methods**:
   - Methods created by the programmer to perform specific tasks.
   - Example: The `addNumbers` method above.

---

### Example of a Complete Program with Methods:
```java
public class Main {
    // User-defined method to add two numbers
    public static int addNumbers(int a, int b) {
        return a + b;
    }

    // User-defined method to print a message
    public static void printMessage(String message) {
        System.out.println(message);
    }

    // Main method (entry point of the program)
    public static void main(String[] args) {
        int result = addNumbers(5, 10); // Calling the addNumbers method
        printMessage("The sum is: " + result); // Calling the printMessage method
    }
}
```

### Output:
```
The sum is: 15
```

---

### Key Points:
1. **Static vs. Non-Static Methods**:
   - **Static Methods**: Belong to the class and can be called without creating an object of the class.
     - Example: `public static void main(String[] args)`.
   - **Non-Static Methods**: Belong to an instance of the class and require an object to be called.
     - Example: `public void display()`.

2. **Method Overloading**:
   - Defining multiple methods with the same name but different parameter lists.
   - Example:
     ```java
     public int add(int a, int b) { return a + b; }
     public int add(int a, int b, int c) { return a + b + c; }
     ```

3. **Method Overriding**:
   - Redefining a method in a subclass that is already defined in its superclass.
   - Used in inheritance.

4. **Void Methods**:
   - Methods that do not return any value.
   - Example:
     ```java
     public void greet() {
         System.out.println("Hello!");
     }
     ```

5. **Recursive Methods**:
   - Methods that call themselves to solve a problem.
   - Example:
     ```java
     public int factorial(int n) {
         if (n == 0) return 1;
         else return n * factorial(n - 1);
     }
     ```

---

### Summary:
Methods in Java are fundamental building blocks that allow you to encapsulate logic, reuse code, and structure programs effectively.
They can take inputs, perform operations, and return results, making them essential for writing clean and efficient code.
""",



"""
# Parameters in java

In Java, the term "parameters" typically refers to the variables that are passed to a method when it is called. These parameters allow you to pass data into a method, which can then be used within the method's body. Parameters are specified in the method declaration, and the values passed to the method when it is called are known as arguments.

### Method Parameters in Java

Here’s a basic example of a method with parameters:

```java
public class Example {
    // Method with two parameters
    public void printSum(int a, int b) {
        int sum = a + b;
        System.out.println("Sum: " + sum);
    }

    public static void main(String[] args) {
        Example example = new Example();
        // Calling the method with arguments 5 and 10
        example.printSum(5, 10);  // Output: Sum: 15
    }
}
```

### Key Points about Method Parameters:

1. **Parameter List**: The parameter list is defined in the method declaration, inside the parentheses `()`. Each parameter consists of a type followed by a name, and multiple parameters are separated by commas.

2. **Arguments**: When you call a method, you pass values (arguments) that match the types of the parameters defined in the method declaration.

3. **Pass-by-Value**: In Java, all parameters are passed by value. This means that the method receives a copy of the value of the argument, not the actual variable itself. For primitive types, this means changes to the parameter inside the method do not affect the original argument. For object references, the reference itself is passed by value, so changes to the object's state inside the method will affect the original object.

4. **Varargs (Variable-Length Arguments)**: Java allows you to pass a variable number of arguments to a method using varargs. This is done by using an ellipsis (`...`) after the type in the parameter list.

   ```java
   public void printNumbers(int... numbers) {
       for (int number : numbers) {
           System.out.println(number);
       }
   }

   public static void main(String[] args) {
       Example example = new Example();
       example.printNumbers(1, 2, 3, 4);  // Output: 1 2 3 4
   }
   ```

5. **Method Overloading**: Java supports method overloading, which allows you to define multiple methods with the same name but different parameter lists.

   ```java
   public class Example {
       public void print(int a) {
           System.out.println("Integer: " + a);
       }

       public void print(double a) {
           System.out.println("Double: " + a);
       }

       public static void main(String[] args) {
           Example example = new Example();
           example.print(5);      // Output: Integer: 5
           example.print(5.5);    // Output: Double: 5.5
       }
   }
   ```

### Summary

- **Parameters** are the variables defined in a method's declaration.
- **Arguments** are the actual values passed to the method when it is called.
- Java uses **pass-by-value** for all parameters.
- **Varargs** allow you to pass a variable number of arguments to a method.
- **Method overloading** allows multiple methods with the same name but different parameter lists.

Understanding how parameters work in Java is fundamental to writing flexible and reusable methods.
""",


"""
# Arguments in java

In Java, **arguments** are the actual values that you pass to a method when you call it. These values correspond to the parameters defined in the method's declaration. Arguments are sometimes referred to as **actual parameters**, while the variables in the method declaration are called **formal parameters**.

### Key Concepts:

1. **Arguments vs Parameters**:
   - **Parameters**: These are the variables defined in the method signature. They act as placeholders for the values that will be passed to the method.
   - **Arguments**: These are the actual values passed to the method when it is invoked.

   Example:
   ```java
   public void printSum(int a, int b) { // 'a' and 'b' are parameters
       System.out.println(a + b);
   }

   public static void main(String[] args) {
       Example example = new Example();
       example.printSum(5, 10); // '5' and '10' are arguments
   }
   ```

   In this example:
   - `int a` and `int b` are **parameters**.
   - `5` and `10` are **arguments**.

2. **Passing Arguments**:
   - When you call a method, you pass arguments that match the types and order of the parameters defined in the method.
   - Java supports passing arguments of primitive types (e.g., `int`, `double`, `boolean`) and reference types (e.g., objects, arrays).

3. **Pass-by-Value**:
   - In Java, all arguments are passed **by value**. This means:
     - For **primitive types**, the method receives a copy of the value. Changes to the parameter inside the method do not affect the original argument.
     - For **reference types**, the method receives a copy of the reference to the object. This means changes to the object's state inside the method will affect the original object, but reassigning the reference does not affect the original reference.

   Example:
   ```java
   public void modifyValues(int x, int[] arr) {
       x = 20; // This change does not affect the original argument
       arr[0] = 100; // This change affects the original array
   }

   public static void main(String[] args) {
       Example example = new Example();
       int num = 10;
       int[] numbers = {1, 2, 3};

       example.modifyValues(num, numbers);

       System.out.println(num); // Output: 10 (unchanged)
       System.out.println(numbers[0]); // Output: 100 (changed)
   }
   ```

4. **Variable-Length Arguments (Varargs)**:
   - Java allows you to pass a variable number of arguments to a method using **varargs**. This is denoted by an ellipsis (`...`) after the type in the parameter list.
   - Varargs must be the last parameter in the method signature.

   Example:
   ```java
   public void printNumbers(int... numbers) {
       for (int num : numbers) {
           System.out.println(num);
       }
   }

   public static void main(String[] args) {
       Example example = new Example();
       example.printNumbers(1, 2, 3); // Output: 1 2 3
       example.printNumbers(10, 20);  // Output: 10 20
   }
   ```

5. **Method Overloading and Arguments**:
   - Java supports **method overloading**, where multiple methods can have the same name but different parameter lists. The arguments you pass determine which method is called.

   Example:
   ```java
   public class Example {
       public void print(int a) {
           System.out.println("Integer: " + a);
       }

       public void print(String a) {
           System.out.println("String: " + a);
       }

       public static void main(String[] args) {
           Example example = new Example();
           example.print(5);      // Calls print(int a)
           example.print("Hello"); // Calls print(String a)
       }
   }
   ```

### Summary:
- **Arguments** are the actual values passed to a method when it is called.
- They correspond to the **parameters** defined in the method's signature.
- Java uses **pass-by-value** for all arguments.
- **Varargs** allow you to pass a variable number of arguments to a method.
- **Method overloading** allows you to define methods with the same name but different parameter lists, and the arguments determine which method is called.

Understanding arguments is essential for working with methods in Java and passing data effectively.
""",



"""
# Return values

In Java, a **return value** is the value that a method sends back to the caller when it finishes executing. 
Methods can optionally return a value to the code that called them, and this value is specified using the `return` statement. 
The type of the return value is declared in the method's signature.

### Key Concepts:

1. **Return Type**:
   - The return type of a method is specified in the method declaration. It indicates the type of value the method will return.
   - If a method does not return any value, the return type is declared as `void`.

   Example:
   ```java
   public int add(int a, int b) {
       return a + b; // Returns an integer value
   }

   public void printMessage() {
       System.out.println("Hello, World!"); // No return value (void)
   }
   ```

2. **The `return` Statement**:
   - The `return` statement is used to exit a method and optionally return a value to the caller.
   - For methods with a return type other than `void`, the `return` statement must return a value of the specified type.
   - For `void` methods, the `return` statement can be used to exit the method early, but it does not return any value.

   Example:
   ```java
   public int getMax(int a, int b) {
       if (a > b) {
           return a; // Returns 'a' if it is greater
       } else {
           return b; // Returns 'b' otherwise
       }
   }

   public void checkNumber(int num) {
       if (num < 0) {
           System.out.println("Negative number");
           return; // Exits the method early
       }
       System.out.println("Positive number");
   }
   ```

3. **Returning Primitive Types**:
   - Methods can return primitive data types such as `int`, `double`, `boolean`, etc.

   Example:
   ```java
   public double calculateArea(double radius) {
       return Math.PI * radius * radius; // Returns a double value
   }
   ```

4. **Returning Objects**:
   - Methods can also return objects (instances of classes).

   Example:
   ```java
   public String createGreeting(String name) {
       return "Hello, " + name + "!"; // Returns a String object
   }
   ```

5. **Returning Arrays**:
   - Methods can return arrays of any type.

   Example:
   ```java
   public int[] createArray(int size) {
       int[] array = new int[size];
       for (int i = 0; i < size; i++) {
           array[i] = i + 1;
       }
       return array; // Returns an array of integers
   }
   ```

6. **Returning `null`**:
   - For methods that return reference types (e.g., objects, arrays), you can return `null` to indicate the absence of a value.

   Example:
   ```java
   public String findNameById(int id) {
       if (id == 1) {
           return "Alice";
       } else if (id == 2) {
           return "Bob";
       } else {
           return null; // No name found for the given ID
       }
   }
   ```

7. **Chaining Method Calls**:
   - Since methods can return values, you can chain method calls together, where the return value of one method is used as an argument for another.

   Example:
   ```java
   public int add(int a, int b) {
       return a + b;
   }

   public int multiply(int a, int b) {
       return a * b;
   }

   public static void main(String[] args) {
       Example example = new Example();
       int result = example.multiply(example.add(2, 3), 4); // (2 + 3) * 4 = 20
       System.out.println(result); // Output: 20
   }
   ```

### Summary:
- A **return value** is the value that a method sends back to the caller.
- The return type is specified in the method declaration (e.g., `int`, `String`, `void`).
- The `return` statement is used to return a value and exit the method.
- Methods can return primitive types, objects, arrays, or `null`.
- Return values allow methods to produce results that can be used in further computations or logic.

Understanding return values is crucial for writing methods that perform meaningful tasks and communicate their results to the rest of the program.
""",



"""
# Method Overloading

Method overloading in Java is a feature that allows a class to have more than one method with the same name, as long as their parameter lists (i.e., the number, type, or order of parameters) are different. 
This enables methods to perform similar but slightly different tasks depending on the input parameters.

### Key Points:
1. **Same Method Name**: The methods must have the same name.
2. **Different Parameter Lists**: The methods must have different parameter lists in terms of:
   - **Number of parameters**
   - **Types of parameters**
   - **Order of parameters**
3. **Return Type**: The return type of the methods can be the same or different, but it does not contribute to method overloading. 
Overloading is determined solely by the method signature (name and parameter list).

4. **Compile-Time Polymorphism**: Method overloading is resolved at compile time, based on the method signature.

### Example:
```java
public class Calculator {

    // Method to add two integers
    public int add(int a, int b) {
        return a + b;
    }

    // Overloaded method to add three integers
    public int add(int a, int b, int c) {
        return a + b + c;
    }

    // Overloaded method to add two double values
    public double add(double a, double b) {
        return a + b;
    }

    // Overloaded method with different parameter order
    public String add(String str, int num) {
        return str + num;
    }

    public static void main(String[] args) {
        Calculator calc = new Calculator();

        System.out.println(calc.add(5, 10));           // Calls the first add method
        System.out.println(calc.add(5, 10, 15));       // Calls the second add method
        System.out.println(calc.add(5.5, 10.5));       // Calls the third add method
        System.out.println(calc.add("Result: ", 100)); // Calls the fourth add method
    }
}
```

### Output:
```
15
30
16.0
Result: 100
```

### Explanation:
- The `add` method is overloaded with different parameter lists:
  1. `add(int a, int b)` takes two integers.
  2. `add(int a, int b, int c)` takes three integers.
  3. `add(double a, double b)` takes two doubles.
  4. `add(String str, int num)` takes a `String` and an `int`.

- The correct method is chosen at compile time based on the arguments passed.

### Why Use Method Overloading?
- Improves code readability by using the same method name for similar operations.
- Provides flexibility to handle different types of inputs.
- Reduces the need for multiple method names for similar tasks.

### Note:
- Method overloading is different from **method overriding**, which occurs in inheritance and involves redefining a method in a subclass with the same signature as in the superclass.
""",


"""
# Method Overloading program

public class MethodOverloadingExample {

    // Method to add two integers
    public int add(int a, int b) {
        return a + b;
    }

    // Overloaded method to add three integers
    public int add(int a, int b, int c) {
        return a + b + c;
    }

    // Overloaded method to add two double values
    public double add(double a, double b) {
        return a + b;
    }

    // Overloaded method to concatenate two strings
    public String add(String a, String b) {
        return a + b;
    }

    public static void main(String[] args) {
        MethodOverloadingExample example = new MethodOverloadingExample();

        // Calling the add method with two integers
        System.out.println("Sum of 5 and 10: " + example.add(5, 10));

        // Calling the add method with three integers
        System.out.println("Sum of 5, 10, and 15: " + example.add(5, 10, 15));

        // Calling the add method with two double values
        System.out.println("Sum of 3.5 and 2.7: " + example.add(3.5, 2.7));

        // Calling the add method with two strings
        System.out.println("Concatenation of 'Hello' and 'World': " + example.add("Hello", "World"));
    }
}
""",


"""
# Recursion in java

Recursion in Java is a programming technique where a method calls itself in order to solve a problem. This approach is particularly useful for problems that can be broken down into smaller, similar subproblems. A recursive method typically has two main components:

1. **Base Case**: This is the condition under which the recursion stops. Without a base case, the method would call itself indefinitely, leading to a stack overflow error.

2. **Recursive Case**: This is where the method calls itself with a modified argument, moving closer to the base case with each call.

Here’s a simple example of recursion in Java: calculating the factorial of a number.

```java
public class Factorial {
    // Recursive method to calculate factorial
    public static int factorial(int n) {
        // Base case: factorial of 0 or 1 is 1
        if (n == 0 || n == 1) {
            return 1;
        }
        // Recursive case: n * factorial of (n-1)
        else {
            return n * factorial(n - 1);
        }
    }

    public static void main(String[] args) {
        int number = 5;
        int result = factorial(number);
        System.out.println("Factorial of " + number + " is " + result);
    }
}
```

### Explanation:
- **Base Case**: When `n` is 0 or 1, the method returns 1. This stops the recursion.
- **Recursive Case**: For any other value of `n`, the method calls itself with `n-1` and multiplies the result by `n`.

### Output:
```
Factorial of 5 is 120
```

### Key Points:
- **Stack Usage**: Each recursive call adds a new layer to the call stack. If the recursion is too deep, it can lead to a `StackOverflowError`.
- **Efficiency**: Recursion can be less efficient than iterative solutions due to the overhead of multiple method calls. However, it can make the code more readable and easier to understand for certain problems.
- **Tail Recursion**: Some languages optimize tail-recursive functions (where the recursive call is the last operation in the function) to avoid stack overflow. Java does not currently support tail call optimization.

### Common Use Cases:
- **Tree Traversals**: Recursion is naturally suited for traversing tree structures.
- **Divide and Conquer Algorithms**: Algorithms like QuickSort and MergeSort use recursion to divide the problem into smaller subproblems.
- **Backtracking**: Problems like the N-Queens puzzle or solving mazes often use recursion to explore possible solutions.

Recursion is a powerful tool, but it should be used judiciously to avoid performance issues and stack overflow errors.
""",


"""
# OOP in Java

**Object-Oriented Programming (OOP)** in Java is a programming paradigm that organizes software design around "objects" rather than functions and logic. Java is inherently object-oriented, meaning it uses classes and objects to structure code in a reusable, modular, and organized way. OOP focuses on four core principles: **abstraction**, **encapsulation**, **inheritance**, and **polymorphism**.

---

### **Key Principles of OOP in Java**

#### 1. **Abstraction**  
   - **What**: Hiding complex implementation details and showing only essential features.  
   - **How**: Use **abstract classes** or **interfaces** to define a blueprint for objects.  
   - **Example**:  
     ```java
     abstract class Vehicle {
         abstract void start(); // Abstract method (no implementation)
     }

     class Car extends Vehicle {
         void start() {
             System.out.println("Car starts with a key!");
         }
     }
     ```

---

#### 2. **Encapsulation**  
   - **What**: Bundling data (variables) and methods (functions) into a single unit (class) and restricting direct access to data.  
   - **How**: Use **private** variables and provide **public getter/setter methods** to control access.  
   - **Example**:  
     ```java
     class BankAccount {
         private double balance; // Private variable

         // Public method to modify balance safely
         public void deposit(double amount) {
             if (amount > 0) balance += amount;
         }

         public double getBalance() {
             return balance;
         }
     }
     ```

---

#### 3. **Inheritance**  
   - **What**: Creating new classes (subclasses) from existing ones (superclasses) to reuse code.  
   - **How**: Use the `extends` keyword.  
   - **Example**:  
     ```java
     class Animal {
         void eat() {
             System.out.println("Animal eats food");
         }
     }

     class Dog extends Animal { // Dog inherits from Animal
         void bark() {
             System.out.println("Dog barks");
         }
     }
     ```

---

#### 4. **Polymorphism**  
   - **What**: Performing a single action in different ways.  
   - **How**:  
     - **Method Overriding**: Redefine a method in a subclass (runtime polymorphism).  
     - **Method Overloading**: Multiple methods with the same name but different parameters (compile-time polymorphism).  
   - **Example**:  
     ```java
     class Bird {
         void sing() {
             System.out.println("Bird sings");
         }
     }

     class Sparrow extends Bird {
         // Method overriding
         void sing() {
             System.out.println("Sparrow chirps");
         }

         // Method overloading
         void sing(String song) {
             System.out.println("Sparrow sings: " + song);
         }
     }
     ```

---

### **Example: OOP in Practice**
```java
// Class (Encapsulation + Abstraction)
public class Car {
    private String model; // Encapsulated field

    public Car(String model) {
        this.model = model;
    }

    public void drive() { // Abstraction of behavior
        System.out.println(model + " is driving.");
    }
}

// Inheritance
class ElectricCar extends Car {
    public ElectricCar(String model) {
        super(model);
    }

    // Polymorphism (method overriding)
    @Override
    public void drive() {
        System.out.println("Electric car drives silently!");
    }
}

public class Main {
    public static void main(String[] args) {
        Car myCar = new Car("Toyota");
        myCar.drive(); // Output: Toyota is driving.

        ElectricCar tesla = new ElectricCar("Tesla");
        tesla.drive(); // Output: Electric car drives silently!
    }
}
```

---

### **Why Use OOP in Java?**
1. **Reusability**: Reuse classes across projects (e.g., `ArrayList`, `HashMap`).  
2. **Modularity**: Break code into independent, manageable components.  
3. **Flexibility**: Polymorphism allows dynamic behavior.  
4. **Maintainability**: Encapsulation protects data integrity and simplifies debugging.  

---

### **Common Uses of OOP in Java**
- Building GUI applications (e.g., Swing, JavaFX).  
- Developing Android apps.  
- Enterprise software (e.g., Spring Framework).  
- Game development.  

OOP is the backbone of Java programming, making it easier to model real-world entities and solve complex problems efficiently. 🚀
""",



"""
# Classes in java


In Java, a **class** is a fundamental building block of object-oriented programming (OOP) that serves as a **blueprint** or **template** for creating objects. It defines the structure and behavior (data and methods) that the objects instantiated from it will possess. Here's a breakdown:

---

### **Components of a Class**
1. **Fields (Attributes/Properties)**  
   Variables that hold the state/data of an object.  
   Example: `String name; int age;`

2. **Methods (Behaviors)**  
   Functions that define actions an object can perform.  
   Example: `void eat() { ... }`

3. **Constructors**  
   Special methods used to initialize objects when they are created.  
   - Default constructor (provided if none is defined).  
   - Parameterized constructor (takes arguments).  

4. **Access Modifiers**  
   Control visibility (e.g., `public`, `private`, `protected`).  

5. **Static Members**  
   Belong to the class itself, not individual objects (e.g., `static int count;`).  

---

### **Example: Simple Class**
```java
public class Dog {
    // Fields (attributes)
    private String name;
    private int age;

    // Constructor
    public Dog(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Method (behavior)
    public void bark() {
        System.out.println(name + " says: Woof!");
    }

    // Getter method
    public String getName() {
        return name;
    }
}
```

---

### **Key Concepts**
1. **Object Creation**  
   Use the `new` keyword to create instances (objects) of a class:  
   ```java
   Dog myDog = new Dog("Buddy", 3);
   myDog.bark(); // Output: "Buddy says: Woof!"
   ```

2. **Inheritance**  
   A class can inherit fields/methods from another class using `extends`:  
   ```java
   public class Puppy extends Dog { // Subclass of Dog
       public Puppy(String name, int age) {
           super(name, age); // Calls parent constructor
       }
   }
   ```

3. **Encapsulation**  
   Hide internal data using `private` fields and expose via `public` methods (getters/setters).  

4. **Abstraction**  
   Abstract classes (`abstract class Shape`) can define methods without implementation.  

5. **Static vs. Instance Members**  
   - Static: Shared across all instances (e.g., `static int totalDogs;`).  
   - Instance: Unique to each object (e.g., `name` in the `Dog` class).  

---

### **Rules**
- A `.java` file can have only one `public` class, and the filename must match the public class name.  
- Classes can contain inner/nested classes (classes within classes).  

---

### **Why Classes Matter**
- **Reusability**: Define once, create multiple objects.  
- **Organization**: Group related data and behaviors.  
- **Modularity**: Isolate and manage complexity.  

In summary, classes are the foundation of Java's OOP, enabling you to model real-world entities and their interactions efficiently. 🚀
""",


"""
# Class in java

In Java, a **class** is a fundamental building block of object-oriented programming (OOP) that serves as a **blueprint** or **template** for creating objects. It defines the structure and behavior (data and methods) that the objects instantiated from it will possess. Here's a breakdown:

---

### **Components of a Class**
1. **Fields (Attributes/Properties)**  
   Variables that hold the state/data of an object.  
   Example: `String name; int age;`

2. **Methods (Behaviors)**  
   Functions that define actions an object can perform.  
   Example: `void eat() { ... }`

3. **Constructors**  
   Special methods used to initialize objects when they are created.  
   - Default constructor (provided if none is defined).  
   - Parameterized constructor (takes arguments).  

4. **Access Modifiers**  
   Control visibility (e.g., `public`, `private`, `protected`).  

5. **Static Members**  
   Belong to the class itself, not individual objects (e.g., `static int count;`).  

---

### **Example: Simple Class**
```java
public class Dog {
    // Fields (attributes)
    private String name;
    private int age;

    // Constructor
    public Dog(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Method (behavior)
    public void bark() {
        System.out.println(name + " says: Woof!");
    }

    // Getter method
    public String getName() {
        return name;
    }
}
```

---

### **Key Concepts**
1. **Object Creation**  
   Use the `new` keyword to create instances (objects) of a class:  
   ```java
   Dog myDog = new Dog("Buddy", 3);
   myDog.bark(); // Output: "Buddy says: Woof!"
   ```

2. **Inheritance**  
   A class can inherit fields/methods from another class using `extends`:  
   ```java
   public class Puppy extends Dog { // Subclass of Dog
       public Puppy(String name, int age) {
           super(name, age); // Calls parent constructor
       }
   }
   ```

3. **Encapsulation**  
   Hide internal data using `private` fields and expose via `public` methods (getters/setters).  

4. **Abstraction**  
   Abstract classes (`abstract class Shape`) can define methods without implementation.  

5. **Static vs. Instance Members**  
   - Static: Shared across all instances (e.g., `static int totalDogs;`).  
   - Instance: Unique to each object (e.g., `name` in the `Dog` class).  

---

### **Rules**
- A `.java` file can have only one `public` class, and the filename must match the public class name.  
- Classes can contain inner/nested classes (classes within classes).  

---

### **Why Classes Matter**
- **Reusability**: Define once, create multiple objects.  
- **Organization**: Group related data and behaviors.  
- **Modularity**: Isolate and manage complexity.  

In summary, classes are the foundation of Java's OOP, enabling you to model real-world entities and their interactions efficiently. 🚀
""",


"""
# Create class 

Creating a class in Java is straightforward. A class is defined using the `class` keyword, followed by the class name and a body enclosed in curly braces `{}`. Here's a step-by-step guide:

---

### **Steps to Create a Class in Java**
1. **Define the Class**  
   Use the `class` keyword followed by the class name.  
   Example:  
   ```java
   public class MyClass {
       // Class body
   }
   ```

2. **Add Fields (Attributes)**  
   Declare variables to represent the state of the object.  
   Example:  
   ```java
   private int age;
   private String name;
   ```

3. **Add Constructors**  
   Define a constructor to initialize objects. If no constructor is provided, Java uses a default constructor.  
   Example:  
   ```java
   public MyClass(int age, String name) {
       this.age = age;
       this.name = name;
   }
   ```

4. **Add Methods (Behaviors)**  
   Define methods to represent the actions the object can perform.  
   Example:  
   ```java
   public void displayInfo() {
       System.out.println("Name: " + name + ", Age: " + age);
   }
   ```

5. **Add Getters and Setters (Optional)**  
   Provide methods to access and modify private fields.  
   Example:  
   ```java
   public String getName() {
       return name;
   }

   public void setName(String name) {
       this.name = name;
   }
   ```

---

### **Example: Complete Class**
```java
public class Person {
    // Fields (attributes)
    private String name;
    private int age;

    // Constructor
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Method (behavior)
    public void displayInfo() {
        System.out.println("Name: " + name + ", Age: " + age);
    }

    // Getter for name
    public String getName() {
        return name;
    }

    // Setter for name
    public void setName(String name) {
        this.name = name;
    }
}
```

---

### **Using the Class**
To use the class, create an object of the class in another class (usually the `main` class) and call its methods.

```java
public class Main {
    public static void main(String[] args) {
        // Create an object of the Person class
        Person person1 = new Person("Alice", 25);

        // Call methods on the object
        person1.displayInfo(); // Output: Name: Alice, Age: 25

        // Use setter to change the name
        person1.setName("Bob");
        person1.displayInfo(); // Output: Name: Bob, Age: 25
    }
}
```

---

### **Key Points**
1. **Class Naming Convention**  
   - Use PascalCase (e.g., `MyClass`, `Person`).  
   - The class name should be meaningful and describe the entity it represents.  

2. **Access Modifiers**  
   - `public`: The class is accessible from anywhere.  
   - `default` (no modifier): The class is accessible only within the same package.  

3. **File Naming**  
   - Save the file as `<ClassName>.java` (e.g., `Person.java`).  

4. **Main Method**  
   - The `main` method is the entry point of a Java program and is required to execute the program.  

---

### **Summary**
To create a class in Java:
1. Use the `class` keyword.
2. Define fields, constructors, and methods.
3. Use the class by creating objects and calling methods.

This is the foundation of Java's object-oriented programming! 🚀
""",


"""
# Object in Java

In Java, an **object** is an **instance of a class**. It is a fundamental concept in object-oriented programming (OOP) that represents a real-world entity. Objects are created from classes and encapsulate both **data (state)** and **behavior (methods)**.

---

### **Key Characteristics of an Object**
1. **State (Fields/Attributes)**  
   - Represented by the values of an object's fields.  
   - Example: For a `Car` object, the state could include `color`, `model`, and `speed`.

2. **Behavior (Methods)**  
   - Represented by the methods that operate on the object's state.  
   - Example: For a `Car` object, behavior could include `accelerate()`, `brake()`, and `honk()`.

3. **Identity**  
   - Each object has a unique identity, even if its state is the same as another object.  
   - In Java, objects are stored in memory, and their identity is tied to their memory address.

---

### **How Objects Work in Java**
1. **Objects are created from classes.**  
   A class is a blueprint, and an object is an instance of that blueprint.

2. **Objects are created using the `new` keyword.**  
   Example:  
   ```java
   Car myCar = new Car();
   ```

3. **Objects can interact with each other.**  
   They can call each other's methods and share data.

---

### **Example: Object in Java**
Let's use a `Car` class to demonstrate objects:

#### **Step 1: Define the Class**
```java
public class Car {
    // Fields (state)
    private String color;
    private String model;
    private int speed;

    // Constructor
    public Car(String color, String model) {
        this.color = color;
        this.model = model;
        this.speed = 0; // Default speed
    }

    // Methods (behavior)
    public void accelerate(int increment) {
        speed += increment;
    }

    public void brake(int decrement) {
        speed -= decrement;
    }

    public void displayInfo() {
        System.out.println("Model: " + model + ", Color: " + color + ", Speed: " + speed);
    }
}
```

#### **Step 2: Create and Use Objects**
```java
public class Main {
    public static void main(String[] args) {
        // Create an object of the Car class
        Car myCar = new Car("Red", "Toyota");

        // Call methods on the object
        myCar.accelerate(30); // Increase speed by 30
        myCar.displayInfo();  // Output: Model: Toyota, Color: Red, Speed: 30

        myCar.brake(10);      // Decrease speed by 10
        myCar.displayInfo();  // Output: Model: Toyota, Color: Red, Speed: 20
    }
}
```

---

### **Key Points About Objects**
1. **Objects are created at runtime.**  
   They occupy memory and exist while the program is running.

2. **Objects are independent.**  
   Each object has its own copy of the class's fields.

3. **Objects communicate via methods.**  
   Methods define how objects interact with each other.

4. **Objects can be passed as arguments.**  
   You can pass objects to methods or return them from methods.

---

### **Object vs. Class**
| **Class**                          | **Object**                          |
|-------------------------------------|-------------------------------------|
| A blueprint or template.            | An instance of a class.             |
| Defined once.                       | Created multiple times.             |
| Does not occupy memory.             | Occupies memory.                    |
| Contains fields and methods.        | Contains actual data and behavior.  |

---

### **Why Objects Matter**
- **Modularity**: Break down complex systems into smaller, manageable parts.  
- **Reusability**: Reuse classes to create multiple objects.  
- **Encapsulation**: Hide internal details and expose only necessary functionality.  
- **Abstraction**: Focus on what an object does, not how it does it.  

In summary, objects are the building blocks of Java programs, enabling you to model real-world entities and their interactions. 🚀
""",



"""
# Creating object

In Java, an **object** is created from a **class** using the `new` keyword. The process involves defining a class, creating an instance of that class (object), and then using the object to access its fields and methods. Here's a step-by-step guide:

---

### **Steps to Create an Object in Java**
1. **Define a Class**  
   First, you need a class that serves as a blueprint for the object.  
   Example:  
   ```java
   public class Car {
       // Fields (attributes)
       private String color;
       private String model;

       // Constructor
       public Car(String color, String model) {
           this.color = color;
           this.model = model;
       }

       // Method (behavior)
       public void displayInfo() {
           System.out.println("Model: " + model + ", Color: " + color);
       }
   }
   ```

2. **Create an Object Using the `new` Keyword**  
   Use the `new` keyword followed by the class constructor to create an object.  
   Syntax:  
   ```java
   ClassName objectName = new ClassName(arguments);
   ```

   Example:  
   ```java
   Car myCar = new Car("Red", "Toyota");
   ```

3. **Access Fields and Methods**  
   Use the object to call methods or access fields (if they are public).  
   Example:  
   ```java
   myCar.displayInfo(); // Output: Model: Toyota, Color: Red
   ```

---

### **Example: Full Program**
Here’s a complete example of creating and using an object:

#### **Step 1: Define the Class**
```java
public class Car {
    // Fields (attributes)
    private String color;
    private String model;

    // Constructor
    public Car(String color, String model) {
        this.color = color;
        this.model = model;
    }

    // Method (behavior)
    public void displayInfo() {
        System.out.println("Model: " + model + ", Color: " + color);
    }
}
```

#### **Step 2: Create and Use the Object**
```java
public class Main {
    public static void main(String[] args) {
        // Create an object of the Car class
        Car myCar = new Car("Red", "Toyota");

        // Call a method on the object
        myCar.displayInfo(); // Output: Model: Toyota, Color: Red
    }
}
```

---

### **Key Points About Object Creation**
1. **`new` Keyword**  
   - Allocates memory for the object.  
   - Calls the constructor to initialize the object.

2. **Constructor**  
   - A special method used to initialize objects.  
   - If no constructor is defined, Java provides a default constructor.

3. **Object Reference**  
   - The object is stored in memory, and the variable (`myCar` in the example) holds a reference to it.

4. **Multiple Objects**  
   - You can create multiple objects from the same class.  
   Example:  
   ```java
   Car car1 = new Car("Blue", "Honda");
   Car car2 = new Car("Black", "Ford");
   ```

---

### **Example: Multiple Objects**
```java
public class Main {
    public static void main(String[] args) {
        // Create multiple objects
        Car car1 = new Car("Blue", "Honda");
        Car car2 = new Car("Black", "Ford");

        // Call methods on the objects
        car1.displayInfo(); // Output: Model: Honda, Color: Blue
        car2.displayInfo(); // Output: Model: Ford, Color: Black
    }
}
```

---

### **Common Mistakes**
1. **Forgetting the `new` Keyword**  
   - Without `new`, the object is not created, and you'll get a compilation error.  
   Example of incorrect usage:  
   ```java
   Car myCar = Car("Red", "Toyota"); // Error: Missing 'new'
   ```

2. **Using a Constructor That Doesn't Exist**  
   - Ensure the constructor matches the class definition.  
   Example of incorrect usage:  
   ```java
   Car myCar = new Car(); // Error: If no default constructor is defined
   ```

3. **Accessing Private Fields Directly**  
   - Private fields cannot be accessed directly from outside the class. Use getters/setters instead.  
   Example of incorrect usage:  
   ```java
   System.out.println(myCar.color); // Error: 'color' is private
   ```

---

### **Summary**
To create an object in Java:
1. Define a class with fields and methods.
2. Use the `new` keyword to create an object.
3. Call methods or access fields using the object.

Objects are the foundation of Java's object-oriented programming, enabling you to model real-world entities and their interactions. 🚀
""",


"""
# Classes and Objects

In Java, **classes** and **objects** are fundamental concepts of Object-Oriented Programming (OOP). They allow you to model real-world entities and their behaviors in your programs.

---

### **Class**
A class is a blueprint or template for creating objects. It defines the properties (attributes) and behaviors (methods) that the objects created from the class will have.

#### Structure of a Class:
```java
public class ClassName {
    // Fields (attributes or properties)
    dataType fieldName;

    // Constructor (used to initialize objects)
    public ClassName(parameters) {
        // Initialization code
    }

    // Methods (behaviors or actions)
    returnType methodName(parameters) {
        // Method implementation
    }
}
```

#### Example of a Class:
```java
public class Car {
    // Fields (attributes)
    String brand;
    String color;
    int year;

    // Constructor
    public Car(String brand, String color, int year) {
        this.brand = brand;
        this.color = color;
        this.year = year;
    }

    // Method (behavior)
    public void start() {
        System.out.println("The " + color + " " + brand + " is starting.");
    }
}
```

---

### **Object**
An object is an instance of a class. It is created using the `new` keyword and represents a specific entity based on the class blueprint. Each object has its own state (values for fields) and can perform actions (methods).

#### Creating an Object:
```java
ClassName objectName = new ClassName(arguments);
```

#### Example of Creating an Object:
```java
public class Main {
    public static void main(String[] args) {
        // Create an object of the Car class
        Car myCar = new Car("Toyota", "Red", 2020);

        // Access fields and methods
        System.out.println("Brand: " + myCar.brand);
        System.out.println("Color: " + myCar.color);
        System.out.println("Year: " + myCar.year);

        // Call a method
        myCar.start();
    }
}
```

#### Output:
```
Brand: Toyota
Color: Red
Year: 2020
The Red Toyota is starting.
```

---

### Key Points:
1. **Class**: A blueprint or template for creating objects.
2. **Object**: An instance of a class, representing a specific entity.
3. **Fields**: Variables that define the state of an object.
4. **Methods**: Functions that define the behavior of an object.
5. **Constructor**: A special method used to initialize objects.

---

### Example Summary:
- **Class**: `Car` (defines properties like `brand`, `color`, `year` and behaviors like `start()`).
- **Object**: `myCar` (an instance of the `Car` class with specific values for `brand`, `color`, and `year`).

This is the foundation of OOP in Java!
""",



"""
# Classes and Objects

Sure thing! Let’s dive into Java’s world of classes and objects:

### **Classes:**
A class in Java can be thought of as a blueprint or a template that defines the properties and behaviors (methods) that an object of that class will have. It's like a prototype for creating objects. Here's a basic structure of a class:

```java
public class Car {
    // Fields or properties
    private String color;
    private String model;

    // Constructor
    public Car(String color, String model) {
        this.color = color;
        this.model = model;
    }

    // Methods or behaviors
    public void startEngine() {
        System.out.println("Engine started");
    }
}
```

### **Objects:**
An object is an instance of a class. When a class is defined, no memory is allocated until an object of that class is created. Here's how you can create an object from the `Car` class:

```java
public class Main {
    public static void main(String[] args) {
        // Creating an object of the Car class
        Car myCar = new Car("Red", "Toyota");

        // Accessing fields and methods
        myCar.startEngine();
    }
}
```

### Key Points:
- **Class:** Blueprint for objects, defining properties and behaviors.
- **Object:** Instance of a class, representing a specific implementation of the blueprint.

Do you want to explore more about Java or any specific concepts within it? 🖥️✨

""",



"""
# Creating classes and objects

In Java, classes and objects are fundamental concepts of Object-Oriented Programming (OOP). A class is a blueprint for creating objects, and an object is an instance of a class. Below is a step-by-step guide on how to create classes and objects in Java:

---

### 1. **Define a Class**
A class is defined using the `class` keyword. It can contain fields (variables), methods (functions), constructors, and other components.

```java
// Syntax for defining a class
class ClassName {
    // Fields (variables)
    dataType fieldName;

    // Constructor (optional)
    ClassName(parameters) {
        // Initialization code
    }

    // Methods (functions)
    returnType methodName(parameters) {
        // Method body
    }
}
```

#### Example:
```java
// Define a class named "Car"
class Car {
    // Fields (attributes)
    String brand;
    String model;
    int year;

    // Constructor
    Car(String brand, String model, int year) {
        this.brand = brand;
        this.model = model;
        this.year = year;
    }

    // Method
    void displayInfo() {
        System.out.println("Brand: " + brand + ", Model: " + model + ", Year: " + year);
    }
}
```

---

### 2. **Create an Object**
An object is an instance of a class. You create an object using the `new` keyword and the class constructor.

#### Syntax:
```java
ClassName objectName = new ClassName(arguments);
```

#### Example:
```java
public class Main {
    public static void main(String[] args) {
        // Create an object of the Car class
        Car myCar = new Car("Toyota", "Corolla", 2020);

        // Access fields and methods of the object
        myCar.displayInfo(); // Output: Brand: Toyota, Model: Corolla, Year: 2020
    }
}
```

---

### 3. **Key Points**
- **Fields**: Variables that belong to the class or object.
- **Methods**: Functions that define the behavior of the class or object.
- **Constructor**: A special method used to initialize objects. It has the same name as the class.
- **`this` Keyword**: Refers to the current object instance.

---

### 4. **Full Example**
Here’s a complete example:

```java
// Define a class
class Dog {
    // Fields
    String name;
    int age;

    // Constructor
    Dog(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Method
    void bark() {
        System.out.println(name + " is barking!");
    }
}

// Main class
public class Main {
    public static void main(String[] args) {
        // Create an object of the Dog class
        Dog myDog = new Dog("Buddy", 3);

        // Access fields and methods
        System.out.println("Name: " + myDog.name); // Output: Name: Buddy
        System.out.println("Age: " + myDog.age);   // Output: Age: 3
        myDog.bark(); // Output: Buddy is barking!
    }
}
```

---

### 5. **Output**
When you run the above program, the output will be:
```
Name: Buddy
Age: 3
Buddy is barking!
```

---

This is the basic structure for creating classes and objects in Java. You can expand on this by adding more fields, methods, and constructors as needed.
""",


"""
# Multiple objects

In Java, you can create and work with multiple objects by following these steps:

1. **Define a Class:** First, you need a blueprint for your objects, which is the class. For example:
```java
public class Dog {
    String name;
    int age;
    
    // Constructor
    public Dog(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    // Method
    public void bark() {
        System.out.println(name + " is barking");
    }
}
```

2. **Create Objects:** Next, you can create multiple objects of the class using the `new` keyword.
```java
public class Main {
    public static void main(String[] args) {
        // Creating multiple objects
        Dog dog1 = new Dog("Buddy", 3);
        Dog dog2 = new Dog("Max", 2);
        
        // Calling methods on objects
        dog1.bark(); // Output: Buddy is barking
        dog2.bark(); // Output: Max is barking
    }
}
```

In this example:
- We define a `Dog` class with attributes `name` and `age`, a constructor to initialize these attributes, and a method `bark()`.
- In the `Main` class, we create two `Dog` objects (`dog1` and `dog2`) and call the `bark()` method on each object.

Each object is an instance of the `Dog` class, with its own set of attributes and methods.

Feel free to ask if you have more questions about Java or any other topic!
""",


"""
# Multiple classes

In Java, multiple classes can be defined within a single source file, but there are some rules and conventions to follow:

### 1. **Single Public Class per File**:
   - A Java source file (`.java`) can contain only **one public class**.
   - The name of the public class must match the name of the file.
   - For example, if the file is named `MyProgram.java`, the public class inside it must be named `MyProgram`.

   ```java
   // MyProgram.java
   public class MyProgram {
       public static void main(String[] args) {
           System.out.println("Hello, World!");
       }
   }
   ```

### 2. **Non-Public Classes**:
   - You can define additional **non-public classes** in the same file.
   - These classes can have any name, and they are accessible only within the same file.

   ```java
   // MyProgram.java
   public class MyProgram {
       public static void main(String[] args) {
           Helper helper = new Helper();
           helper.display();
       }
   }

   class Helper {
       void display() {
           System.out.println("This is a helper class.");
       }
   }
   ```

### 3. **Nested Classes**:
   - Java allows you to define classes within other classes. These are called **nested classes**.
   - Nested classes can be **static** or **non-static** (inner classes).

   ```java
   public class OuterClass {
       private int outerField = 10;

       // Inner class
       class InnerClass {
           void display() {
               System.out.println("Outer field value: " + outerField);
           }
       }

       // Static nested class
       static class StaticNestedClass {
           void display() {
               System.out.println("This is a static nested class.");
           }
       }
   }
   ```

### 4. **Anonymous Classes**:
   - Java also supports **anonymous classes**, which are classes without a name and are defined and instantiated at the same time.

   ```java
   interface Greeting {
       void greet();
   }

   public class MyProgram {
       public static void main(String[] args) {
           Greeting greeting = new Greeting() {
               @Override
               public void greet() {
                   System.out.println("Hello from an anonymous class!");
               }
           };
           greeting.greet();
       }
   }
   ```

### 5. **Multiple Classes in Separate Files**:
   - If you want to define multiple public classes, each public class must be in its own file.
   - For example:
     - `ClassA.java` contains `public class ClassA`.
     - `ClassB.java` contains `public class ClassB`.

### Summary:
- A single Java file can have **one public class** and **multiple non-public classes**.
- Nested classes and anonymous classes provide additional ways to organize and encapsulate code.
- Each public class must reside in its own file with the same name as the class.

This structure helps maintain clarity and organization in Java programs.
"""


    
 
        
    ]

    # Tokenizer and preprocessing
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(questions)

    vocab_size = len(tokenizer.word_index) + 1
    max_length = max(len(q.split()) for q in questions)
    question_sequences = tokenizer.texts_to_sequences(questions)
    padded_questions = pad_sequences(question_sequences, maxlen=max_length, padding='post')

    answer_indices = np.array(range(len(answers)))
    one_hot_answers = to_categorical(answer_indices, num_classes=len(answers))

    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=16, input_length=max_length),
        LSTM(32),
        Dense(16, activation='relu'),
        Dense(len(answers), activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(padded_questions, one_hot_answers, epochs=10, verbose=1)
    model.save("my_model.keras")

    def process_input(user_input, chat_display, input_field, user_id):
        if not user_input.strip():
            return

        # Enable chat display for updating
        chat_display.configure(state="normal")
        
        # Add user message
        chat_display.insert(END, f"You: {user_input}\n", "user")
        chat_display.tag_configure("user", foreground="#2962ff", font=("Helvetica", 12, "bold"))
        
        # Find best matching answer
        best_match = None
        highest_similarity = 0
        
        for q, a in zip(questions, answers):
            similarity = cosine_similarity(
                TfidfVectorizer().fit_transform([q.lower(), user_input.lower()])
            )[0][1]
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = a
        
        # Add AI response
        chat_display.insert(END, "\nAI Assistant: ", "ai_prefix")
        chat_display.tag_configure("ai_prefix", foreground="#00c853", font=("Helvetica", 12, "bold"))
        
        if highest_similarity >= 0.3:  # Threshold for acceptable match
            chat_display.insert(END, f"{best_match}\n\n", "ai_response")
        else:
            chat_display.insert(END, "I'm sorry, I don't have a specific answer for that question. Please try rephrasing or ask another question about Java.\n\n", "ai_response")
        
        chat_display.tag_configure("ai_response", foreground="#263238", font=("Helvetica", 12))
        
        # Save to history
        cursor.execute("INSERT INTO history (user_id, query) VALUES (?, ?)", (user_id, user_input))
        conn.commit()
        
        # Clear input field
        input_field.delete(0, END)
        
        # Scroll to bottom
        chat_display.see(END)
        
        # Disable chat display
        chat_display.configure(state="disabled")

   

   

    # Bind Enter key to send message
    user_input.bind("<Return>", lambda event: process_input(user_input.get(), chat_display, user_input, user_id))

    # Set focus to input field
    user_input.focus_set()

    # Add initial greeting to chat
    chat_display.insert(END, "AI Assistant: Hello! How can I help you today?\n\n")
    chat_display.configure(state="disabled")

def show_history_dashboard(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    # Color scheme
    PRIMARY_COLOR = "#2962ff"
    BG_COLOR = "#f5f5f5"
    CARD_BG = "#ffffff"
    TEXT_COLOR = "#263238"

    # Configure root window
    root.configure(bg=BG_COLOR)
    root.geometry("1400x900")
    root.title("History Dashboard - Java AI Teacher")

    # Create main container
    main_frame = Frame(root, bg=BG_COLOR)
    main_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    # Header
    header_frame = Frame(main_frame, bg=PRIMARY_COLOR, height=80)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="History Dashboard",
        font=("Helvetica", 24, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(side=LEFT, padx=40, pady=20)

    Button(
        header_frame,
        text="🏠 Back to Dashboard",
        command=lambda: show_ai_dashboard(user_id, user_name),
        font=("Helvetica", 12, "bold"),
        bg="white",
        fg=PRIMARY_COLOR,
        relief=FLAT,
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(side=RIGHT, padx=40, pady=20)

    # History content
    history_frame = Frame(main_frame, bg=CARD_BG, relief=GROOVE, bd=1)
    history_frame.pack(fill=BOTH, expand=True, pady=30)

    # Create a canvas for scrolling
    canvas = Canvas(history_frame, bg=CARD_BG)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    # Create a scrollbar for the canvas
    history_scrollbar = Scrollbar(history_frame, orient=VERTICAL, command=canvas.yview)
    history_scrollbar.pack(side=RIGHT, fill=Y)

    # Configure the canvas
    canvas.configure(yscrollcommand=history_scrollbar.set)

    # Create a frame inside the canvas to hold the history items
    history_inner_frame = Frame(canvas, bg=CARD_BG)
    canvas.create_window((0, 0), window=history_inner_frame, anchor='nw')

    # Ensure the scrollbar updates when the history frame changes
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    history_inner_frame.bind("<Configure>", on_configure)

    # Fetch user history
    history = cursor.execute("SELECT id, query FROM history WHERE user_id = ?", (user_id,)).fetchall()

    # Display history
    for i, item in enumerate(history, 1):
        history_card = Frame(history_inner_frame, bg=CARD_BG)
        history_card.pack(fill=X, padx=20, pady=10)

        Label(
            history_card,
            text=f"Query {i}: {item[1]}",
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(padx=20, pady=(10, 5))

        Button(
            history_card,
            text="Delete Query",
            command=lambda q_id=item[0]: delete_history_item(user_id, user_name, q_id),
            font=("Helvetica", 10),
            bg="#dc3545",
            fg="white",
            relief=FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=RIGHT, padx=10)

def delete_history_item(user_id, user_name, history_id):
    try:
        # Check if the history ID exists
        cursor.execute("SELECT id FROM history WHERE id = ?", (history_id,))
        result = cursor.fetchone()

        if result is None:
            print(f"No history found with ID: {history_id}")
        else:
            # Delete the history item
            cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
            conn.commit()
            print(f"History item with ID {history_id} deleted successfully.")
        
        # Refresh the history dashboard
        show_history_dashboard(user_id, user_name)
    except Exception as e:
        print(f"Error deleting history item: {e}")

# Function to delete all history items for a user
def delete_all_history(user_id, user_name):
    try:
        # Check if the user has any history
        cursor.execute("SELECT id FROM history WHERE user_id = ?", (user_id,))
        results = cursor.fetchall()

        if not results:
            print(f"No history found for user ID: {user_id}")
        else:
            # Delete all history items for the user
            cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            conn.commit()
            print(f"All history for user ID {user_id} deleted successfully.")
        
        # Refresh the history dashboard
        show_history_dashboard(user_id, user_name)
    except Exception as e:
        print(f"Error deleting all history: {e}")

    
# Show login screen
def show_login():
    for widget in root.winfo_children():
        widget.destroy()
    create_login_form()

def create_login_form():
    # Stylish gradient-like background
    root.configure(bg="#1a1a2e")  # Set background color to a stylish dark theme

    Label(root, text="User Login Form", font=("Arial", 28, "bold"), bg="#16213e", fg="white").pack(pady=20)

    global entry_email, entry_password

    # Stylish frame for the login form
    frame = Frame(root, bg="#0f3460", relief=RIDGE, bd=5)
    frame.pack(pady=50)

    Label(frame, text="Email", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=0, column=0, pady=15, padx=15)
    entry_email = Entry(frame, width=30, font=("Arial", 14))
    entry_email.grid(row=0, column=1, pady=15, padx=15)

    Label(frame, text="Password", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=1, column=0, pady=15, padx=15)
    entry_password = Entry(frame, width=30, font=("Arial", 14), show="*")
    entry_password.grid(row=1, column=1, pady=15, padx=15)

    toggle_btn = Button(frame, text="🔒", command=lambda: toggle_password(entry_password, toggle_btn), bg="#0f3460", fg="white", relief=FLAT)
    toggle_btn.grid(row=1, column=2, padx=5)

    Button(frame, text="Login", command=user_login, bg="#1fab89", fg="white", font=("Arial", 14), relief=GROOVE).grid(row=2, column=0, columnspan=3, pady=20)
    Button(frame, text="Register Here", command=show_register, bg="#3282b8", fg="white", font=("Arial", 14), relief=GROOVE).grid(row=3, column=0, columnspan=3)

    # Add Admin Login Button
    Button(root, text="Admin Login", command=show_admin_login, bg="#e94560", fg="white", font=("Arial", 12), relief=GROOVE).place(x=10, y=10)

# Helper function to toggle password visibility
def toggle_password(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="🔓")
    else:
        entry.config(show="*")
        button.config(text="🔒")

# Register screen
def show_register():
    for widget in root.winfo_children():
        widget.destroy()
    create_register_form()

def create_register_form():
    # Stylish gradient-like background
    root.configure(bg="#1a1a2e")  # Set background color to match the login theme

    Label(root, text="Register Form", font=("Arial", 28, "bold"), bg="#16213e", fg="white").pack(pady=20)

    global entry_email, entry_password, entry_name, entry_surname, entry_class

    # Stylish frame for the registration form
    frame = Frame(root, bg="#0f3460", relief=RIDGE, bd=5)
    frame.pack(pady=50)

    Label(frame, text="Email", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=0, column=0, pady=15, padx=15)
    entry_email = Entry(frame, width=30, font=("Arial", 14))
    entry_email.grid(row=0, column=1, pady=15, padx=15)

    Label(frame, text="Password", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=1, column=0, pady=15, padx=15)
    entry_password = Entry(frame, width=30, font=("Arial", 14), show="*")
    entry_password.grid(row=1, column=1, pady=15, padx=15)

    toggle_btn = Button(frame, text="🔒", command=lambda: toggle_password(entry_password, toggle_btn), bg="#0f3460", fg="white", relief=FLAT)
    toggle_btn.grid(row=1, column=2, padx=5)

    Label(frame, text="Name", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=2, column=0, pady=15, padx=15)
    entry_name = Entry(frame, width=30, font=("Arial", 14))
    entry_name.grid(row=2, column=1, pady=15, padx=15)

    Label(frame, text="Surname", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=3, column=0, pady=15, padx=15)
    entry_surname = Entry(frame, width=30, font=("Arial", 14))
    entry_surname.grid(row=3, column=1, pady=15, padx=15)

    Label(frame, text="Class", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=4, column=0, pady=15, padx=15)
    entry_class = Entry(frame, width=30, font=("Arial", 14))
    entry_class.grid(row=4, column=1, pady=15, padx=15)

    Button(frame, text="Register", command=register, bg="#1fab89", fg="white", font=("Arial", 14), relief=GROOVE).grid(row=5, column=0, columnspan=3, pady=20)
    
    # Add a Back button
    Button(root, text="Back to Login", command=show_login, bg="#e94560", fg="white", font=("Arial", 14), relief=GROOVE).place(x=10, y=10)
    
# Helper function to toggle password visibility
def toggle_password(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="🔓")
    else:
        entry.config(show="*")
        button.config(text="🔒")

# Admin login and registration logic
def show_admin_login():
    for widget in root.winfo_children():
        widget.destroy()
    create_admin_login_form()

def create_admin_login_form():
    # Set a stylish background color
    root.configure(bg="#1a1a2e")  # Consistent dark theme with other forms

    Label(root, text="Admin Login Form", font=("Arial", 28, "bold"), bg="#16213e", fg="white").pack(pady=20)

    global admin_email, admin_password

    # Frame for the form
    frame = Frame(root, bg="#0f3460", relief=RIDGE, bd=5)
    frame.pack(pady=50)

    Label(frame, text="Admin Email", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=0, column=0, pady=15, padx=15)
    admin_email = Entry(frame, width=30, font=("Arial", 14))
    admin_email.grid(row=0, column=1, pady=15, padx=15)

    Label(frame, text="Password", font=("Arial", 16, "bold"), bg="#0f3460", fg="white").grid(row=1, column=0, pady=15, padx=15)
    admin_password = Entry(frame, width=30, font=("Arial", 14), show="*")
    admin_password.grid(row=1, column=1, pady=15, padx=15)

    toggle_btn = Button(frame, text="🔒", command=lambda: toggle_password(admin_password, toggle_btn), bg="#0f3460", fg="white", relief=FLAT)
    toggle_btn.grid(row=1, column=2, padx=5)

    Button(frame, text="Login", command=admin_login, bg="#1fab89", fg="white", font=("Arial", 14), relief=GROOVE).grid(row=2, column=0, columnspan=3, pady=20)
    
    # Add a Back button
    Button(root, text="Back to User Login", command=show_login, bg="#e94560", fg="white", font=("Arial", 14), relief=GROOVE).place(x=10, y=10)

# Helper function to toggle password visibility
def toggle_password(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="🔓")
    else:
        entry.config(show="*")
        button.config(text="🔒")

# Initialize window
root = Tk()
root.geometry("800x600")
root.title("Java AI Teacher")

# Load background image
 

# Show login form
show_login()

# Run the application
root.mainloop()

def show_practice_dashboard(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    # Color scheme    log_text.insert(END, "[WARNING] High traffic detected\n")

    PRIMARY_COLOR = "#2962ff"
    BG_COLOR = "#f5f5f5"
    CARD_BG = "#ffffff"
    TEXT_COLOR = "#263238"

    # Configure root window
    root.configure(bg=BG_COLOR)
    root.geometry("1400x900")
    root.title("Practice Questions - Java AI Teacher")

    # Create main container
    main_frame = Frame(root, bg=BG_COLOR)
    main_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    # Header
    header_frame = Frame(main_frame, bg=PRIMARY_COLOR, height=80)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="Practice Questions",
        font=("Helvetica", 24, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(side=LEFT, padx=40, pady=20)

    Button(
        header_frame,
        text="🏠 Back to Dashboard",
        command=lambda: show_ai_dashboard(user_id, user_name),
        font=("Helvetica", 12, "bold"),
        bg="white",
        fg=PRIMARY_COLOR,
        relief=FLAT,
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(side=RIGHT, padx=40, pady=20)

    # Practice categories
    categories_frame = Frame(main_frame, bg=BG_COLOR)
    categories_frame.pack(fill=BOTH, expand=True, pady=30)

    practice_categories = [
        ("Basic Java Syntax", "Learn the fundamentals of Java programming syntax"),
        ("Variables & Data Types", "Practice with different variable types and declarations"),
        ("Control Flow", "Master if statements, loops, and switch cases"),
        ("Object-Oriented Programming", "Understand classes, objects, inheritance, and polymorphism"),
        ("Exception Handling", "Learn to handle errors and exceptions in Java"),
        ("Collections Framework", "Work with Lists, Sets, Maps, and other collections")
    ]

    def start_practice(category):
        show_practice_questions(user_id, user_name, category)

    row = 0
    col = 0
    for category, description in practice_categories:
        card = Frame(categories_frame, bg=CARD_BG, relief=GROOVE, bd=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        Label(
            card,
            text=category,
            font=("Helvetica", 16, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(padx=20, pady=(20,10))
        
        Label(
            card,
            text=description,
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            wraplength=300
        ).pack(padx=20, pady=(0,20))
        
        Button(
            card,
            text="Start Practice →",
            command=lambda c=category: start_practice(c),
            font=("Helvetica", 12),
            bg=PRIMARY_COLOR,
            fg="white",
            relief=FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(padx=20, pady=20)
        
        col += 1
        if col > 1:
            col = 0
            row += 1
    
    # Configure grid weights
    categories_frame.grid_columnconfigure(0, weight=1)
    categories_frame.grid_columnconfigure(1, weight=1)

def show_settings_dashboard(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    # Color scheme
    PRIMARY_COLOR = "#2962ff"
    SECONDARY_COLOR = "#00c853"
    BG_COLOR = "#f5f5f5"
    CARD_BG = "#ffffff"
    TEXT_COLOR = "#263238"

    # Configure root window
    root.configure(bg=BG_COLOR)
    root.geometry("1400x900")
    root.title("Settings - Java AI Teacher")

    # Create main container
    main_frame = Frame(root, bg=BG_COLOR)
    main_frame.pack(fill=BOTH, expand=True, padx=40, pady=30)

    # Header
    header_frame = Frame(main_frame, bg=PRIMARY_COLOR, height=80)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame,
        text="Settings",
        font=("Helvetica", 24, "bold"),
        fg="white",
        bg=PRIMARY_COLOR
    ).pack(side=LEFT, padx=40, pady=20)

    Button(
        header_frame,
        text="🏠 Back to Dashboard",
        command=lambda: show_ai_dashboard(user_id, user_name),
        font=("Helvetica", 12, "bold"),
        bg="white",
        fg=PRIMARY_COLOR,
        relief=FLAT,
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(side=RIGHT, padx=40, pady=20)

    # Settings content
    settings_frame = Frame(main_frame, bg=CARD_BG, relief=GROOVE, bd=1)
    settings_frame.pack(fill=BOTH, expand=True, pady=30)

    # Create a canvas and scrollbar for scrollable content
    canvas = Canvas(settings_frame, bg=CARD_BG)
    scrollbar = Scrollbar(settings_frame, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas, bg=CARD_BG)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack the canvas and scrollbar
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    def create_section_header(text):
        return Label(
            scrollable_frame,
            text=text,
            font=("Helvetica", 18, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            anchor="w"
        )

    def create_setting_label(text):
        return Label(
            scrollable_frame,
            text=text,
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            anchor="w"
        )

    def create_button(text, command, color=PRIMARY_COLOR):
        return Button(
            scrollable_frame,
            text=text,
            command=command,
            font=("Helvetica", 12, "bold"),
            bg=color,
            fg="white",
            relief=FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )

    # Profile Settings Section
    create_section_header("Profile Settings").pack(anchor="w", padx=40, pady=(30,20))

    # Get current user info
    cursor.execute("SELECT name, class_name, email FROM users WHERE id=?", (user_id,))
    current_user = cursor.fetchone()

    # Name setting
    create_setting_label("Name:").pack(anchor="w", padx=40, pady=(10,5))
    name_entry = Entry(scrollable_frame, font=("Helvetica", 12), width=40)
    name_entry.insert(0, current_user[0])
    name_entry.pack(anchor="w", padx=40)

    # Class setting
    create_setting_label("Class:").pack(anchor="w", padx=40, pady=(20,5))
    class_entry = Entry(scrollable_frame, font=("Helvetica", 12), width=40)
    class_entry.insert(0, current_user[1])
    class_entry.pack(anchor="w", padx=40)

    def update_profile():
        new_name = name_entry.get()
        new_class = class_entry.get()
        if new_name and new_class:
            cursor.execute("UPDATE users SET name=?, class_name=? WHERE id=?", 
                         (new_name, new_class, user_id))
            conn.commit()
            messagebox.showinfo("Success", "Profile updated successfully!")
            show_settings_dashboard(user_id, new_name)

    create_button("Update Profile", update_profile).pack(anchor="w", padx=40, pady=20)

    # Account Settings Section
    create_section_header("Account Settings").pack(anchor="w", padx=40, pady=(30,20))

    # Change Password
    def change_password():
        change_window = Toplevel()
        change_window.title("Change Password")
        change_window.geometry("400x300")
        change_window.configure(bg=CARD_BG)

        Label(
            change_window,
            text="Change Password",
            font=("Helvetica", 16, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(pady=20)

        # Current password
        Label(
            change_window,
            text="Current Password:",
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(pady=(10,5))
        current_pass = Entry(change_window, show="*", font=("Helvetica", 12))
        current_pass.pack()

        # New password
        Label(
            change_window,
            text="New Password:",
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(pady=(10,5))
        new_pass = Entry(change_window, show="*", font=("Helvetica", 12))
        new_pass.pack()

        # Confirm new password
        Label(
            change_window,
            text="Confirm New Password:",
            font=("Helvetica", 12),
            bg=CARD_BG,
            fg=TEXT_COLOR
        ).pack(pady=(10,5))
        confirm_pass = Entry(change_window, show="*", font=("Helvetica", 12))
        confirm_pass.pack()

        def update_password():
            current = current_pass.get()
            new = new_pass.get()
            confirm = confirm_pass.get()

            # Verify current password
            cursor.execute("SELECT password FROM users WHERE id=?", (user_id,))
            stored_pass = cursor.fetchone()[0]

            if current != stored_pass:
                messagebox.showerror("Error", "Current password is incorrect!")
                return

            if new != confirm:
                messagebox.showerror("Error", "New passwords don't match!")
                return

            if len(new) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters long!")
                return

            cursor.execute("UPDATE users SET password=? WHERE id=?", (new, user_id))
            conn.commit()
            messagebox.showinfo("Success", "Password updated successfully!")
            change_window.destroy()

        Button(
            change_window,
            text="Update Password",
            command=update_password,
            font=("Helvetica", 12, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            relief=FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(pady=20)

    create_button("Change Password", change_password).pack(anchor="w", padx=40, pady=10)

    # Learning Preferences Section
    create_section_header("Learning Preferences").pack(anchor="w", padx=40, pady=(30,20))

    # Difficulty Level
    

