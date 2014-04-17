#Test reading in memory
import time

BIN_XPOS = 4109
BIN_YPOS = 4107
BIN_ORIENT = 4146

BIN_LINK_DEAD = 4132

BIN_BOSS_YPOS = 4299
BIN_BOSS_XPOS = 4301

STEPSIZE = 0.5

class GameState():
    def __init__(self, (xPos, yPos, orient, bossXPos, bossYPos, linkDead)):
        self.linkPos = (xPos, yPos)
        self.linkOrient = orient
        self.bossPos(bossXPos, bossYPos)

        if self.bossPos == (0,0):
            self.bossDead = True
        else:
            self.bossDead = False

        if linkDead == 0x80:
            self.linkDead = True
        else:
            self.linkDead = False

    def __repr__(self):
        (lx, ly) = self.linkPos
        ret = "Link: " , self.linkPos , "orient:", self.linkOrient ", dead: ", self.linkDead, "\nboss: " , self.bossPos, "dead: ", self.bossDead
        return ret

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

    return xPos, yPos, orient, bossXPos, bossYPos



while True:
    time.sleep(1)

    print readGameStateFromFile()



while True:
    time.sleep(STEPSIZE)

    state = GameState(readGameStateFromFile)

