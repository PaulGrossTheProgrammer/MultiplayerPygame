# MultiplayerPygame
An example of how to build an MMORPG using Python's PyGame library

How to install pygame on Python for Windows:

Right-click start button, choose Run, or Windows key + R key:

When prompted to "Open:", type:
cmd 
then press Enter, and the Windows command prompt should appear.

Type

C:\\>python --version

Python 3.9.2

c:\\>python -m pip install pygame

Requirement already satisfied: pygame in c:\users\paul_g\appdata\roaming\python\python38\site-packages (1.9.6)

OR

Collecting pygame

  Downloading pygame-2.0.1-cp39-cp39-win_amd64.whl (5.2 MB)
  
     |¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦| 5.2 MB 1.7 MB/s
     
Installing collected packages: pygame

Successfully installed pygame-2.0.1


Now test that the library is installed

c:\\>python

\>\>\>import pygame

pygame 1.9.6

Hello from the pygame community. https://www.pygame.org/contribute.html

\>\>\>exit()

c:\\>

Now double-clicking the pygame dungeon_server.py and dungeon_client.py should run them normally.

Run the server, noting your IP address, for example:

Game Running:

LOCAL IP address = 192.168.1.100

Waiting for clients on port 56789...

Go to another PC and install pygame, then download from Github and run the dungeon_client.py,
entering the server's IP address when prompted.
