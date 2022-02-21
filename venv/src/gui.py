import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import pickle, threading, os, time
from os.path import exists
import datetime
from platform import system

OS = system()
if OS == "Darwin":
    # Macbook
    import info as info
    import nhi_functions as nhi
    import fine_scraper as scraper
elif OS == "Windows":
    # Windows
    import src.nhi_functions as nhi
    import src.fine_scraper as scraper
    import src.info as info

# Global variables
LARGEFONT = ("Verdana", 35)
savepath = ""
filepath = ""
state_df = None
fines_hash = {}
partial_instructions = None
partial_instructions2 = None
dl_btn = None
load_scraper = False
nopath = False
east = []
west  = []
central = []
sdate = None
edate = None
eemails = []
wemails = []
cemails = []
userecent = False
options = None
  
class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("NHI Scraper")
        if OS == "Darwin":
            self.iconbitmap(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/icon.ico")
        elif OS == "Windows":
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
        for F in (StartPage, DownloadPage, WebscrapingChoicePage, WebscrapingPage,\
                  OptionsPage, NoPathPage, TerritoriesPage, DateRangePage, EmailsPage,\
                  FormatPage, ExcelPage, SendEmailsPage, TestPage):
  
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
        self.geometry("500x500")

    # Set back to start size
    def dresize(self):
        self.geometry("500x300")


# Default page layout
class PageLayout(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # Logo
        if OS == "Darwin":
            logo = Image.open(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/logo.png")
        elif OS == "Windows":
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
        global nopath; nopath = True
        self.controller.show_frame(NoPathPage)


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

        thread(nhi.download).start()
        # For skipping download
        #thisframe.advance_page()

    def advance_page(thisframe):
        global filepath

        with open(filepath + "/dataframes/state_df.pkl", 'rb') as inp:
            global state_df; state_df = pickle.load(inp)
            
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
        global load_scraper; load_scraper = True
        global savepath; savepath = askdirectory()

        self.controller.show_frame(WebscrapingPage)
    
    # If no is chosen -> means a full scrape will be done
    def fresh_scrape(self):
        global filepath
        global savepath
        
        savepath = "//Users//Freddie//Impruvon//guiwebscraperproject//venv//src//pages"
        ''' Doesnt work on mac rn
        savepath = filepath + "/pages"
        if not exists(savepath):
            os.mkdir(savepath)'''
        
        
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
        global state_df
        global load_scraper
        global savepath
        global filepath

        # For testing:
        with open(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/state_df.pkl", 'rb') as inp:
            state_df = pickle.load(inp)

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                if load_scraper:
                    self.func(thisframe, False, state_df, savepath, filepath)
                else:
                    self.func(thisframe, True, state_df, savepath, filepath)
        
        thread(scraper.scrape_fines).start()
        #thisframe.advance_page()

    # Called after scraper is done and fines have been matched
    def advance_page(thisframe):
        global filepath

        '''
        with open(filepath + "/hashes/fines_hash.pkl", 'rb') as inp:
            global fines_hash; fines_hash = pickle.load(inp)
        '''
        #thisframe.controller.resize()
        thisframe.controller.show_frame(OptionsPage)


# If no is selected, choose where the hashes are located
class NoPathPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller
         
        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Click browse to select locations of save data", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Download button
        browse_text = tk.StringVar()
        thisframe.dl_btn = tk.Button(thisframe, command=lambda:thisframe.choose_path(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        thisframe.dl_btn.grid(column=2, row=3, pady=10)
        browse_text.set("Browse")

    def choose_path(self):
        global savepath
        global state_df
        self.controller.resize()
        self.controller.show_frame(OptionsPage)
        '''
        while True:
            savepath = askdirectory()
            # Checks to see if user gave us path with hash we need, otherwise let them retry
            if exists(savepath + "/states_hash.pkl"):
                with open(savepath + "/states_hash.pkl", 'rb') as inp:
                    states_hash = pickle.load(inp)

                self.controller.resize()
                self.controller.update_idletasks()
                self.controller.show_frame(OptionsPage)
                break

            else:
                self.instructions.config(text="Folder chosen doesn't contain states_hash.pkl, try again")
                self.controller.update_idletasks()
                time.sleep(3)

        '''


# Shown if user didn't reinitialize data, or if reinitialization is complete
class OptionsPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Instructions
        self.instructions = ttk.Label(self, text="Choose your options", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # Set territories button
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:controller.show_frame(TerritoriesPage), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.dl_btn.grid(column=2, row=2, pady=10)
        browse_text.set("Set Territories")

        # Set date range button
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:self.show_daterange(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.dl_btn.grid(column=2, row=3, pady=10)
        browse_text.set("Set Date Range")

        # Set emails
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:controller.show_frame(EmailsPage), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.dl_btn.grid(column=2, row=4, pady=10)
        browse_text.set("Set Emails For Territories/States")

        # Format excel
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:self.show_format(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.dl_btn.grid(column=2, row=5, pady=10)
        browse_text.set("Format Excel Data")

        # Make excel files button
        browse_text = tk.StringVar()
        self.dl_btn = tk.Button(self, command=lambda:self.show_excel(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.dl_btn.grid(column=2, row=6, pady=10)
        browse_text.set("Make Excel Files and Send Emails ->")

    def show_daterange(thisframe):
        if OS == "Darwin":
            thisframe.controller.geometry("500x600")
        elif OS == "Windows":
            thisframe.controller.geometry("500x600")

        thisframe.controller.show_frame(DateRangePage)

    def show_format(thisframe):
        if OS == "Darwin":
            thisframe.controller.geometry("500x700")
        elif OS == "Windows":
            thisframe.controller.geometry("500x700")

        thisframe.controller.show_frame(FormatPage)

    def show_excel(thisframe):
        thisframe.controller.dresize()
        thisframe.controller.show_frame(ExcelPage)



# Page where states in each territory is set
class TerritoriesPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Lists to represent territories
        thisframe.east = []
        thisframe.west = []
        thisframe.central = []
        # Bools to determine if a territory has been set yet
        thisframe.eastc = False
        thisframe.westc = False
        thisframe.centralc = False
        # List of all states
        states = info.all_states

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Which territory do you want to set first?", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        # East Button
        browse_text = tk.StringVar()
        thisframe.eastbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("E", states, 0), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.eastbtn.grid(column=2, row=2, pady=20)
        browse_text.set("East")

        # Central button
        browse_text = tk.StringVar()
        thisframe.cenbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("C", states, 0), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.cenbtn.grid(column=2, row=3, pady=20)
        browse_text.set("Central")

        # West button
        browse_text = tk.StringVar()
        thisframe.wstbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("W", states, 0), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.wstbtn.grid(column=2, row=4, pady=20)
        browse_text.set("West")

    # Function for choosing states in territories
    def choose_terrs(thisframe, territory, states, chosen):

        # Custom checkbox - had to do this to get around problem with creating buttons in a loop
        class CheckB(ttk.Checkbutton):
            def __init__(self, parent, text):
                ttk.Checkbutton.__init__(self, master=parent, text=text, command=lambda:parent.add_state(text, territory, states))
                self.parent = thisframe
            
        # When we've chosen all 3 territories
        if chosen >= 3:
            thisframe.roptions()
        else:
            # Hide buttons
            thisframe.eastbtn.grid_forget()
            thisframe.cenbtn.grid_forget()
            thisframe.wstbtn.grid_forget()
            if OS == "Darwin":
                thisframe.controller.geometry("500x600")
            elif OS == "Windows":
                thisframe.controller.geometry("570x630")
     
            # Instructions
            if territory == "W":
                thisframe.instructions.config(text="Choose states in the west territory")
                thisframe.westc = True

                # East button
                browse_text = tk.StringVar()
                thisframe.cenbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("E", states, chosen+1), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
                thisframe.cenbtn.grid(column=2, row=25, pady=20)
                if chosen == 2:
                    browse_text.set("Finish")
                else:
                    browse_text.set("Set east territory")

            elif territory == "E":
                thisframe.instructions.config(text="Choose states in the east territory")
                thisframe.eastc = True

                # Central button
                browse_text = tk.StringVar()
                thisframe.cenbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("C", states, chosen+1), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
                thisframe.cenbtn.grid(column=2, row=25, pady=20)
                if chosen == 2:
                    browse_text.set("Finish")
                else:
                    browse_text.set("Set central territory")

            else:
                thisframe.instructions.config(text="Choose states in the central territory")
                thisframe.centralc = True

                # West button
                browse_text = tk.StringVar()
                thisframe.cenbtn = tk.Button(thisframe, command=lambda:thisframe.choose_terrs("W", states, chosen+1), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
                thisframe.cenbtn.grid(column=2, row=25, pady=20)
                if chosen == 2:
                    browse_text.set("Finish")
                else:
                    browse_text.set("Set west territory")     

            # Init checkboxes
            crow = 2
            ct = 0
            second = False
            third = False
            boxes = []
            for state in states:
                if ct <= len(states)/3:
                    boxes.append(CheckB(thisframe, state))
                    boxes[ct].grid(column=1, row=crow)
                elif ct <= (len(states)/3)*2:
                    # Init second column
                    if not second:
                        second = True
                        crow = 2
                    boxes.append(CheckB(thisframe, state))
                    boxes[ct].grid(column=2, row=crow)
                else:
                    # Init third column
                    if not third:
                        third = True
                        crow= 2
                    boxes.append(CheckB(thisframe, state))
                    boxes[ct].grid(column=3, row=crow)

                ct += 1
                crow += 1

            thisframe.controller.update_idletasks()

    # Called when a checkbox is clicked
    def add_state(thisframe, state, territory, states):
        # This handles states that have already been clicked
        if state in states:
            if territory == "W":
                thisframe.west.append(state)
                thisframe.west = sorted(thisframe.west)
            elif territory == "E":
                thisframe.east.append(state)
                thisframe.east = sorted(thisframe.east)
            else:
                thisframe.central.append(state)
                thisframe.central = sorted(thisframe.central)
        # If a state has been clicked and is unclicked
        else:
            if territory == "W":
                thisframe.west.remove(state)
            elif territory == "E":
                thisframe.east.remove(state)
            else:
                thisframe.central.remove(state)

    # Return to options page after territories have been allocated
    def roptions(thisframe):
        global east; east = thisframe.east
        global west; west = thisframe.west
        global central; central = thisframe.central

        thisframe.controller.resize()
        thisframe.controller.show_frame(OptionsPage)


# Page where date range for cases is set
class DateRangePage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller   

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Choose range of dates to include in excel file", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        # Instructions 2
        thisframe.instructions2 = ttk.Label(thisframe, text="Start date (MM/DD/YYYY)", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=3, columnspan=3, pady=10)

        # Instructions 3
        thisframe.instructions3 = ttk.Label(thisframe, text="End date (MM/DD/YYYY)", font=("Times", 15))
        thisframe.instructions3.grid(column=1, row=5, columnspan=3, pady=10)

        # Start date
        thisframe.start = tk.Text(thisframe, height=2, width=25)
        thisframe.start.grid(column=2, row=4, pady=10)

        # End date
        thisframe.end = tk.Text(thisframe, height=2, width=25)
        thisframe.end.grid(column=2, row=6, pady=10)

        # Finish button
        browse_text = tk.StringVar()
        thisframe.finbtn = tk.Button(thisframe, command=lambda:thisframe.check_range(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.finbtn.grid(column=2, row=7, pady=20)
        browse_text.set("Finish")

        # Instructions 4 -> need to save last run
        thisframe.instructions3 = ttk.Label(thisframe, text=".. or only include new data (Last run XX/XX/XXX)", font=("Times", 15))
        thisframe.instructions3.grid(column=1, row=8, columnspan=3, pady=10)

        # Use most recent data button
        browse_text = tk.StringVar()
        thisframe.finbtn = tk.Button(thisframe, command=lambda:thisframe.use_recent(), textvariable=browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.finbtn.grid(column=2, row=9, pady=20)
        browse_text.set("Use Recent")

    def use_recent(thisframe):
        global userecent; userecent = True
        thisframe.controller.show_frame(OptionsPage)

    # Checks to see if dates are in correct format and within range -> need to add earliest date
    def check_range(thisframe):
            try:
                stext = thisframe.start.get("1.0","end-1c")
                etext = thisframe.end.get("1.0","end-1c")
                stime = datetime.datetime.strptime(stext, '%m/%d/%Y')
                etime = datetime.datetime.strptime(etext, '%m/%d/%Y')

                # If user gives start date later than end date
                if stime > etime:
                    thisframe.instructions.config(text="Start date must be less than or equal to end date!")
                else:
                    global sdate; sdate = stime
                    global edate; edate = etime
                    thisframe.instructions.config(text="Dates set")
                    thisframe.update_idletasks()
                    time.sleep(2)
                    thisframe.controller.show_frame(OptionsPage)

            except:
                thisframe.instructions.config(text="Check date formats and retry")


# Page where emails for each territory are set
class EmailsPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Enter emails (each on their own line) for the east territory", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        # Instructions2
        thisframe.instructions2 = ttk.Label(thisframe, text="Please make sure the emails are typed correctly and valid", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=3, columnspan=3, pady=10)

        # Instructions3
        thisframe.instructions3 = ttk.Label(thisframe, text="Ex: justin@aol.com\n      ethan@gmail.com\n      ...", font=("Times", 15))
        thisframe.instructions3.grid(column=1, row=4, columnspan=3, pady=10)

        # Email box
        thisframe.box = scrolledtext.ScrolledText(thisframe, undo=True, width=40, height=5)
        thisframe.box.grid(column=2, row=5, pady=10)

        # Next territory button
        thisframe.browse_text = tk.StringVar()
        thisframe.nextbtn = tk.Button(thisframe, command=lambda:thisframe.advance_screen(), textvariable=thisframe.browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.nextbtn.grid(column=2, row=6, pady=40)
        thisframe.browse_text.set("Next Territory")

        # To represent what territory is being set
        thisframe.curter = "E"

    # Advance to next territory
    def advance_screen(thisframe):
        
        if thisframe.curter == "E":
            global eemails; eemails = thisframe.box.get("1.0","end-1c").splitlines()
            thisframe.curter = "C"
            thisframe.instructions.config(text="Enter emails (each on their own line) for the central territory")

        else:
            global cemails; cemails = thisframe.box.get("1.0","end-1c").splitlines()
            thisframe.curter = "W"
            thisframe.instructions.config(text="Enter emails (each on their own line) for the west territory")

            # Change button and command
            thisframe.browse_text = tk.StringVar()
            thisframe.nextbtn = tk.Button(thisframe, command=lambda:thisframe.finish(), textvariable=thisframe.browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
            thisframe.nextbtn.grid(column=2, row=6, pady=40)
            thisframe.browse_text.set("Finish")
        
        # Reset Email box
        thisframe.box = scrolledtext.ScrolledText(thisframe, undo=True, width=40, height=5)
        thisframe.box.grid(column=2, row=5, pady=10)

    def finish(thisframe):
        global wemails; wemails = thisframe.box.get("1.0","end-1c").splitlines()
        thisframe.controller.show_frame(OptionsPage)


# Page where emails for each territory are set
class FormatPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Choose which data to include", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        # Holds buttons
        thisframe.boxes = {"US Fines":False, "US Violations":False, \
                            "Top fined organizations per state":False, \
                            "Most severe organizations per state":False, "Sum of fines per state":False, \
                            "Sum of fines per state per year":False, "Sum of fined violations per state":False, \
                            "Sum of fined violations per state per year":False, "Most severe incidents per organization":False, \
                            "Incidents with highest fines per organization":False, "Create sheet with all territories combined":False}

        fm = ttk.Labelframe(thisframe, width=50, border=0)
        fm.grid(column=2, row=3)
        
        # Buttons
        b1 = tk.Checkbutton(fm, width=35, text="US Fines (Total and by year for dates in range)", anchor="w", command=lambda:thisframe.add_option("US Fines"))
        b1.grid()
        
        b1 = tk.Checkbutton(fm, width=35, text="US Violations (Total and by year for dates in range)", anchor="w", command=lambda:thisframe.add_option("US Violations"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Top fined organizations per state", width=35, anchor="w", command=lambda:thisframe.add_option("Top fined organizations per state"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Most severe organizations per state", width=35, anchor="w", command=lambda:thisframe.add_option("Most severe organizations per state"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Sum of fines per state", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of fines per state"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Sum of fines per state per year", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of fines per state per year"))
        b1.grid()
        
        b1 = tk.Checkbutton(fm, text="Sum of fined violations per state", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of fined violations per state"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Sum of fined violations per state per year", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of fined violations per state per year"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Most severe incidents per organization", width=35, anchor="w", command=lambda:thisframe.add_option("Most severe incidents per organization"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Incidents with highest fines per organization", width=35, anchor="w", command=lambda:thisframe.add_option("Incidents with highest fines per organization"))
        b1.grid()

        b1 = tk.Checkbutton(fm, text="Create sheet with all territories combined", width=35, anchor="w", command=lambda:thisframe.add_option("Create sheet with all territories combined"))
        b1.grid()

        # Finish button
        thisframe.browse_text = tk.StringVar()
        thisframe.nextbtn = tk.Button(thisframe, command=lambda:thisframe.finish(), textvariable=thisframe.browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.nextbtn.grid(column=2, row=4, pady=40)
        thisframe.browse_text.set("Finish")

    def finish(thisframe):
        global options; options = thisframe.boxes
        thisframe.controller.resize()
        thisframe.controller.show_frame(OptionsPage)

    # Add a chosen option to a list
    def add_option(thisframe, opt):
        thisframe.boxes[opt] = not thisframe.boxes[opt]
        
    
# Page where excel sheet is made
class ExcelPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Press button to make excel sheets with chosen options", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        # Start button -- command=lambda:nhi.summarize_data(states_hash, thisframe)
        # thisframe.finish()
        global state_df
        thisframe.browse_text = tk.StringVar()
        thisframe.nextbtn = tk.Button(thisframe, command=lambda:thisframe.make_sheets(), textvariable=thisframe.browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.nextbtn.grid(column=2, row=3, pady=40)
        thisframe.browse_text.set("Make Sheets")

    # Send territories that we chose to nhi functions to sort the violations
    def sort_terrs(thisframe):
        global state_df, east, central, west
        nhi.sort_by_territories(state_df, east, central, west)

    # Uses threads to make excel sheets -> need to first break data up by territory
    def make_sheets(thisframe):

        '''
        For testing:
        '''
        with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\state_df.pkl", 'rb') as inp:
            state_df = pickle.load(inp)

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                global options
                ts = [{"east": ["Maryland", "Virginia"], "west": ["Texas", "Alabama"]}]
                #; global sdate, edate, east, west, east
                sdate = datetime.datetime.strptime("01/01/2018", '%m/%d/%Y')
                edate = datetime.datetime.strptime("12/31/2021", '%m/%d/%Y')
                self.func(thisframe, "", options, state_df, sdate, edate, ts)

        thread(nhi.make_sheets).start()

    # Once sheet is made
    def finish(thisframe):
        time.sleep(1.5)
        thisframe.controller.show_frame(SendEmailsPage)


# Page where emails are sent
class SendEmailsPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Press button to send emails", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        # Send button
        thisframe.browse_text = tk.StringVar()
        thisframe.nextbtn = tk.Button(thisframe, command=lambda:thisframe.finish(), textvariable=thisframe.browse_text, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.nextbtn.grid(column=2, row=3, pady=40)
        thisframe.browse_text.set("Send Emails")
        

        # After emails are sent
    def finish(thisframe):
        thisframe.instructions.config(text="Emails Sent")
        thisframe.nextbtn.grid_forget()

class TestPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Press button to send emails", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        b1 = tk.Checkbutton(thisframe, text="Most severe incidents", width=35, anchor="w", command=lambda:thisframe.add_option("Most severe incidents per organization"))
        b1.grid(column=1, row=3, sticky="w")
        b1 = tk.Checkbutton(thisframe, text="Most severe incidents", width=35, anchor="w", command=lambda:thisframe.add_option("Most severe incidents per organization"))
        b1.grid(column=2, row=3, sticky="w")

        #fm = ttk.Labelframe(thisframe, width=50, border=0)
        #fm.grid(column=1, row=3)
        
        

    


# Driver Code
app = tkinterApp()
app.mainloop()
