from contextlib import contextmanager
import config
import locale
import threading
import time

#for Python 3
from tkinter import *
from smb.SMBConnection import SMBConnection

#for Python 2.7
#from Tkinter import *
#from smb import *
#from SMBConnection import *

#for photos
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import random
import tempfile
import io

#for news
import feedparser

#for calendar
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import datetime

#so we can break from a deep loop
class ContinueI(Exception):
    pass
    
continue_i = ContinueI()


#--------functions
def GetDirs(conn, share, directory):
    print(directory)
    sharedfiles = conn.listPath(share_name, directory)
    dirs = []
    skipdirs = config.skip_directories
    for sharedfile in sharedfiles:
        try:
            #skip 
            for skipdir in skipdirs:
                if sharedfile.filename == skipdir:
                    raise continue_i
        except ContinueI:
            continue
            
        if sharedfile.isDirectory:
            newdir = directory + '/' + sharedfile.filename
            dirs.append(newdir)
            if config.recursive_dirs:
                dirs = dirs + GetDirs(conn, share, newdir)
    return dirs

@contextmanager 
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

def getEXIF(img):
    ret = {}
    info = img._getexif()
    if info is not None:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[str(decoded).lower()] = value
    return ret  

def printEXIF(img):
        tags = getEXIF(img)
        try:
            for tag, value in tags.items():
                print("{" + str(tag) + "}[" + str(value) + "]\n")
        except:
            print("can't get EXIF information\n") 
            
#calendar funtions
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
            

#--------main
LOCALE_LOCK = threading.Lock()

#set up constants
screen_base_width = config.screen_width
screen_base_height = config.screen_height
screen_multiplier = 1 #/1.875
screen_width = screen_base_width * screen_multiplier
screen_height = screen_base_height * screen_multiplier
screen_tuple = (screen_width,screen_height)
screen_ratio = screen_width/screen_height
millis_between_calendar_checks = 1000 * 60 *30

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

#for calendar
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'
photoIsPortrait = True


class Photo(Frame):
    def __init__(self, parent, *args, **kwargs):
        self.parent=parent
        Frame.__init__(self, parent, bg='black')
        imageTemp=None
        self.panel1 = Label(self, image=imageTemp)
        self.panel1.pack(side='top', fill='both', expand='yes')
        self.flip()
    
    def flip(self):
        #find a photo to display
        photo_path = ''
        while photo_path == '':
            #get a random directory
            randomDir = random.choice(dirs)
            #get list of jpgs
            print("rd" + randomDir)
            try:
                sharedphotos = conn.listPath(share_name, randomDir,pattern="*.jpg")
            except:
                continue
            #pick one at random
            photo = random.choice(sharedphotos)
            photo_path = randomDir + '/' + photo.filename

        #read a photo to memory
        fp = io.BytesIO()
        file_attrs, retrlen = conn.retrieveFile(share_name,photo_path,fp)
        fp.seek(0)

        #resize the photo and setup for display
        try:
            imageRaw = Image.open(fp)
        except:
            print("Could not open:" + photo_path)
            fp.close()
            self.flip()
            return

        #print exif info
        exif = getEXIF(imageRaw)

        if exif == None:
            print("could not get exif for " + photo_path + "\n")
        else:
            image_date = exif.get('datetime',"")
            image_orientation = exif.get('orientation',1)
        
        #rotate first    
        if image_orientation == 3:
            imageRot = imageRaw.rotate(180)
            print("Rotating " + photo_path + "\n")
        elif image_orientation == 6:
            imageRot= imageRaw.rotate(270)
            print("Rotating " + photo_path + "\n")
        elif image_orientation == 8:
            imageRot = imageRaw.rotate(90)
            print("Rotating " + photo_path + "\n")
        else:
            imageRot = imageRaw

        #now find the image aspect ratio and size
        image_s = imageRot.size    
        image_w = image_s[0]
        image_h = image_s[1]

        ratio = float(image_w)/float(image_h)

        if ratio < screen_ratio:  #height is the constraint (portrait)
            h = int(screen_height)
            w = int(h*ratio)
            photoIsPortrait = True
        else:   #width is the constraint
            w = int(screen_width)
            h = int(w/ratio)
            photoIsPortrait = False

        #then resize
        imageRR = imageRot.resize((w,h),Image.ANTIALIAS)

        image1 = ImageTk.PhotoImage(imageRR)
        fp.close()
        
        #hide or show the calendar
        if photoIsPortrait:
            self.parent.parent.show_cal()
        else:
            self.parent.parent.hide_cal()

        #show the photo
        self.panel1.config(image=image1)
        self.panel1.image = image1  
        self.after(config.flip_after_secs*1000, self.flip)    

