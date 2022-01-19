import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
  
 
LARGEFONT =("Verdana", 35)
  
class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("NHI Scraper")
        self.iconbitmap(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\icon.ico")
        self.resizable(width=False, height=False)
        self.geometry("500x300")
         
        # creating a container
        container = tk.Frame(self) 
        container.pack(side = "top", fill = "both", expand = True)
  
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
  
        # initializing frames to an empty array
        self.frames = {} 
  
        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage, Page1, Page2):
  
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
  
# first window frame startpage
  
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        # Logo
        logo = Image.open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\logo.png")
        logo = ImageTk.PhotoImage(logo)
        logo_label = ttk.Label(self, image=logo)
        logo_label.image = logo
        logo_label.grid(column=1, row=0, columnspan=3)
         
        # Instructions
        global instructions
        instructions = ttk.Label(self, text="Download Nursing Home Inspect's Raw data?", font=("Times", 15))
        instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Yes button
        browse_text = tk.StringVar()
        yes_btn = tk.Button(self, textvariable=browse_text, command=lambda:controller.show_frame(Page1), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("Yes")
        yes_btn.grid(column=1, row=2, pady=10)

        # No button
        browse_text = tk.StringVar()
        no_btn = tk.Button(self, textvariable=browse_text, command=lambda:controller.show_frame(Page2), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("No")
        no_btn.grid(column=3, row=2, pady=10)

        
  
  
          
  
  
# second window frame page1
class Page1(tk.Frame):
     
    def __init__(self, parent, controller):
         
        tk.Frame.__init__(self, parent)
        # Logo
        logo = Image.open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\logo.png")
        logo = ImageTk.PhotoImage(logo)
        logo_label = ttk.Label(self, image=logo)
        logo_label.image = logo
        logo_label.grid(column=1, row=0, columnspan=3)
         
        # Instructions
        global instructions
        instructions = ttk.Label(self, text="Choose folder to save to", font=("Times", 15))
        instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Download button
        browse_text = tk.StringVar()
        dl_btn = tk.Button(self, command=lambda:controller.show_frame(StartPage), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        dl_btn.grid(column=2, row=2, pady=10)
        browse_text.set("Browse")
  
  
  
  
# third window frame page2
class Page2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text ="Page 2", font = LARGEFONT)
        label.grid(row = 0, column = 4, padx = 10, pady = 10)
  
        # button to show frame 2 with text
        # layout2
        button1 = ttk.Button(self, text ="Page 1",
                            command = lambda : controller.show_frame(Page1))
     
        # putting the button in its place by
        # using grid
        button1.grid(row = 1, column = 1, padx = 10, pady = 10)
  
        # button to show frame 3 with text
        # layout3
        button2 = ttk.Button(self, text ="Startpage",
                            command = lambda : controller.show_frame(StartPage))
     
        # putting the button in its place by
        # using grid
        button2.grid(row = 2, column = 1, padx = 10, pady = 10)
  
  
# Driver Code
app = tkinterApp()
app.mainloop()