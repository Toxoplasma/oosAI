#Imports
import time
import random
import win32api
import win32com.client as comclt
import util


#Constants
BIN_XPOS = 4109
BIN_YPOS = 4107
BIN_ORIENT = 4146

BIN_LINK_DEAD = 4128

BIN_BOSS_YPOS = 4299
BIN_BOSS_XPOS = 4301
BIN_BOSS_HIT = 4779

STEPSIZE = 0.01

LINKXDIST = 30
LINKYDIST = 30

LINKLEFT = 87
LINKRIGHT = 85
LINKUP = 84
LINKDOWN = 86
bossDeathCounter = 0

#I, J, K, L controls
ACTION_TO_VKEY = dict(left = 0x4A, right = 0x4C, up = 0x49, down = 0x4B,
                        a = 0x5A, b = 0x58, getstate = 0xBE, #a is z, b is x
                        f1 = 0x70) 
ACTION_TO_SKEY = dict(left = 36, right = 38, up = 23, down = 37,
                        a = 44, b = 45, getstate = 46,
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
            if byteIndex == BIN_BOSS_HIT:
                bossHit = byte


            byteIndex += 1
    finally:
        f.close()

    return xPos, yPos, orient, bossXPos, bossYPos, linkDead, bossHit

def argMax(argValues):
    def pairMax((ak, av), (bk, bv)):
        if av > bv:
            return (ak, av)
        return (bk, bv)
    (bestKey, bestValue) = reduce(pairMax, argValues)
    return bestKey


#GAMESTATE CLASS
class GameState():
    def __init__(self, (xPos, yPos, orient, bossXPos, bossYPos, linkDead, bossHit)):
        self.linkPos = (xPos, yPos)
        self.linkOrient = orient
        self.bossPos = (bossXPos, bossYPos)

        if self.bossPos == (0,0):
            self.bossDead = True
        else:
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

    def getNextState(self, action):
        nextState = state #This should make it copy

        if(action == 'left'):
            oldx, oldy = state.linkPos
            nextState.linkPos = (oldx - LINKXDIST, oldy)
            nextState.linkOrient = LINKLEFT
        elif(action == 'right'):
            oldx, oldy = state.linkPos
            nextState.linkPos = (oldx + LINKXDIST, oldy)
            nextState.linkOrient = LINKRIGHT
        elif(action == 'down'):
            oldx, oldy = state.linkPos
            nextState.linkPos = (oldx, oldy + LINKYDIST)
            nextState.linkOrient = LINKDOWN
        elif(action == 'up'):
            oldx, oldy = state.linkPos
            nextState.linkPos = (oldx, oldy - LINKYDIST)
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



#feature-based Q-learning class
class QAgent():
    def __init__(self, numFeatures):
        self.weights = util.Counter()#xDif = 0, yDif = 0,
                            #up = 0, left = 0, down = 0, right = 0)
        self.actions = ["left", "up", "right", "down", "b", "a"]

        self.epsilon = 0.1
        self.discount = 0.8 #gamma
        self.alpha = 0.2 #learning rate

    #Modeled after simpleExtractor
    #To do: Try some bucketing maybe?
    def getFeatures(self, state, action):
        stateFeatures = state.getFeatures()
        nextState = state.getNextState(action)
        nextStateFeatures = nextState.getFeatures()
        feat = util.Counter()
        # feat[nextState] = 1.0
        feat['action=%s' % action] = 1.0

        #Xdif buckets
        if nextStateFeatures["xDif"] < -90:
            feat['xDif<-90'] = 1.0
        elif nextStateFeatures["xDif"] < -60:
            feat['xDif<-60'] = 1.0
        elif nextStateFeatures["xDif"] < -30:
            feat['xDif<-30'] = 1.0
        elif nextStateFeatures["xDif"] < 0:
            feat['xDif<0'] = 1.0
        elif nextStateFeatures["xDif"] < 30:
            feat['xDif<30'] = 1.0
        elif nextStateFeatures["xDif"] < 60:
            feat['xDif<60'] = 1.0
        elif nextStateFeatures["xDif"] < 90:
            feat['xDif<90'] = 1.0
        else:
            feat['xDif>90'] = 1.0

        #ydif buckets
        if nextStateFeatures["yDif"] < -90:
            feat['yDif<-90'] = 1.0
        elif nextStateFeatures["yDif"] < -60:
            feat['yDif<-60'] = 1.0
        elif nextStateFeatures["yDif"] < -30:
            feat['yDif<-30'] = 1.0
        elif nextStateFeatures["yDif"] < 0:
            feat['yDif<0'] = 1.0
        elif nextStateFeatures["yDif"] < 30:
            feat['yDif<30'] = 1.0
        elif nextStateFeatures["yDif"] < 60:
            feat['yDif<60'] = 1.0
        elif nextStateFeatures["yDif"] < 90:
            feat['yDif<90'] = 1.0
        else:
            feat['yDif>90'] = 1.0

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
        features = state.getFeatures()
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
agent = QAgent(len(state.getFeatures()))


#Main game loop
turnCount = 0
while True:
    turnCount+= 1

    dumpState()
    state = GameState(readGameStateFromFile())
    

    action = agent.getAction(state)
    if turnCount % 1000 = 0:
        print "State is: " + str(state)
        print "Action is: " + action

    #Do the action for one STEP
    win32api.keybd_event(ACTION_TO_VKEY[action], ACTION_TO_SKEY[action])
    time.sleep(STEPSIZE)
    win32api.keybd_event(ACTION_TO_VKEY[action], ACTION_TO_SKEY[action], 2)

    #Get the reward and update the weights
    gameIsOver = False

    newState = GameState(readGameStateFromFile())

    reward = 0
    if newState.bossHit: #and (not state.bossHit):
        reward += 10
    if newState.linkDead:
        reward += -100
        gameIsOver = True
    elif newState.bossDead:
        reward += +100
        gameIsOver = True

    #Update
    agent.update(state, action, newState, reward)

    if turnCount % 1000 = 0:
        print "Reward is: " + str(reward)
        print "New weights are: " + str(agent.weights)

    if gameIsOver:
        win32api.keybd_event(ACTION_TO_VKEY['f1'], ACTION_TO_SKEY['f1'])
        win32api.keybd_event(ACTION_TO_VKEY['f1'], ACTION_TO_SKEY['f1'], 2)

    #win32api.keybd_event(0xBE, 46)
    #win32api.keybd_event(0xBE, 46, 2)
    #state = GameState(readGameStateFromFile())
    #print state

