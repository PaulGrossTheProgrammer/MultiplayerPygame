# MultiplayerPygame
An example of how to build an MMORPG using Python's PyGame library

How to install pygame on Python for Windows:

Right-click start button, choose Run

When prompted to "Open:", type:
cmd 
then press Enter, and the Windows command prompt should appear.

Type

C:\\>python --version
Python 3.8.5

c:\\>python -m pip install pygame
Requirement already satisfied: pygame in c:\users\paul_g\appdata\roaming\python\python38\site-packages (1.9.6)

OR 

(The installer will proceed...)

Test that the library is installed

c:\\>python
import pygame
pygame 1.9.6
Hello from the pygame community. https://www.pygame.org/contribute.html

exit()

c:\\>

Now double-clicking the pygame dungeon_server.py and dungeon_client.py should run them normally.

Run the server, noting your IP address, for example:

Game Running:
LOCAL IP address = 192.168.1.103
Waiting for clients on port 56789...

Go to another PC and install pygame, then download from Github and run the dungeon_client.py,
entering the server's IP address when prompted.
