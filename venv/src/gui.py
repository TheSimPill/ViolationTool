import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import pickle, threading, datetime, info
import nhi_functions as nhi
    
# Global variables
state_df = None
sdate = None
edate = None
options = None
territories = {}
chosen_tags = []

# Contains tags and their descriptions
with open(nhi.resource_path("dataframes/tag_hash.pkl"), 'rb') as inp:
    tag_hash = pickle.load(inp)

  
class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("NHI Scraper")
        self.iconbitmap(nhi.resource_path("images/icon.ico"))
    
        # Prevents user from stretching screen
        self.resizable(width=False, height=False)
        self.geometry("500x300")
         
        # creating a container
        self.container = tk.Frame(self) 
        self.container.pack(side = "top", fill = "both", expand = True)
  
        self.container.grid_rowconfigure(0, weight = 1)
        self.container.grid_columnconfigure(0, weight = 1)
  
        # Initializing frames to an empty dict so that we can access pages by their name
        self.frames = {} 
  
        self.add_frames([OptionsPage, StartPage, TerritoriesPage, DateRangePage,\
                  FormatPage, TagsPage, ExcelPage, DonePage])

        self.show_frame(StartPage)
  
    # Shows frame that was passed in as a parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()        

    # Add a frame to the dict of pages 
    def add_frames(self, frames):
        for F in frames:
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row = 0, column = 0, sticky ="nsew")

    # Window size for options page
    def resize_optionspage(self):
        self.geometry("500x500")
        

# Default page layout
class PageLayout(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # Logo
        logo = Image.open(nhi.resource_path("images/logo.png"))
        logo = ImageTk.PhotoImage(logo)
        logo_label = ttk.Label(self, image=logo)
        logo_label.image = logo
        logo_label.grid(column=1, row=0, columnspan=3)

# Start Page
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller
         
        # Instructions and Download button
        self.instructions = ttk.Label(self, text="Welcome!", font=("Times", 15))
        self.instructions.grid(column=1, row=1, columnspan=3, pady=10)

        self.dl_btn = tk.Button(self, command=lambda:self.show_options(), text="Start", font="Times", bg="#000099", fg="#00ace6", height=2, width=15)
        self.dl_btn.grid(column=2, row=3, pady=10)

    def show_options(self):
        self.controller.resize_optionspage()
        self.controller.show_frame(OptionsPage)
             

# Shows users options for the dataset
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

        self.tag_btn = tk.Button(self, command=lambda:self.show_tags(), text="Choose Tags to Include", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.tag_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.excel_btn = tk.Button(self, command=lambda:self.show_format(), text="Format Excel Data", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.excel_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

        self.make_btn = tk.Button(self, command=lambda:self.show_excel(), text="Make Excel Files and Set/Send Emails ->", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.make_btn.grid(column=2, row=option_count, pady=15)
        option_count += 1 

    # Functions to show appropriate screens and disable buttons after press

    def show_territories(self):
        self.terr_btn.config(text="", command=())
        self.controller.show_frame(TerritoriesPage)

    def show_daterange(self):     
        self.controller.geometry("500x600")
        self.date_btn.config(text="", command=())
        self.controller.show_frame(DateRangePage)
    
    def show_tags(self):
        self.tag_btn.config(text="", command=())
        self.controller.show_frame(TagsPage)

    def show_format(self):
        self.controller.geometry("500x600")
        self.excel_btn.config(text="", command=())
        self.controller.show_frame(FormatPage)

    def show_excel(self):
        self.controller.geometry("500x300")
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
       
        self.instructions4 = ttk.Label(self, text=".. or use all dates in the dataset", font=("Times", 15))
        self.instructions4.grid(column=1, row=8, columnspan=3, pady=10)

        self.rec_btn = tk.Button(self, command=lambda:controller.show_frame(OptionsPage), text="All Dates", font="Times", bg="#000099", fg="#00ace6", height=1, width=30)
        self.rec_btn.grid(column=2, row=9, pady=20)
       

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
        rejected_tags = []
        if len(lines) != 0:
            # List to hold the tags
            global chosen_tags
            for tag in lines:        
                if tag in tag_hash.keys():
                    chosen_tags += [tag]
                    notags = False
                else:
                    rejected_tags += [tag]
                
        
        if notags:
            self.instructions.config(text="Please enter at least one valid tag")
            self.instructions2.grid_forget()
        else:
            # Display rejected tags if any 
            if len(rejected_tags) != 0:
                self.box.grid_forget()
                self.all_btn.grid_forget()
                self.fin_btn.grid_forget()
                self.instructions2.grid_forget()
                self.instructions.config(text="Rejected " + rejected_tags)

            self.controller.show_frame(OptionsPage)
    
    # For setting all tags
    def set_all_tags(self):
        global chosen_tags; chosen_tags = list(tag_hash.keys())
        self.controller.show_frame(OptionsPage)


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
        with open(nhi.resource_path("dataframes/state_df.pkl"), 'rb') as inp:
            state_df = pickle.load(inp)

        # Create a thread to run make_sheets() so we can update the screen
        class thread(threading.Thread):
            def __init__(self, func):
                threading.Thread.__init__(self)
                self.func = func
        
            def run(self):
                global options, sdate, edate, territories, chosen_tags
                self.func(thisframe, options, state_df, sdate, edate, territories, chosen_tags, outpath)

        thread(nhi.make_sheets).start()

    # Once sheets are made
    def finish(thisframe):
        thisframe.controller.show_frame(DonePage)


# After excel sheets are made
class DonePage(tk.Frame):
    def __init__(self, parent, controller):
        PageLayout.__init__(self, parent)
        self.controller = controller

        # Instructions
        self.instructions = ttk.Label(self, text="Sheets made, you may exit the program", font=("Times", 15))
        self.instructions.grid(column=1, row=2, columnspan=3, pady=10)
    

if __name__ == '__main__':
    # Driver Code
    app = tkinterApp()
    app.mainloop()