class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', medium_text_size), fg="white", bg="black")
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
            
class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Upcoming' 
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=W)
        self.eventsContainer = Frame(self, bg="black")
        self.eventsContainer.pack(side=TOP)
        self.get_events()

    def get_events(self):
        print("getting events")
        try:
            # remove all children
            for widget in self.eventsContainer.winfo_children():
                widget.destroy()
                
            #~ events_url = "https://news.google.com/news?ned=us&output=rss"

            #~ feed = feedparser.parse(events_url)

            #~ for post in feed.entries[0:5]:
                #~ eventFrame = calendarevent(self.eventsContainer, post.title)
                #~ eventFrame.pack(side=TOP, anchor=W)
                #~ print(event)
                

            now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
            print('Getting the upcoming 10 events')
            eventsResult = service.events().list(
                calendarId=config.google_calendar_id, timeMin=now, maxResults=10, singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])

            if not events:
                eventFrame = calendarevent(self.eventsContainer, "No upcoming events found")
                eventFrame.pack(side=TOP, anchor=W)
                print('No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                lDate = start.split('T')
                sDT = datetime.datetime.strptime(lDate[0],"%Y-%m-%d")
                eventFrame = calendarevent(self.eventsContainer, event['summary'],custom_strftime('%A %B {S}',sDT))
                eventFrame.pack(side=TOP, anchor=W) 
                print(event['summary'],custom_strftime('%A %B {S}',sDT))
                
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get calendar." % e)

        self.after(millis_between_calendar_checks, self.get_events)


class calendarevent(Frame):
    def __init__(self, parent, event_name="",event_date=""):
        Frame.__init__(self, parent, bg='black')

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=W)
        self.eventDate = event_date
        self.eventDateLbl = Label(self, text=self.eventDate, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventDateLbl.pack(side=TOP, anchor=W)

class Blank(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'BLANK' 
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=W)

class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black',cursor="none")
        self.topFrame = Frame(self.tk, background = 'black')
        self.topFrame.parent = self
        #self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        #self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        self.tk.bind('<Up>',self.hide_cal)
        self.tk.bind('<Down>',self.show_cal)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=0, pady=0)
        # Calendar 
        self.calendar = Calendar(self.topFrame)
        self.calendar.pack(side = RIGHT, anchor=S, padx=0, pady=0)
        # Photo
        self.photo = Photo(self.topFrame)
        self.photo.pack(side=LEFT, anchor=N, padx=0, pady=0)
        #~ # weather
        #~ self.weather = Weather(self.topFrame)
        #~ self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        #~ # news
        #~ self.news = News(self.bottomFrame)
        #~ self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)

        #~ self.calendar.pack_forget()
        #blank widget for hidding calendar when there isn't enough room
        #~ self.blank = Blank(self.topFrame)
        #~ self.blank.pack(side=RIGHT, anchor=S, padx=0, pady=0)
        self.toggle_fullscreen()

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"
        
    def hide_cal(self, event=None):
        self.calendar.pack_forget()
        print("hiding")

    def show_cal(self, event=None):
        self.calendar.pack(side = RIGHT, anchor=S, padx=0, pady=0)
        print("showing")

if __name__ == '__main__':
    #do calendar set-up
    print("setting up Google Calendar connection")
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

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

    #build a list of folders
    print("building directory list")
    dirs = GetDirs(conn, share_name, photo_dir)

    #setup windows and begin event loop
    w = FullscreenWindow()
    w.tk.mainloop()



