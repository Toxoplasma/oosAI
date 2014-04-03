#Test reading in memory
import sleep

BIN_XPOS = 4109
BIN_YPOS = 4107

def readGameStateFromFile:
	xPos = 0
	yPos = 0


	#Open in read binary mode
	f = open("gb_wram.bin", "rb")

	byteIndex = 0
	try:
	    byte = f.read(1)
	    while byte != "":
	        # Do stuff with byte.
	        byte = f.read(1)

	        if byteIndex = BIN_XPOS:
	        	xPos = byte
	        if byteIndex = BIN_YPOS:
	        	yPos = byte


	        byteIndex += 1
	finally:
	    f.close()

	return xPos, yPos


while True:
	time.sleep(1)

	print readGameStateFromFile()
