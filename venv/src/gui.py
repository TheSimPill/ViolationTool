from email.mime import image
import tkinter as tk
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk


class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
         
        # creating a container
        container = tk.Frame(self) 
        container.pack(side = "top", fill = "both", expand = True)
  
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
  
        # initializing frames to an empty array
        self.frames = {} 
  
        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage):
  
            frame = F(container, self)
  
            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame
  
            frame.grid(row = 0, column = 0, sticky ="nsew")
  
        self.show_frame(StartPage)
  
    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()



class StartPage():
    root = tk.Tk()

    canvas = tk.Canvas(root, width=600, height=400)
    # Splits canvas into 3 identical invisible elements
    canvas.grid(columnspan=3, rowspan=3)

    # Logo
    logo = Image.open("../logo.png")
    logo = ImageTk.PhotoImage(logo)
    logo_label = tk.Label(image=logo)
    logo_label.image = logo
    logo_label.grid(column=1, row=0)

    # Instructions
    instructions = tk.Label(root, text="Choose path of folder to save required files to \nOR\n Choose path to required files from previous run", font="Times")
    instructions.grid(columnspan=3, column=0, row=1)

    def open_file():
        browse_text.set("loading...")
        dir = askdirectory()
        browse_text.set("Browse")

    # Browse button
    browse_text = tk.StringVar()
    browse_btn = tk.Button(root, command=lambda:open_file(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
    browse_text.set("Browse")
    browse_btn.grid(column=1, row=2)

    # Add margin under button
    canvas = tk.Canvas(root, width=600, height=250)
    canvas.grid(columnspan=3)

    root.mainloop()