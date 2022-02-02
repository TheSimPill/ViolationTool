from optparse import Option
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import src.nhi_functions as nhi
import src.fine_scraper as scraper
import pickle, threading, os
from os.path import exists
 
LARGEFONT = ("Verdana", 35)
savepath = ""
filepath = ""
states_hash = {}
fines_hash = {}
partial_instructions = None
partial_instructions2 = None
dl_btn = None
load_scraper = False
  
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
        for F in (StartPage, DownloadPage, WebscrapingChoicePage, WebscrapingPage, OptionsPage):
  
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

    # Extend the display when we get to options page
    def resize(self):
        self.geometry("500x600")

# Default page layout
class PageLayout(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # Logo
        logo = Image.open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\logo.png")
        logo = ImageTk.PhotoImage(logo)
        logo_label = ttk.Label(self, image=logo)
        logo_label.image = logo
        logo_label.grid(column=1, row=0, columnspan=3)

# Startpage
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions
        start_instructions = ttk.Label(self, text="Reinitialize all data?", font=("Times", 15))
        start_instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Yes button
        browse_text = tk.StringVar()
        yes_btn = tk.Button(self, textvariable=browse_text, command=lambda:controller.show_frame(DownloadPage), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("Yes")
        yes_btn.grid(column=1, row=2, pady=10)

        # No button
        browse_text = tk.StringVar()
        no_btn = tk.Button(self, textvariable=browse_text, command=lambda:self.show_options(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("No")
        no_btn.grid(column=3, row=2, pady=10)

    # When no button is pressed, extend window and show options pags
    def show_options(self):
        self.controller.resize()
        self.controller.show_frame(OptionsPage)

# Download page
class DownloadPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller
         
        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Choose empty folder to save to and download will start", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Instructions line 2
        thisframe.instructions2 = ttk.Label(thisframe, text="MAKE SURE FOLDER IS EMPTY", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        # Download button
        browse_text = tk.StringVar()
        thisframe.dl_btn = tk.Button(thisframe, command=lambda:thisframe.download_and_parse(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        thisframe.dl_btn.grid(column=2, row=3, pady=10)
        browse_text.set("Browse")

    # Choose save location and start download
    def download_and_parse(thisframe):
        global filepath
        filepath = askdirectory()

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                self.func(thisframe, filepath)

        #thread(nhi.download).start()
        # For skipping download
        thisframe.advance_page()

    def advance_page(thisframe):
        global states_hash
        global filepath

        with open(filepath + "/hashes/states_hash.pkl", 'rb') as inp:
            states_hash = pickle.load(inp)
            
        thisframe.controller.show_frame(WebscrapingChoicePage)
            
# Webscraping choice page - shown after downloading raw data if yes is chosen on initial screen
class WebscrapingChoicePage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions
        instructions = ttk.Label(self, text="Do you have partial webscraping data to use?", font=("Times", 15))
        instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Instructions line 2
        instructions2 = ttk.Label(self, text="If yes, choose folder where partial save data resides", font=("Times", 15))
        instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        # Yes button
        browse_text = tk.StringVar()
        yes_btn = tk.Button(self, textvariable=browse_text, command=lambda:self.open_and_scrape(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("Yes")
        yes_btn.grid(column=1, row=3, pady=10)

        # No button
        browse_text = tk.StringVar()
        no_btn = tk.Button(self, textvariable=browse_text, command=lambda:self.fresh_scrape(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        browse_text.set("No")
        no_btn.grid(column=3, row=3, pady=10)

    # If yes is chosen -> Choose location of saved data, scrape will used saved pages when possible
    def open_and_scrape(self):
        global savepath
        global load_scraper
        load_scraper = True

        savepath = askdirectory()
        self.controller.show_frame(WebscrapingPage)
    
    # If no is chosen -> means a full scrape will be done
    def fresh_scrape(self):
        global filepath
        global savepath

        savepath = filepath + "/pages"
        if not exists(savepath):
            os.mkdir(savepath)
        
        self.controller.show_frame(WebscrapingPage)
        
# Webscraping page - shown if partial data choice is yes
class WebscrapingPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
        self.parent = parent
         
        # Instructions
        self.instructions = ttk.Label(self, text="Press start to begin webscraping", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Instructions line 2
        self.instructions2 = ttk.Label(self, text="Will take ~1hour if limited or no save data used", font=("Times", 15))
        self.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        # Start button
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:self.scrape(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        self.dl_btn.grid(column=2, row=3, pady=10)
        browse_text.set("Start Webscraping")

    def scrape(thisframe):
        global fines_hash
        global states_hash
        global load_scraper
        global savepath
        global filepath

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                if load_scraper:
                    self.func(thisframe, False, states_hash, savepath, filepath)
                else:
                    self.func(thisframe, True, states_hash, savepath, filepath)
        
        #thread(scraper.scrape_fines).start()
        thisframe.advance_page()

    # Called after scraper is done and fines have been matched
    def advance_page(thisframe):
        global fines_hash
        global filepath

        '''
        with open(filepath + "/hashes/fines_hash.pkl", 'rb') as inp:
            fines_hash = pickle.load(inp)
        '''
        thisframe.controller.resize()
        thisframe.controller.show_frame(OptionsPage)
        
    

        

# Shown if user didn't reinitialize data, or if reinitialization is complete
class OptionsPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Instructions
        self.instructions = ttk.Label(self, text="Press start to begin webscraping", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)


  
# Driver Code
app = tkinterApp()
app.mainloop()