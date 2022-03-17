from re import T
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import pickle, threading, os, time, sys
from os.path import exists
import datetime
from platform import system

OS = system()
if OS == "Darwin":
    # Macbook
    import info as info
    import nhi_functions as nhi
    import scraper as scraper

    
    with open(nhi.resource_path("dataframes/tag_hash.pkl"), 'rb') as inp:
        tag_hash = pickle.load(inp)

elif OS == "Windows":
    # Windows
    import src.nhi_functions as nhi
    import src.scraper as scraper
    import src.info as info
    import src.strip_pdf as spdf
    

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
sdate = None
edate = None
userecent = False
options = None
territories = {}
chosen_tags = []
apikey = ""



  
class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("NHI Scraper")
        if OS == "Darwin":
            #self.iconbitmap(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/icon.ico")
            self.iconbitmap(nhi.resource_path("icon.ico"))
        elif OS == "Windows":
            self.iconbitmap(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\icon.ico")
        
        # Prevents user from stretching screen
        self.resizable(width=False, height=False)
        self.geometry("500x300")
         
        # creating a container
        self.container = tk.Frame(self) 
        self.container.pack(side = "top", fill = "both", expand = True)
  
        self.container.grid_rowconfigure(0, weight = 1)
        self.container.grid_columnconfigure(0, weight = 1)
  
        # initializing frames to an empty dict so that we can access pages by their name
        self.frames = {} 
  
        self.add_frames([StartPage, DownloadPage, WebscrapingChoicePage, WebscrapingPage,\
                  OptionsPage, NoPathPage, TerritoriesPage, DateRangePage,\
                  FormatPage, TagsPage, ExcelPage, TestPage, KeyPage])

        self.show_frame(NoPathPage)
  
    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()        

    # Add a frame to the dict of pages 
    def add_frames(self, frames):
        for F in frames:
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row = 0, column = 0, sticky ="nsew")

    # Set back to start size
    def dresize(self):
        self.geometry("500x300")

    # Window size for options page
    def resize_optionspage(self):
        if OS == "Darwin":
            self.geometry("500x500")
        elif OS == "Windows":
            self.geometry("500x600")


