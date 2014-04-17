#Test reading in memory
import time
import win32api
import win32com.client as comclt
wsh= comclt.Dispatch("WScript.Shell")
# switch to emulator window
wsh.AppActivate("VisualBoyAdvance")

BIN_XPOS = 4109
BIN_YPOS = 4107
BIN_ORIENT = 4146

BIN_LINK_DEAD = 4128

BIN_BOSS_YPOS = 4299
BIN_BOSS_XPOS = 4301

STEPSIZE = 0.5
bossDeathCounter = 0

class GameState():
    def __init__(self, (xPos, yPos, orient, bossXPos, bossYPos, linkDead)):
        global bossDeathCounter
        self.linkPos = (xPos, yPos)
        self.linkOrient = orient
        self.bossPos = (bossXPos, bossYPos)

        if self.bossPos == (0,0):
            if bossDeathCounter > 3:
                self.bossDead = True
            else:
                bossDeathCounter += 1
                self.bossDead = False
        else:
            self.bossDead = False
            bossDeathCounter = 0

        if linkDead == 0x80:
            self.linkDead = True
        else:
            self.linkDead = False

    def __repr__(self):
        (lx, ly) = self.linkPos
        linkString = "Link: " + str(self.linkPos) + " orient: " + str(self.linkOrient)
        linkDeadString = ", Life status: "
        if self.linkDead:
            linkDeadString += "Dead"
        else:
            linkDeadString += "Alive"

        bossString = "\nBoss: " + str(self.bossPos)
        bossDeadString = ", Life status: "
        if self.bossDead:
            bossDeadString += "Dead"
        else:
            bossDeadString += "Alive"
        
        ret = linkString + linkDeadString + bossString + bossDeadString
        return ret
    
    def __str__(self):
        return self.__repr__()

def readGameStateFromFile():
    xPos = 0
    yPos = 0
    orient = 0
    bossXPos = 0
    bossYPos = 0
    linkDead = 0

    #Open in read binary mode
    f = open("gb_wram.bin", "rb")

    byteIndex = 0
    try:
        byte = " "
        while byte != "":
            # Do stuff with byte.
            byte = f.read(1)
            if byte != "":
                byte = ord(byte)

            if byteIndex == BIN_XPOS:
                xPos = byte
            if byteIndex == BIN_YPOS:
                yPos = byte
            if byteIndex == BIN_ORIENT:
                orient = byte
            if byteIndex == BIN_BOSS_XPOS:
                bossXPos = byte
            if byteIndex == BIN_BOSS_YPOS:
                bossYPos = byte
            if byteIndex == BIN_LINK_DEAD:
                linkDead = byte


            byteIndex += 1
    finally:
        f.close()

    return xPos, yPos, orient, bossXPos, bossYPos, linkDead


while True:
    time.sleep(STEPSIZE)
    win32api.keybd_event(0xBE, 46)
    win32api.keybd_event(0xBE, 46, 2)
    state = GameState(readGameStateFromFile())
    print state

