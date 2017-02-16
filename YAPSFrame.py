from smb.SMBConnection import SMBConnection
import config
import tempfile
from tkinter import *
#from Tkinter import *
from PIL import Image, ImageTk
#from smb import *
#from SMBConnection import *

#set up connection
userID = config.userID
password = config.password
client_machine_name = config.client_machine_name

server_name = config.server_name
server_ip = config.server_ip

domain_name = config.domain_name

conn = SMBConnection(userID, password, client_machine_name, server_name, domain=domain_name, use_ntlm_v2=True,
                     is_direct_tcp=True)

conn.connect(server_ip, 445)

#set up tk
root = Tk()
root.title('background image')




fp = tempfile.TemporaryFile()
file_attrs, retrlen = conn.retrieveFile('big data','Our Pictures/grace6.jpg',fp)
image1 = ImageTk.PhotoImage(Image.open(fp))


root.geometry("%dx%d+%d+%d" % (1024, 768, 0, 0))

panel1 = Label(root, image=image1)
panel1.pack(side='top', fill='both', expand='yes')
panel1.image = image1

root.mainloop()

#~ shares = conn.listShares()

#~ for share in shares:
    #~ if not share.isSpecial and share.name not in ['NETLOGON', 'SYSVOL']:
        #~ print(share.name)
        #~ sharedfiles = conn.listPath(share.name, '/')
        #~ for sharedfile in sharedfiles:
            #~ print(sharedfile.filename)

#~ conn.close()



