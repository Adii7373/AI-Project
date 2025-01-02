import tkinter as tk
from tkinter import ttk

def main_app():
    # Create the main application window
    main_window = tk.Tk()
    main_window.title("Main Application")
    main_window.geometry("400x300")
    
    label = ttk.Label(main_window, text="Welcome to the Main Application!", font=("Arial", 16))
    label.pack(pady=50)
    
    main_window.mainloop()

def show_splash():
    # Create the splash screen window
    splash = tk.Tk()
    splash.title("Splash Screen")
    splash.geometry("300x200")
    splash.overrideredirect(True)  # Remove window decorations (title bar, etc.)
    
    # Add content to the splash screen
    splash_label = ttk.Label(splash, text="Loading...", font=("Arial", 16))
    splash_label.pack(expand=True)
    
    # Close the splash screen after 3 seconds
    splash.after(3000, lambda: [splash.destroy(), main_app()])
    splash.mainloop()

# Run the splash screen
show_splash()
