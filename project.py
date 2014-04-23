#Imports
import time
import random
import win32api
import win32com.client as comclt
import util


#Constants
BIN_XPOS = 4109
BIN_YPOS = 4107
BIN_LINK_HIT = BIN_YPOS + 32
BIN_ORIENT = 4146
BIN_LINK_WALLS = 4147 #ypos + 32 #ypos + 3*16 - 8

BIN_LINK_DEAD = 4128

BIN_BOSS_YPOS = 4299
BIN_BOSS_XPOS = 4301
BIN_BOSS_HIT = 4779

STEPSIZE = 0.3

LINKXDIST = 30
LINKYDIST = 30

LINKLEFT = 87
LINKRIGHT = 85
LINKUP = 84
LINKDOWN = 86
bossDeathCounter = 0

BUCKETSIZE = 10

SLASHPERCENT = 4

#I, J, K, L controls
ACTION_TO_VKEY = dict(left = 0x4A, right = 0x4C, up = 0x49, down = 0x4B,
                        a = 0x5A, getstate = 0xBE, #a is z,
                        f1 = 0x70) 
ACTION_TO_SKEY = dict(left = 36, right = 38, up = 23, down = 37,
                        a = 44, getstate = 46,
                        f1 = 59)

#Utility functions
def dumpState():
    #Press period then release it
    win32api.keybd_event(ACTION_TO_VKEY['getstate'], ACTION_TO_SKEY['getstate'])
    win32api.keybd_event(ACTION_TO_VKEY['getstate'], ACTION_TO_SKEY['getstate'], 2)


def readGameStateFromFile():
    xPos = 0
    yPos = 0
    orient = 0
    bossXPos = 0
    bossYPos = 0
    linkDead = 0
    bossHit = 0
    linkHit = 0
    walls = 0

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
            if byteIndex == BIN_LINK_HIT:
                linkHit = byte
            if byteIndex == BIN_ORIENT:
                orient = byte
            if byteIndex == BIN_LINK_WALLS:
                walls = byte
            if byteIndex == BIN_BOSS_XPOS:
                bossXPos = byte
            if byteIndex == BIN_BOSS_YPOS:
                bossYPos = byte
            if byteIndex == BIN_LINK_DEAD:
                linkDead = byte
            if byteIndex == BIN_BOSS_HIT:
                bossHit = byte


            byteIndex += 1
    finally:
        f.close()

    return xPos, yPos, orient, bossXPos, bossYPos, linkDead, bossHit, linkHit, walls

def argMax(argValues):
    def pairMax((ak, av), (bk, bv)):
        if av > bv:
            return (ak, av)
        return (bk, bv)
    (bestKey, bestValue) = reduce(pairMax, argValues)
    return bestKey