# Default page layout
class PageLayout(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # Logo
        if OS == "Darwin":
            #logo = Image.open(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/logo.png")
            logo = Image.open(nhi.resource_path("logo.png"))
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
         
        # Instructions, Yes and No buttons
        start_instructions = ttk.Label(self, text="Reinitialize all data?", font=("Times", 15))
        start_instructions.grid(column=1, row=1, columnspan=3, pady=10)

        yes_btn = tk.Button(self, text="Yes", command=lambda:controller.show_frame(DownloadPage), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        yes_btn.grid(column=1, row=2, pady=10)

        no_btn = tk.Button(self, text="No", command=lambda:self.show_options(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
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
         
        # Instructions and Download button
        thisframe.instructions = ttk.Label(thisframe, text="Choose empty folder to save to and download will start", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        thisframe.instructions2 = ttk.Label(thisframe, text="MAKE SURE FOLDER IS EMPTY", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        thisframe.dl_btn = tk.Button(thisframe, text="Browse", command=lambda:thisframe.download_and_parse(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        thisframe.dl_btn.grid(column=2, row=3, pady=10)

    # Choose save location and start download
    def download_and_parse(thisframe):
        global filepath; filepath = askdirectory()

        # Create a custom thread class so that we can update the screen during download
        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                self.func(thisframe, filepath)

        thread(nhi.download).start()
        # For skipping download
        #thisframe.advance_page()

    # Called after excel sheets are parsed and made into state_df
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
         
        # Instructions, Yes and No buttons
        instructions = ttk.Label(self, text="Do you have partial webscraping data to use?", font=("Times", 15))
        instructions.grid(column=1, row=1, columnspan=3, pady=10)

        instructions2 = ttk.Label(self, text="If yes, choose folder where partial save data resides", font=("Times", 15))
        instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        yes_btn = tk.Button(self, text="Yes", command=lambda:self.open_and_scrape(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        yes_btn.grid(column=1, row=3, pady=10)

        no_btn = tk.Button(self, text="No", command=lambda:self.fresh_scrape(), font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        no_btn.grid(column=3, row=3, pady=10)


    # If yes is chosen -> Choose location of saved data, scrape will use saved pages when possible
    def open_and_scrape(self):
        global load_scraper; load_scraper = True
        global savepath; savepath = askdirectory()

        self.controller.show_frame(KeyPage)
    
    # If no is chosen -> means a full scrape will be done
    def fresh_scrape(self):
        global filepath, savepath
        
        #savepath = "//Users//Freddie//Impruvon//guiwebscraperproject//venv//src//pages"
        savepath = r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\rawdata\pages"
        ''' Doesnt work on mac rn
        savepath = filepath + "/pages"
        '''
        if not exists(savepath):
            os.mkdir(savepath)
        
        self.controller.show_frame(KeyPage)

# Page to enter API key before scrape starts
class KeyPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions, Text box and Start button
        self.instructions = ttk.Label(self, text="Enter key for WebScrapingApi.com below", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        self.box = scrolledtext.ScrolledText(self, undo=True, width=40, height=1)
        self.box.grid(column=2, row=2, pady=1)

        self.start_btn = tk.Button(self, command=lambda:self.save_key(), text="Next", font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        self.start_btn.grid(column=2, row=3, pady=3)

    # Save the api key and advance screen
    def save_key(thisframe):
        global apikey; apikey = thisframe.box.get("1.0","end-1c")
        thisframe.controller.show_frame(WebscrapingPage)


# Webscraping page 
class WebscrapingPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions and Start button
        self.instructions = ttk.Label(self, text="Press start to begin webscraping", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        self.instructions2 = ttk.Label(self, text="Will take ~1hour if limited or no save data used", font=("Times", 15))
        self.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        self.start_btn = tk.Button(self, command=lambda:self.scrape(), text="Start Webscraping", font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        self.start_btn.grid(column=2, row=3, pady=10)
    

    def scrape(thisframe):
        global fines_hash, state_df, load_scraper, savepath, filepath, apikey
        # On windows for testing
        filepath = r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src"

        # For testing:
        # MAC
        #with open(r"/Users/Freddie/Impruvon/guiwebscraperproject/venv/src/dataframes/state_df.pkl", 'rb') as inp:
        #   state_df = pickle.load(inp)
        #with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\state_df.pkl", 'rb') as inp:
         #   state_df = pickle.load(inp)

        # For real run
        with open(r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\rawdata\dataframes\state_df.pkl", 'rb') as inp:
            state_df = pickle.load(inp)

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                if load_scraper:
                    self.func(thisframe, False, state_df, savepath, filepath, apikey)
                else:
                    self.func(thisframe, True, state_df, savepath, filepath, apikey)
        
        thread(scraper.scrape_fines).start()
        #thisframe.advance_page()

    # Called after scraper is done and fines have been matched
    def advance_page(thisframe):
        global filepath

        '''
        with open(filepath + "/hashes/fines_hash.pkl", 'rb') as inp:
            global fines_hash; fines_hash = pickle.load(inp)
        '''
        thisframe.controller.resize_optionspage()
        thisframe.controller.show_frame(OptionsPage)


# If no is selected, choose where the dataframes are located
class NoPathPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions and Download button
        self.instructions = ttk.Label(self, text="Welcome!", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        #self.instructions2 = ttk.Label(self, text="Click browse to select locations of save data", font=("Times", 15))
        #self.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        self.dl_btn = tk.Button(self, command=lambda:self.choose_path(), text="Start", font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        self.dl_btn.grid(column=2, row=3, pady=10)


    def choose_path(self):
        global savepath, state_df
        self.controller.resize_optionspage()
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

        # Instructions, Buttons for options
        option_count = 1
        self.instructions = ttk.Label(self, text="Choose your options", font=("Times", 15))
        self.instructions.grid(column=1, row=option_count, columnspan=3, pady=15)
        option_count += 1 

        self.instructions2 = ttk.Label(self, text="You will only be able to choose each once!", font=("Times", 15))
        self.instructions2.grid(column=1, row=option_count, columnspan=3)
        option_count += 1 

        self.terr_btn = tk.Button(self, command=lambda:self.show_territories(), text="Set Territories", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.terr_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.date_btn = tk.Button(self, command=lambda:self.show_daterange(), text="Set Date Range", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.date_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.excel_btn = tk.Button(self, command=lambda:self.show_format(), text="Format Excel Data", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.excel_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.tag_btn = tk.Button(self, command=lambda:self.show_tags(), text="Choose Tags to Include", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.tag_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.make_btn = tk.Button(self, command=lambda:self.show_excel(), text="Make Excel Files and Set/Send Emails ->", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.make_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

    # Functions to show appropriate screens and disable buttons after press

    def show_territories(self):
        self.terr_btn.config(text="", command=())
        self.controller.show_frame(TerritoriesPage)

    def show_daterange(self):
        if OS == "Darwin":
            self.controller.geometry("500x600")
        elif OS == "Windows":
            self.controller.geometry("500x600")

        self.date_btn.config(text="", command=())
        self.controller.show_frame(DateRangePage)

    def show_format(self):
        if OS == "Darwin":
            self.controller.geometry("500x600")
        elif OS == "Windows":
            self.controller.geometry("500x600")

        self.excel_btn.config(text="", command=())
        self.controller.show_frame(FormatPage)

    def show_tags(self):
        self.tag_btn.config(text="", command=())
        self.controller.show_frame(TagsPage)

    def show_excel(self):
        self.controller.dresize()
        self.controller.show_frame(ExcelPage)


# Page where states in each territory is set
class TerritoriesPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Instructions, Territory box and Next button 
        self.instructions = ttk.Label(self, text="Enter territory names, each on their own line", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        self.instructions2 = ttk.Label(self, text="", font=("Times", 15))
        self.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        self.box = scrolledtext.ScrolledText(self, undo=True, width=40, height=10)
        self.box.grid(column=2, row=3, pady=10)

        self.nextbtn = tk.Button(self, command=lambda:self.set_terr(), text="Next", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.nextbtn.grid(column=2, row=4, pady=30)

        # Used for populating territories
        self.count = 0 


    # Lets the user add territories
    def set_terr(self):
        lines = self.box.get("1.0","end-1c").splitlines()
        lines = [x for x in lines if x != '']
        if len(lines) != 0:
            # Makes dict to hold territories and their states
            global territories; territories = {key: [] for key in lines}
            self.tlist = lines

            # Update screen
            self.add_states()
    
        else:
            self.instructions.config(text="Please enter at least one territory")

    # Lets the user add states
    def add_states(self):
        global territories
        bad = False
        self.instructions2.config(text="Use full state names, with first letter capitalized".format(self.tlist[0]))
        # First territory
        if self.count == 0:
            self.instructions.config(text="Enter states in {} territory, each on their own line".format(self.tlist[0]))
            self.nextbtn.config(command=lambda:self.add_states())

            # If there's only one territory
            if len(self.tlist) == 1:
                self.nextbtn.config(text="Finish")

        elif self.count > 0:
            # Grab states from box
            states = self.box.get("1.0","end-1c").splitlines()
            states = [x.strip() for x in states if x != '']

            # Make sure valid states were given
            for state in states:
                if state not in info.all_states:
                    self.instructions.config(text="Please make sure states are spelled correctly and valid")
                    self.instructions2.grid_forget()
                    bad = True

            # Only continue if valid input was given
            if not bad:
                # Update territory hash
                terr = self.tlist[self.count-1]
                territories[terr] = states
                # Update screen
                if self.count < len(self.tlist):
                    terr = self.tlist[self.count]
                    self.instructions.config(text="Enter states in {} territory, each on their own line".format(terr))
                # Updates the button
                if self.count == len(self.tlist) - 1:
                    self.nextbtn.config(text="Finish")
                # Last screen
                elif self.count == len(self.tlist):
                    self.controller.show_frame(OptionsPage)

        # Clear the box
        if not bad:
            self.box.delete("1.0", "end")
            self.count += 1


# Page where date range for cases is set
class DateRangePage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller   

        # Instructions, Dates, Buttons
        self.instructions = ttk.Label(self, text="Choose range of dates to include in excel file", font=("Times", 15))
        self.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        self.instructions2 = ttk.Label(self, text="Start date (MM/DD/YYYY)", font=("Times", 15))
        self.instructions2.grid(column=1, row=3, columnspan=3, pady=10)

        self.instructions3 = ttk.Label(self, text="End date (MM/DD/YYYY)", font=("Times", 15))
        self.instructions3.grid(column=1, row=5, columnspan=3, pady=10)

        self.start = tk.Text(self, height=2, width=25)
        self.start.grid(column=2, row=4, pady=10)

        self.end = tk.Text(self, height=2, width=25)
        self.end.grid(column=2, row=6, pady=10)

        self.fin_btn = tk.Button(self, command=lambda:self.check_range(), text="Finish", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.fin_btn.grid(column=2, row=7, pady=20)
       
        self.instructions4 = ttk.Label(self, text=".. or only include new data (Last run XX/XX/XXX)", font=("Times", 15))
        self.instructions4.grid(column=1, row=8, columnspan=3, pady=10)

        self.rec_btn = tk.Button(self, command=lambda:self.use_recent(), text="Use Recent", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.rec_btn.grid(column=2, row=9, pady=20)
       

    def use_recent(self):
        global userecent; userecent = True
        self.controller.show_frame(OptionsPage)

    # Checks to see if dates are in correct format and within range -> need to add earliest date
    def check_range(self):
            try:
                stext = self.start.get("1.0","end-1c")
                etext = self.end.get("1.0","end-1c")
                stime = datetime.datetime.strptime(stext, '%m/%d/%Y')
                etime = datetime.datetime.strptime(etext, '%m/%d/%Y')

                # If user gives start date later than end date
                if stime > etime:
                    self.instructions.config(text="Start date must be less than or equal to end date!")
                else:
                    global sdate; sdate = stime
                    global edate; edate = etime
                    self.controller.show_frame(OptionsPage)

            except:
                self.instructions.config(text="Check date formats and retry")


# Format excel sheets
class FormatPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions
        thisframe.instructions = ttk.Label(thisframe, text="Choose which data to include", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)\
        
        thisframe.instructions2 = ttk.Label(thisframe, text="Will include dates in range or default if none selected", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=3, columnspan=3, pady=10)

        # Holds buttons
        thisframe.options = {"US Fines":False, "US Violations":False, \
                            "Top fined organizations per state":False, "Most severe organizations per state":False, \
                            "Sum of fines per state per year":False, "Sum of violations per state per year":False,\
                            "Create sheet with all territories combined":False, "All Violations":False}

        # Frame to hold the buttons and list to access them directly
        fm = ttk.Labelframe(thisframe, width=50, border=0)
        fm.grid(column=2, row=4)
        thisframe.boxes = []
        i = 0
        
        # Buttons
        thisframe.boxes.append(tk.Checkbutton(fm, width=35, text="US Fines (Total, yearly)", anchor="w", command=lambda:thisframe.add_option("US Fines")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, width=35, text="US Violations (Total, yearly)", anchor="w", command=lambda:thisframe.add_option("US Violations")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Top fined organizations (Total, yearly)", width=35, anchor="w", command=lambda:thisframe.add_option("Top fined organizations per state")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Most severe organizations (Total, yearly)", width=35, anchor="w", command=lambda:thisframe.add_option("Most severe organizations per state")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Sum of fines per state (Total, yearly)", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of fines per state per year")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Sum of violations per state (Total, yearly)", width=35, anchor="w", command=lambda:thisframe.add_option("Sum of violations per state per year")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Create sheet with all territories combined", width=35, anchor="w", command=lambda:thisframe.add_option("Create sheet with all territories combined")))
        thisframe.boxes[i].grid()
        i += 1

        thisframe.boxes.append(tk.Checkbutton(fm, text="Create sheet for all violations without territories", width=35, anchor="w", command=lambda:thisframe.add_option("All Violations")))
        thisframe.boxes[i].grid()
        i += 1

        # Butttons
        thisframe.all_btn = tk.Button(thisframe, command=lambda:thisframe.select_all(), text="Select All", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.all_btn.grid(column=2, row=5, pady=15)
        thisframe.all = False

        thisframe.fin_btn = tk.Button(thisframe, command=lambda:thisframe.finish(), text="Finish", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.fin_btn.grid(column=2, row=6, pady=5)
        

    # Once user is done selecting options
    def finish(thisframe):
        global options; options = thisframe.options
        thisframe.controller.resize_optionspage()
        thisframe.controller.show_frame(OptionsPage)

    # Add a chosen option to a list
    def add_option(thisframe, opt):
        thisframe.options[opt] = not thisframe.options[opt]

    # Select all button functionality
    def select_all(thisframe):
        if thisframe.all:    
            thisframe.options = {k: False for k, _ in thisframe.options.items()}
            for box in thisframe.boxes:
                box.deselect()   
            thisframe.all = False
            thisframe.all_btn.config(text="Select All")   
        else:         
            thisframe.options = {k: True for k, _ in thisframe.options.items()}
            for box in thisframe.boxes:
                box.select()
            thisframe.all = True
            thisframe.all_btn.config(text="Unselect All")   


# Choose which tags to include
class TagsPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Instructions, Tags box, buttons
        self.instructions = ttk.Label(self, text="Enter tags to include in excel sheets, each on their own line", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        self.instructions2 = ttk.Label(self, text="Only include last 3 numbers (ex: F757 -> 757)", font=("Times", 15))
        self.instructions2.grid(column=1, row=2, columnspan=3, pady=10)

        self.box = scrolledtext.ScrolledText(self, undo=True, width=40, height=10)
        self.box.grid(column=2, row=3, pady=10)

        self.all_btn = tk.Button(self, command=lambda:self.set_all_tags(), text="Include All Tags", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.all_btn.grid(column=2, row=4, pady=15)

        self.fin_btn = tk.Button(self, command=lambda:self.set_tags(), text="Finish", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.fin_btn.grid(column=2, row=5, pady=10)


    # Lets the user add the tags
    def set_tags(self):
        notags = True
        lines = self.box.get("1.0","end-1c").splitlines()
        lines = [x.strip() for x in lines if x != '']
        if len(lines) != 0:
            # List to hold the tags
            global chosen_tags
            for tag in lines:
                newtag = '0' + tag
                
                if newtag in tag_hash.keys():
                    chosen_tags += [newtag]
                    notags = False
            
        if notags:
            self.instructions.config(text="Please enter at least one valid tag")
            self.instructions2.grid_forget()
        else:
            self.controller.show_frame(OptionsPage)
    
    # For setting all tags
    def set_all_tags(self):
        global chosen_tags; chosen_tags = list(tag_hash.keys())
        self.controller.show_frame(OptionsPage)


# Page where excel sheet is made
class ExcelPage(tk.Frame):
    def __init__(thisframe, parent, controller):
        PageLayout.__init__(thisframe, parent)
        thisframe.controller = controller

        # Instructions and Make sheets button
        thisframe.instructions = ttk.Label(thisframe, text="Press button to choose where to save excel sheets", font=("Times", 15))
        thisframe.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        thisframe.instructions2 = ttk.Label(thisframe, text="Sheet creation will start", font=("Times", 15))
        thisframe.instructions2.grid(column=1, row=3, columnspan=3, pady=10)
    
        thisframe.sheet_btn = tk.Button(thisframe, command=lambda:thisframe.make_sheets(), text="Make Sheets", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        thisframe.sheet_btn.grid(column=2, row=4, pady=40)
        

    # Uses threads to make excel sheets -> need to first break data up by territory
    def make_sheets(thisframe):

        outpath = askdirectory()

        '''
        For testing:
        '''
        if OS == "Darwin":
            with open(nhi.resource_path("dataframes/state_df.pkl"), 'rb') as inp:
                state_df = pickle.load(inp)
        else:
            path = r"C:\Users\FreddieG3\Documents\Job\Impruvon\Web Scraper Project GUI\venv\src\dataframes\state_df.pkl"

        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                global options, sdate, edate, territories, chosen_tags

                self.func(thisframe, "", options, state_df, sdate, edate, territories, chosen_tags, outpath)

        thread(nhi.make_sheets).start()

    # Once sheet is made
    def finish(thisframe, terrs):
        # This line is in case the user never set territories but called to make sheets
        global territories; territories = terrs

        time.sleep(1.5)
        thisframe.controller.resize_optionspage()
        thisframe.controller.add_frames([EmailsPage])
        thisframe.controller.show_frame(EmailsPage)


# Page where emails for each territory are set
class EmailsPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Will be used to iterate through territories
        global territories
        self.terr_names = list(territories.keys())
        
        self.terr_emails = {}

        # Instructions, Email box, Next/Finish button
        self.instructions = ttk.Label(self, text="Enter emails (each on their own line) for the {} territory".format(self.terr_names[0]), font=("Times", 15))
        self.instructions.grid(column=1, row=2, columnspan=3, pady=10)

        self.instructions2 = ttk.Label(self, text="Please make sure the emails are typed correctly and valid", font=("Times", 15))
        self.instructions2.grid(column=1, row=3, columnspan=3, pady=10)

        self.instructions3 = ttk.Label(self, text="Ex: justin@aol.com\n      ethan@gmail.com\n      ...", font=("Times", 15))
        self.instructions3.grid(column=1, row=4, columnspan=3, pady=10)

        self.box = scrolledtext.ScrolledText(self, undo=True, width=40, height=5)
        self.box.grid(column=2, row=5, pady=10)
        
        # What the button will say to start
        if len(self.terr_names) == 1:
            textfield = "Send Emails"
        else:
            textfield = "Next Territory"

        self.nextbtn = tk.Button(self, command=lambda:self.add_emails(), text=textfield, font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.nextbtn.grid(column=2, row=6, pady=40)
        
        # For counting which territory we're on
        self.count = 1
        
     # Lets the user add states
    def add_emails(self):
            
        if self.count > 0:
            # Grab states from box
            emails = self.box.get("1.0","end-1c").splitlines()
            emails = [x.strip() for x in emails if x != '']
            # Update territory email hash
            terr = self.terr_names[self.count-1]
            self.terr_emails[terr] = emails
            # Update screen
            if self.count < len(self.terr_names):
                terr = self.terr_names[self.count]
                self.instructions.config(text="Enter emails (each on their own line) for the {} territory".format(terr))
            # Updates the button
            if self.count == len(self.terr_names) - 1:
                self.nextbtn.config(text="Send Emails")
            # Last screen
            elif self.count == len(self.terr_names):
                self.controller.show_frame(OptionsPage)
                print(self.terr_emails)
                nhi.send_emails(self, self.terr_emails)

        # Clear the box
        self.box.delete("1.0", "end")
        self.count += 1


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
        
        

    

if __name__ == '__main__':
    # Driver Code
    app = tkinterApp()
    app.mainloop()
