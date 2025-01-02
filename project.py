# Import required libraries
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tkinter import BOTH, FLAT, GROOVE, LEFT, RIDGE, RIGHT, VERTICAL, WORD, X, Y, Image, TclError, messagebox, END, SEL_FIRST, SEL_LAST, Tk, Frame, Label, Button, Text, Entry, Scrollbar, Canvas
from tensorflow.keras.utils import to_categorical
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

 

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
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

cursor.execute("INSERT OR IGNORE INTO admin (email, password) VALUES (?, ?)", ("Aditya123", "12345678*"))
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
    """
    Displays the admin dashboard with a list of registered users.
    """
    for widget in root.winfo_children():
        widget.destroy()

    Label(root, text="Admin Dashboard", font=("Arial", 24, "bold")).pack(pady=20)

    users = cursor.execute("SELECT id, name, surname, email, class_name FROM users").fetchall()
    Label(root, text="Registered Users", font=("Arial", 16)).pack(pady=10)

    for user in users:
        user_frame = Frame(root, bg="lightgray", padx=10, pady=10)
        user_frame.pack(pady=5, fill=X, padx=20)

        user_info = f"ID: {user[0]}, Name: {user[1]} {user[2]}, Email: {user[3]}, Class: {user[4]}"
        Label(user_frame, text=user_info, font=("Arial", 12), bg="lightgray", anchor="w").pack(side=LEFT, padx=10)

        Button(user_frame, text="View History",
               command=lambda u_id=user[0], u_name=f"{user[1]} {user[2]}": view_user_history(u_id, u_name),
               bg="green", fg="white", font=("Arial", 10)).pack(side=RIGHT, padx=5)

        Button(user_frame, text="Delete User", 
               command=lambda u_id=user[0]: delete_user(u_id),
               bg="red", fg="white", font=("Arial", 10)).pack(side=RIGHT, padx=5)

    Button(root, text="Back to Login", command=show_login, bg="blue", fg="white", font=("Arial", 14)).pack(pady=20)


def view_user_history(user_id, user_name):
    """
    Displays the history of a specific user for the admin.
    """
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

    # Questions and answers training 
    questions = [
        "what is a java",
        "what is the uses of java",
        "write a program of hello world",
        "what are the features of java",
        "what is the data types in java",
        "write a program of variables",
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
        "write a program of reverse number using java"
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
        1] Java is used for Mobile applications.
        2] Desktop applications.
        3] Web applications.
        4] Web servers.
        5] Application servers.
        6] Database connection, etc.
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
        1] Simple: Java is designed to be easy to learn.
        2] Secure: Java does not allocate direct pointers to memory, making it safe.
        3] Portable: Java is architecture-neutral and highly portable.
        4] Dynamic: Java can dynamically link class libraries and extend itself at runtime.
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
            public static void main(String args[]){
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
        
        1] Variable is used to store data .  
        2] variable is a containter to store data
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
            
            
           Example: // This is Single Line comment
           
           
           
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
        
          -  Documentation Section
          -  Package Declaration
          -  Import Statements
          -  Interface Section
          -  Class Definition
          -  Class Variables and Variables
          -  Main Method Class
          -  Methods and Behaviors
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

    def get_best_match(user_question, questions):
        vectorizer = TfidfVectorizer()
        question_vectors = vectorizer.fit_transform(questions)
        user_vector = vectorizer.transform([user_question])
        similarities = cosine_similarity(user_vector, question_vectors)
        best_match_index = similarities.argmax()
        return best_match_index, similarities[0, best_match_index]

    def ask_ai():
        user_question = question_entry.get().lower().strip()

        if not user_question or user_question == "type your question here...":
            messagebox.showerror("Error", "Please enter a question!")
            return

        try:
            user_tokens = tokenizer.texts_to_sequences([user_question])
            user_padded = pad_sequences(user_tokens, maxlen=max_length)
            prediction = model.predict(user_padded)
            answer_index = np.argmax(prediction)

            best_index, similarity_score = get_best_match(user_question, questions)
            if similarity_score > 0.5:
                answer = answers[best_index]
            elif answer_index < len(answers):
                answer = answers[answer_index]
            else:
                answer = "Sorry, I couldn't find a matching answer."

            chat_log.insert(END, f"You: {user_question}\n", "user")
            chat_log.insert(END, f"AI: {answer}\n", "ai")
            question_entry.delete(0, END)

            cursor.execute("INSERT INTO history (user_id, query) VALUES (?, ?)", (user_id, user_question))
            conn.commit()

        except Exception as e:
            print(f"Error during AI prediction: {e}")
            messagebox.showerror("Error", "An error occurred while processing your question.")
            
                
    def view_history():
        show_history_dashboard(user_id, user_name)

    # Function to delete all chat logs
    def clear_all():
        chat_log.delete(1.0, END)

    # Function to copy selected text
    def copy_text():
        try:
            root.clipboard_clear()
            root.clipboard_append(chat_log.get(SEL_FIRST, SEL_LAST))
            messagebox.showinfo("Copied", "Text copied to clipboard!")
        except TclError:
            messagebox.showerror("Error", "No text selected to copy!")

    # Sidebar
    sidebar = Frame(root, width=250, bg="yellow")
    sidebar.pack(side=LEFT, fill=Y)

    Button(sidebar, text="History", command=view_history, bg="blue", fg="white", font=("Arial", 12)).pack(pady=40)
    Button(sidebar, text="Log out", command=show_login, bg="green", fg="white", font=("Arial", 12)).pack(pady=40)

    # Main Area with black background
    main_area = Frame(root, bg="black")
    main_area.pack(side=RIGHT, fill=BOTH, expand=True)

    # Labels with white background for clear visibility
    Label(main_area, text=f"Welcome {user_name}", font=("Arial", 16, "bold"), fg="red").pack(pady=10)
    Label(main_area, text="Ask a question about Java!", font=("Arial", 12, "italic"), bg="black", fg="gray").pack(pady=20)

    # Answer height and width
    chat_log = Text(main_area, height=20, width=100, font=("Arial", 14), wrap=WORD, fg="white")
    chat_log.tag_config("user", foreground="blue")
    chat_log.tag_config("ai", foreground="green")
    chat_log.tag_config("history", foreground="purple")
    chat_log.pack(pady=10)

    # Entry field for question with hint behavior
    question_entry = Entry(main_area, width=50, font=("Arial", 14), fg="black", bg="white")
    question_entry.insert(0, "Type your question here...")  # Hint text
    question_entry.pack(pady=80)

    # Function to handle hint behavior
    def on_focus_in(event):
        if question_entry.get() == "Type your question here...":
            question_entry.delete(0, END)  # Remove hint text

    def on_focus_out(event):
        if question_entry.get() == "":
            question_entry.insert(0, "Type your question here...")  # Add hint text back

    # Bind events for focus in and out
    question_entry.bind("<FocusIn>", on_focus_in)
    question_entry.bind("<FocusOut>", on_focus_out)

    # Buttons
    button_frame = Frame(main_area, bg="black")
    button_frame.pack(pady=10)

    Button(button_frame, text=" 📩  Ask ", command=ask_ai, bg="lightgreen", font=("Arial", 12)).pack(side=LEFT, padx=40)
    Button(button_frame, text=" 📋  Copy", command=copy_text, bg="lightblue", font=("Arial", 12)).pack(side=LEFT, padx=40)
    Button(button_frame, text=" 🧹   Clean", command=clear_all, bg="white", font=("Arial", 12)).pack(side=LEFT, padx=40)

