import tkinter as tk
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
from tkinter.ttk import Progressbar

root = tk.Tk()
root.title("NHI Scraper")
root.iconbitmap(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\icon.ico")
root.resizable(width=False, height=False)
root.geometry("500x300")

# Logo
logo = Image.open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\logo.png")
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0, columnspan=3)

# Instructions
instructions = tk.Label(root, text="Download Nursing Home Inspect's Raw data?", font=("Times", 15))
instructions.grid(column=1, row=1, columnspan=3, pady=10)

# Yes button
browse_text = tk.StringVar()
yes_btn = tk.Button(root, command=lambda:open_file(),textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
browse_text.set("Yes")
yes_btn.grid(column=1, row=2, pady=10)

# No button
browse_text = tk.StringVar()
no_btn = tk.Button(root, textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
browse_text.set("No")
no_btn.grid(column=3, row=2, pady=10)

# If yes is clicked
def open_file():
    dir = askdirectory()
    yes_btn.grid_forget()
    no_btn.grid_forget()
    instructions.config(text="Starting download")

    # Progress bar widget
    progress = Progressbar(root, orient = "horizontal",
                length = 200, mode = 'determinate')
    progress.grid(column=1, row=2, columnspan=3, pady=10)

# Progress bar function
def bar():
    pass




root.mainloop()