#GAMESTATE CLASS
class GameState():
    def __init__(self):
        'hi'

    def __init__(self, (xPos, yPos, orient, bossXPos, bossYPos, linkDead, bossHit, linkHit, walls)):
        global bossDeathCounter
        self.linkPos = (xPos, yPos)
        self.linkOrient = orient
        self.bossPos = (bossXPos, bossYPos)
        self.linkHitValue = linkHit
        self.bossDead = False
        self.leftWall = False
        self.rightWall = False
        self.topWall = False
        self.bottomWall = False

        #Walls
        if walls % 16 == 0x0c:
            self.leftWall = True
        if walls % 16 == 0x03:
            self.rightWall = True
        if walls / 16 == 0x0c:
            self.topWall = True
        if walls / 16 == 0x03:
            self.bottomWall = True

        if self.bossPos == (0,0):
            bossDeathCounter += 1
            if bossDeathCounter >= 5:
                self.bossDead = True
        else:
            bossDeathCounter = 0
            self.bossDead = False

        if linkDead == 0x80:
            self.linkDead = True
        else:
            self.linkDead = False

        if bossHit != 0:
            self.bossHit = True
            print "Boss is hit!"
        else:
            self.bossHit = False

    def getNextState(self, actionPair):
        action, actionTime = actionPair

        nextState = GameState((0, 0, 0, 2, 2, 0, 0, 0, 0))
        nextState.copy(state) #This should make it copy

        if(action == 'left'):
            if not state.leftWall:
                oldx, oldy = state.linkPos
                nextState.linkPos = (oldx - LINKXDIST * actionTime, oldy)
            nextState.linkOrient = LINKLEFT
        elif(action == 'right'):
            if not state.rightWall:
                oldx, oldy = state.linkPos
                nextState.linkPos = (oldx + LINKXDIST * actionTime, oldy)
            nextState.linkOrient = LINKRIGHT
        elif(action == 'down'):
            if not state.bottomWall:
                oldx, oldy = state.linkPos
                nextState.linkPos = (oldx, oldy + LINKYDIST * actionTime)
            nextState.linkOrient = LINKDOWN
        elif(action == 'up'):
            if not state.topWall:
                oldx, oldy = state.linkPos
                nextState.linkPos = (oldx, oldy - LINKYDIST * actionTime)
            nextState.linkOrient = LINKUP

        return nextState

    def getFeatures(self):
            #f1: difference between x pos of link and boss
            f1 = self.linkPos[0] - self.bossPos[0]

            #f2: difference between y pos of link and boss
            f2 = self.linkPos[1] - self.bossPos[1]

            #f3-7: link orientation
            #Up
            f3 = (self.linkOrient == LINKUP)
            #Left
            f4 = (self.linkOrient == LINKLEFT)
            #Down
            f5 = (self.linkOrient == LINKDOWN)
            #Right
            f6 = (self.linkOrient == LINKRIGHT)

            featureDict = dict(xDif = f1, yDif = f2,
                               up = f3, left = f4, down = f5, right = f6)

            return featureDict

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

    def copy(self, state):
        self.linkPos = state.linkPos
        self.linkOrient = state.linkOrient
        self.linkDead = state.linkDead
        self.bossPos = state.bossPos
        self.linkHitValue = state.linkHitValue
        self.bossDead = state.bossDead
        self.bossHit = state.bossHit
        self.leftWall = state.leftWall
        self.topWall = state.topWall
        self.rightWall = state.rightWall
        self.bottomWall = state.bottomWall



