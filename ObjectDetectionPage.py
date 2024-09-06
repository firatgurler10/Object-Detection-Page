import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
from PIL import Image, ImageTk
import cv2
import pandas as pd
from ultralytics import YOLO
import cvzone
import serial
import time

# Global variables for OpenCV-related objects and flags
cap = None
is_camera_on = False
frame_count = 0
frame_skip_threshold = 3
model = None
video_paused = False
correct_username = "YOUR_USERNAME"
correct_password = "YOUR_PASSWORD"
ser = None

# Function to read coco.txt
def read_classes_from_file(file_path):
    with open(file_path, 'r') as file:
        classes = [line.strip() for line in file]
    return classes

# Function to start the webcam feed
def start_webcam():
    global cap, is_camera_on, video_paused
    if not is_camera_on:
        cap = cv2.VideoCapture(0)  # Use the default webcam (you can change the index if needed)
        is_camera_on = True
        video_paused = False
        update_canvas()  # Start updating the canvas

# Function to stop the webcam feed
def stop_webcam():
    global cap, is_camera_on, video_paused
    if cap is not None:
        cap.release()
        is_camera_on = False
        video_paused = False

# Function to update the Canvas with the webcam frame or video frame
def update_canvas():
    global is_camera_on, frame_count, video_paused, ser
    if is_camera_on:
        if not video_paused:
            ret, frame = cap.read()
            if ret:
                frame_count += 1
                if frame_count % frame_skip_threshold != 0:
                    canvas.after(10, update_canvas)
                    return

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (1020, 500))
                selected_class = class_selection.get()

                results = model.predict(frame)
                a = results[0].boxes.data
                px = pd.DataFrame(a.cpu().numpy()).astype("float")
                object_names = []
                for index, row in px.iterrows():
                    x1 = int(row[0])
                    y1 = int(row[1])
                    x2 = int(row[2])
                    y2 = int(row[3])
                    d = int(row[5])
                    if d < len(class_list):
                        c = class_list[d]
                        if selected_class == "All" or c == selected_class:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cvzone.putTextRect(frame, f'{c}', (x1, y1), 1, 1)
                            object_names.append(c)
                print(f"{object_names}, {frame_count} frame")
                photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                canvas.img = photo
                canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    
        canvas.after(10, update_canvas)

# Function to handle login
def handle_login():
    username = username_entry.get()
    password = password_entry.get()
    if username == correct_username and password == correct_password:
        root.deiconify()  # Make main window visible
        login_window.destroy()  # Close the login window
        start_webcam()
    else:
        messagebox.showerror("Error", "Wrong username or password!")

# Function to quit the application
def quit_app():
    stop_webcam()
    root.quit()
    root.destroy()

# Create the main Tkinter window
root = tk.Tk()
root.title("Object Detection Page")
root.withdraw()  # Hide main window

# Create a Notebook widget to contain different tabs
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Create tabs for different functionalities
tab1 = tk.Frame(notebook)
notebook.add(tab1, text="Object Detection")

# Load YOLO model
try:
    model = YOLO('yolov8s.pt')
except FileNotFoundError:
    messagebox.showerror("Error", "YOLO model file not found!")

# Read classes from coco.txt
class_list = read_classes_from_file('coco.txt')

# Create a frame to hold the main content (tab1)
content_frame = tk.Frame(tab1)
content_frame.pack(side = 'right', fill='both', expand=True)

# Create a label for the title
title_label = tk.Label(content_frame, text="Object Detection System", font=("Helvetica", 24))
title_label.pack(pady=20)

# Create a Canvas widget to display the webcam feed or video
canvas = tk.Canvas(content_frame, width=1020, height=500, bg='black')
canvas.pack()

# Set default class selection
class_selection = tk.StringVar()
class_selection.set("All")

# Create label for selecting class
class_selection_label = tk.Label(content_frame, text="Select Class:")
class_selection_label.pack(side='top', anchor = 'nw')
class_selection_entry = tk.OptionMenu(content_frame, class_selection, "All", *class_list)
class_selection_entry.pack(side='top', anchor = 'nw')

# Create a listbox for selecting class
class_selection_listbox = tk.Listbox(content_frame, selectmode=tk.SINGLE, width=20, height=10)
class_selection_listbox.pack(side='left', padx=5, fill=tk.Y)

# Populate the listbox with class options
for class_name in class_list:
    class_selection_listbox.insert(tk.END, class_name)

# Create a scrollbar for the listbox
class_scrollbar = tk.Scrollbar(content_frame, orient=tk.VERTICAL)
class_scrollbar.pack(side='top', anchor='nw')

# Configure the listbox to use the scrollbar
class_selection_listbox.config(yscrollcommand=class_scrollbar.set)
class_scrollbar.config(command=class_selection_listbox.yview)

# Function to handle selection from the listbox
def select_class():
    selected_index = class_selection_listbox.curselection()
    if selected_index:
        selected_class = class_selection_listbox.get(selected_index[0])
        class_selection.set(selected_class)

# Bind the listbox selection to the selection variable
class_selection_listbox.bind("<<ListboxSelect>>", lambda event: select_class())

# Create buttons for control
control_frame = tk.Frame(content_frame)
control_frame.pack()

play_button = tk.Button(control_frame, text="Play", command=start_webcam)
play_button.pack(side='left')

stop_button = tk.Button(control_frame, text="Stop", command=stop_webcam)
stop_button.pack(side='left')

quit_button = tk.Button(control_frame, text="Quit", command=quit_app)
quit_button.pack(side='right')

# Create a Toplevel widget for login
login_window = Toplevel(root)
login_window.title("Login")

# Create widgets for login tab (login_window)
login_label = tk.Label(login_window, text="Username:")
login_label.pack(pady=10)

username_entry = tk.Entry(login_window)
username_entry.pack(pady=5)

password_label = tk.Label(login_window, text="Password:")
password_label.pack(pady=10)

password_entry = tk.Entry(login_window, show="*")
password_entry.pack(pady=5)
login_button = tk.Button(login_window, text="Login", command=handle_login)
login_button.pack(pady=10)

# Start the Tkinter main loop
root.mainloop()