# Function to display the history dashboard
def show_history_dashboard(user_id, user_name):
    for widget in root.winfo_children():
        widget.destroy()

    # Fetch user history
    history = cursor.execute("SELECT id, query FROM history WHERE user_id = ?", (user_id,)).fetchall()

    # Sidebar
    sidebar = Frame(root, width=200, bg="lightgray")
    sidebar.pack(side=LEFT, fill=Y)

    Button(sidebar, text="Back", command=lambda: show_ai_dashboard(user_id, user_name), bg="blue", fg="white", font=("Arial", 12)).pack(pady=10)
    Button(sidebar, text="Delete All History", command=lambda: delete_all_history(user_id, user_name), bg="red", fg="white", font=("Arial", 12)).pack(pady=10)

    # Main Area
    main_area = Frame(root, bg="black")
    main_area.pack(side=RIGHT, fill=BOTH, expand=True)

    Label(main_area, text="History Dashboard", font=("Arial", 16, "bold"), fg="black").pack(pady=10)

    # Scrollable frame for history
    scroll_canvas = Canvas(main_area, bg="white")
    scroll_canvas.pack(side=LEFT, fill=BOTH, expand=True)

    scrollbar = Scrollbar(main_area, orient=VERTICAL, command=scroll_canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    scroll_canvas.configure(yscrollcommand=scrollbar.set)

    history_frame = Frame(scroll_canvas, bg="black")
    scroll_canvas.create_window((0, 0), window=history_frame, anchor="nw")

    for entry in history:
        entry_frame = Frame(history_frame, bg="white", pady=5)
        entry_frame.pack(fill=X)

        Label(entry_frame, text=entry[1], font=("Arial", 12), bg="white", anchor="w").pack(side=LEFT, padx=10, fill=X, expand=True)
        Button(entry_frame, text="Delete", command=lambda e_id=entry[0]: delete_history_item(user_id, user_name, e_id), bg="red", fg="white", font=("Arial", 10)).pack(side=RIGHT, padx=10)

    # Update scroll region
    history_frame.update_idletasks()
    scroll_canvas.config(scrollregion=scroll_canvas.bbox("all"))

# Function to delete a specific history item
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