#feature-based Q-learning class
class QAgent():
    def __init__(self):
        self.weights = util.Counter()#xDif = 0, yDif = 0,
                            #up = 0, left = 0, down = 0, right = 0)
        #self.actions = ["right", "down", "up", "left", "a"]
        self.actions = [("right", .1),("right", .2),("right", .3),("right", .4),("right", .5),("right", .6),("right", .7),("right", .8),("right", .9),("right", 1.0), \
                        ("left", .1),("left", .2),("left", .3),("left", .4),("left", .5),("left", .6),("left", .7),("left", .8),("left", .9),("left", 1.0), \
                        ("down", .1),("down", .2),("down", .3),("down", .4),("down", .5),("down", .6),("down", .7),("down", .8),("down", .9),("down", 1.0), \
                        ("up", .1),("up", .2),("up", .3),("up", .4),("up", .5),("up", .6),("up", .7),("up", .8),("up", .9),("up", 1.0), \
                        ("a", .3)]

        self.epsilon = 0.25
        self.discount = 0.8 #gamma
        self.alpha = 0.5 #learning rate

    #Modeled after simpleExtractor
    #To do: Try some bucketing maybe?
    def getFeatures(self, state, action):
        stateFeatures = state.getFeatures()
        nextState = state.getNextState(action)
        nextStateFeatures = nextState.getFeatures()
        feat = util.Counter()
        # feat[nextState] = 1.0
        #feat['action=%s' % action] = 1.0

        xdif = nextStateFeatures["xDif"]
        ydif = nextStateFeatures["yDif"]

        #position stuff:
        #feat['linkxPos=%s' % state.linkPos[0]]
        #feat['linkyPos=%s' % state.linkPos[1]]
        #feat['bossxPos=%s' % state.bossPos[0]]
        #feat['bossyPos=%s' % state.bossPos[1]]

        #Xdif buckets
        xDifBucket = int(xdif / BUCKETSIZE)
        feat['xDif<%d' % xDifBucket] = 1.0
        yDifBucket = int(ydif / BUCKETSIZE)
        feat['yDif<%d' % yDifBucket] = 1.0

        #Can hit boss? DOWN
        if -35 < xdif and xdif < 0 and \
           -70 < ydif and ydif < -45 and \
           nextStateFeatures["down"]:
           feat['canHitBoss'] = 1.0

        
        if -35 < xdif and xdif < 0 and \
           -70 < ydif and ydif < -45 and \
           nextStateFeatures["down"] and action[0] == "a":
            feat['hitsBoss'] = 1.0

        #Can hit boss? RIGHT
        #-25 to -50 x
        #-50 to -25 y
        if -50 < xdif and xdif < -20 and \
           -50 < ydif and ydif < -25 and \
           nextStateFeatures["right"]:
           feat['canHitBoss'] = 1.0

        
        if -50 < xdif and xdif < -20 and \
           -50 < ydif and ydif < -25 and \
           nextStateFeatures["right"] and action[0] == "a":
            feat['hitsBoss'] = 1.0

        #Can hit boss? LEFT
        #x: 10 - 35
        if 10 < xdif and xdif < 35 and \
           -50 < ydif and ydif < -30 and \
           nextStateFeatures["left"]:
           feat['canHitBoss'] = 1.0

        
        if 10 < xdif and xdif < 35 and \
           -50 < ydif and ydif < -30 and \
           nextStateFeatures["left"] and action[0] == "a":
            feat['hitsBoss'] = 1.0


        #Do we run into aqua?
        if -35 < xdif and xdif < 25 and \
           -50 < ydif and ydif < 20:
           feat['insideBoss'] = 1.0


        #Orientation
        # if (nextState.linkOrient == LINKUP): feat['linkUp'] = 1.0
        # if (nextState.linkOrient == LINKLEFT): feat['linkLeft'] = 1.0
        # if (nextState.linkOrient == LINKDOWN): feat['linkDown'] = 1.0
        # if (nextState.linkOrient == LINKRIGHT): feat['linkRight'] = 1.0

        #Add a guy is hittable feature or a hits guy feature

        #feat['xd=%d' % ] = 1.0
        #feat['yd=%d' % nextStateFeatures.yDif] = 1.0
        feat['bias'] = 1.0
        #feat[(state, action)] = 1.0
        return feat


    def getQValue(self, state, action):
        #Compute new state from state action pair
        #Simple extractor
        features = self.getFeatures(state, action)
        #features = nextState.getFeatures()

        featureNames = sorted(features.keys())

        total = 0
        for featureName in featureNames:
            total += features[featureName] * self.weights[featureName]

        return total

    def computeValueFromQValues(self, state):
        actions = self.actions

        if actions == []:
            print "WE DUN KICKED THE BOOKET"
            return 0.0

        bestScore = float("-inf")
        for action in actions:
            Qvalue = self.getQValue(state, action)
            if Qvalue >= bestScore:
                bestScore = Qvalue

        return bestScore

    def computeActionFromQValues(self, state):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        "*** YOUR CODE HERE ***"
        actions = self.actions

        bestAction = None
        bestScore = float("-inf")
        for action in actions:
            Qvalue = self.getQValue(state, action)
            if Qvalue > bestScore:
                bestScore = Qvalue
                bestAction = action
            if Qvalue == bestScore and random.uniform(0, 1) >= 0.5:
                bestScore = Qvalue
                bestAction = action

        return bestAction

    def getAction(self, state):
        legalActions = self.actions

        action = None
        "*** YOUR CODE HERE ***"
        if random.uniform(0, 1) <= (self.epsilon):
          action = random.choice(legalActions)
        else:
          action = self.computeActionFromQValues(state)
        

        return action

    def update(self, state, action, nextState, reward):
        """
           Should update your weights based on transition
        """
        "*** YOUR CODE HERE ***"
        features = self.getFeatures(state, action) #self.featExtractor.getFeatures(state, action)
        featureNames = featureNames = sorted(features.keys())

        newWeights = self.weights.copy()

        bestAction = self.computeActionFromQValues(nextState)
        #print "best action: ", bestAction
        maxActionQValue = 0.0
        if bestAction != None:
          maxActionQValue = self.getQValue(nextState, bestAction)

        for featureName in featureNames:
          difference = reward + self.discount * maxActionQValue - self.getQValue(state, action)
          newWeights[featureName] = self.weights[featureName] + self.alpha * difference * features[featureName]

        self.weights = newWeights



