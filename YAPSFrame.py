from smb.SMBConnection import SMBConnection
import config
import tempfile
import io
#from tkinter import *
from Tkinter import *
from PIL import Image, ImageTk
#from smb import *
#from SMBConnection import *
import locale
import threading
import time
from contextlib import contextmanager


#--------functions
def GetDirs(conn, share, directory):
    print(directory)
    sharedfiles = conn.listPath(share_name, directory)
    dirs = []
    for sharedfile in sharedfiles:
        #skip the built in directories
        if sharedfile.filename == '.' or sharedfile.filename == '..':
            continue
        if sharedfile.isDirectory:
            newdir = directory + '/' + sharedfile.filename
            dirs.append(newdir)
            #dirs = dirs + GetDirs(conn, share, newdir)
    return dirs

@contextmanager 
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)



#--------main
LOCALE_LOCK = threading.Lock()

#set up constants
screen_base_width = 1920
screen_base_height = 1080
screen_multiplier = 1 #/1.875
screen_width = screen_base_width * screen_multiplier
screen_height = screen_base_height * screen_multiplier
screen_tuple = (screen_width,screen_height)
screen_ratio = screen_width/screen_height

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
news_country_code = 'us'
weather_api_token = '<TOKEN>' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 48
large_text_size = 24
medium_text_size = 16
small_text_size = 8


#set up connection
userID = config.userID
password = config.password

client_machine_name = config.client_machine_name
server_name = config.server_name
server_ip = config.server_ip
domain_name = config.domain_name

share_name = config.share_name
photo_dir = '/' + config.photo_directory

conn = SMBConnection(userID, password, client_machine_name, server_name, domain=domain_name, use_ntlm_v2=True,
                     is_direct_tcp=True)

conn.connect(server_ip, 445)

#set up tk
#~ root = Tk()
#~ root.title('background image')
#~ root.geometry("%dx%d+%d+%d" % (screen_width, screen_height, 0, 0))

#build a list of folders
print("building directory list")
dirs = GetDirs(conn, share_name, photo_dir)




class Photo(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        imageTemp=None
        self.panel1 = Label(self, image=imageTemp)
        self.panel1.pack(side='top', fill='both', expand='yes')
        self.flip()
    
    def flip(self):
        #find a photo to display
        photo_path = photo_dir + '/' + 'grace5.jpg'

        #read a photo to memory
        fp = io.BytesIO()
        file_attrs, retrlen = conn.retrieveFile(share_name,photo_path,fp)
        fp.seek(0)

        #resize the photo and setup for display
        image1a = Image.open(fp)
        image_w = image1a.width
        image_h = image1a.height
        ratio = float(image_w)/float(image_h)

        if ratio < screen_ratio:  #height is the constraint
            h = int(screen_height)
            w = int(h*ratio)
        else:   #width is the constraint
            w = int(screen_width)
            h = int(w/ratio)

        image1r = image1a.resize((w,h),Image.ANTIALIAS)
        image1 = ImageTk.PhotoImage(image1r)
        fp.close()

        #show the photo
        self.panel1.config(image=image1)
        self.panel1.image = image1  
        self.after(200, self.flip)    

class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=00, pady=0)
        # Photo
        self.photo = Photo(self.topFrame)
        self.photo.pack(side=LEFT, anchor=N, padx=00, pady=0)
        #~ # weather
        #~ self.weather = Weather(self.topFrame)
        #~ self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        #~ # news
        #~ self.news = News(self.bottomFrame)
        #~ self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)
        #~ # calender - removing for now
        #~ # self.calender = Calendar(self.bottomFrame)
        #~ # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':
    w = FullscreenWindow()
    w.tk.mainloop()