#Stuff we do at start
#Create a windows object and use it to switch to VBA
wsh= comclt.Dispatch("WScript.Shell")
wsh.AppActivate("VisualBoyAdvance")

#Make our learner
state = GameState(readGameStateFromFile())
agent = QAgent()


#Main game loop
turnCount = 0
while True:
    turnCount+= 1

    dumpState()
    time.sleep(.01)
    state = GameState(readGameStateFromFile())
    

    action = agent.getAction(state)

    if turnCount % SLASHPERCENT == 0:
        action = ('a', .3)
    
    if turnCount % 100 == 0:
        print "State is: " + str(state)
        print "Action is: " + action

    #Do the action for one STEP

    win32api.keybd_event(ACTION_TO_VKEY[action[0]], ACTION_TO_SKEY[action[0]])
    time.sleep([action1])
    win32api.keybd_event(ACTION_TO_VKEY[action[0]], ACTION_TO_SKEY[action[0]], 2)

    #Get the reward and update the weights
    gameIsOver = False

    dumpState()
    time.sleep(.01)

    newState = GameState(readGameStateFromFile())
    #bossHitting = agent.getFeatures(newState, "a")
    #print "Can hit boss: " + str(bossHitting["canHitBoss"])
    #print "Hits boss: " + str(bossHitting["hitsBoss"])
    diffs = newState.getFeatures()

    #print "Link hit value: " + str(state.linkHitValue)
    #print "New Link hit value: " + str(newState.linkHitValue)
    reward = 0
    if state.linkHitValue == 0 and newState.linkHitValue != 0: #state.linkHitValue != newState.linkHitValue and \
        #state.linkHitValue != 0 and newState.linkHitValue != 0:
        print "Link got hit! Do better!"
        print "XDiff: " + str(diffs["xDif"]) + " YDiff: " + str(diffs["yDif"])
        reward += -1
    if newState.bossHit: #and (not state.bossHit):
        print "XDiff: " + str(diffs["xDif"]) + " YDiff: " + str(diffs["yDif"])
        reward += 10
    if newState.linkDead:
        reward += -2
        gameIsOver = True
    elif newState.bossDead:
        reward += 100
        gameIsOver = True

    #Update
    agent.update(state, action, newState, reward)
    #print "Action is: " + str(action) + ", Reward is: " + str(reward)

    interestingKeys = ['linkUp', 'linkRight', 'linkLeft', 'linkDown', 'canHitBoss', 'hitsBoss']
    if turnCount % 100 == 0:        
        print "New weights are: "
        for key in sorted(agent.weights.keys()):
            if key in interestingKeys:
                lol = 0
                print "  " + key + ": " + str(agent.weights[key])

    if gameIsOver:
        win32api.keybd_event(ACTION_TO_VKEY['f1'], ACTION_TO_SKEY['f1'])
        win32api.keybd_event(ACTION_TO_VKEY['f1'], ACTION_TO_SKEY['f1'], 2)

    #win32api.keybd_event(0xBE, 46)
    #win32api.keybd_event(0xBE, 46, 2)
    #state = GameState(readGameStateFromFile())
    #print state

