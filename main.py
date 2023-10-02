import pygame
import sys
import os
import random
import json
from PIL import Image



pygame.font.init()
pygame.init()

#initial window size
STARTWIDTH = 800
STARTHEIGHT = 600

TITLE = "Breaking Screensaver"

FPS = 60

RESOURCESDIRECTORY = "resources"

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

#ratios
HEIGHTRATIO = 0.75 # multiply width by this to get height
BOARDRATIO = 0.9 # multiply app size by this to get board size
IMAGERATIO = 0.2 # multiply board size by this to get image size 
OFFSETRATIO = 0.0125 # multiply board size by this to get board offset
GUIXRATIO = 0.91875 # multiply app width by this to get gui x 
GUIYRATIO = 0.417 # multiply app height by this to get base gui y 
GUIBETWEENRATIO = 0.1 # multiply app height by this to get distance between gui
GUIWIDTHRATIO = 0.075 # multiply app width by this to get gui width
GUIHEIGHTRATIO = 0.083 # multiply app height by this to get gui height

#funny font
SANS = pygame.font.Font("data\\sans.ttf", 48)


class App:
    
    def __init__(self, width:int = STARTWIDTH, height:int = STARTHEIGHT):
        
        self.width = width
        self.height = height
        
        self._root = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        pygame.display.set_caption(TITLE)
        pygame.display.set_icon(pygame.image.load("data\\icon.ico"))
        
        self._clock = pygame.time.Clock()
        
        self.board:Board = Board(self)
        
        self.events:list[pygame.event.Event] = None
        
        self.resourceManager = ResourceManager()
        self.resourceManager.loadResourcesFromMainDirectory()
        
        self.lastGuiIndex = 0
        
        self.guiElements:list[GuiElement] = []
        
        self.initSaverCreators()
        
        self.addGuiElement(
            Button(
                self, 
                self.lastGuiIndex, 
                self.width * GUIWIDTHRATIO, 
                self.height * GUIHEIGHTRATIO, 
                self.width * GUIXRATIO, 
                (self.height * OFFSETRATIO) + ((self.height * GUIBETWEENRATIO) * self.lastGuiIndex),
                "Очистить!!",
                BLACK,
                WHITE,
                self.board.clearSavers
            )
        )

        self.speedInput = InputField(
                self,
                self.lastGuiIndex,
                self.width * GUIWIDTHRATIO,
                self.height * GUIHEIGHTRATIO,
                self.width * GUIXRATIO,
                (self.height * OFFSETRATIO) + ((self.height * GUIBETWEENRATIO) * self.lastGuiIndex),
                "Скорость:",
                "5",
                GREEN,
                BLACK
        )

        self.addGuiElement(self.speedInput)
        
        self.board.addSaver(self.resourceManager.getResourceByName("waltuh"), -1, -1, 5)

    def addGuiElement(self, element):
        
        self.guiElements.append(element)
        
        self.lastGuiIndex += 1
    
    def getSpeed(self):
        
        return int(self.speedInput.text)

    def initSaverCreators(self):
        
        for resource in self.resourceManager.getAllResources():
            
            self.addGuiElement(
                Button(
                    self, 
                    self.lastGuiIndex,
                    self.width * GUIWIDTHRATIO, 
                    self.height * GUIHEIGHTRATIO, 
                    self.width * GUIXRATIO, 
                    (self.height * OFFSETRATIO) + ((self.height * GUIBETWEENRATIO) * self.lastGuiIndex), 
                    resource["resourceName"], 
                    BLACK, 
                    WHITE,
                    self.board.generateSaver, 
                    resource
                )
            )
    
    def _handleEvents(self):
        
        for event in self.events:
            
            if event.type == pygame.QUIT:
                
                pygame.quit()
                sys.exit()    
                
            elif event.type == pygame.VIDEORESIZE:
                
                self.width = event.w
                self.height = event.h 
                 
                self.board.resize()
                
                for element in self.guiElements:
                    
                    element.resize()
    
    def draw(self, surface: pygame.Surface, rect: pygame.Rect):
        
        self._root.blit(surface, rect)
    
    def getTime(self) -> int:
        
        return pygame.time.get_ticks()
    
    def getRandomResource(self):
        
        return self.resourceManager.getRandomResource()
    
    def idle(self):
        
        while True:
            #delay
            self._clock.tick(FPS)
            
            #handle important app events
            self.events = pygame.event.get()
            
            self._handleEvents()
            self.board.handleEvents()
            
            #logic
            for guiElement in self.guiElements:
                
                guiElement.handleEvents()
                
            self.board.updateSavers()
            
            #drawing
            self._root.fill(WHITE)
            
            for guiElement in self.guiElements:
                
                guiElement.draw()
                
            self.board.render()
            
            pygame.display.flip()

class Board:
    
    def __init__(self, app: App):
        
        self._app = app
        
        self.width = self._app.width * BOARDRATIO
        self.height = self._app.height * BOARDRATIO
        
        self._root = pygame.Surface((self.width, self.height))
        self.rect = self._root.get_rect(topleft = (self._app.width * OFFSETRATIO, self._app.height * OFFSETRATIO))
        
        self._savers: list[Saver] = []
        
        self.focusedOnSaver = False
    
    def clearSavers(self):
        
        self._savers = []
    
    def addSaver(self, context:dict, x:int, y:int, speed:int, dirX:int = 1, dirY:int = 1):
        
        self._savers.append(Saver(self._app, self, context, x, y, speed, dirX, dirY))
    
    def generateSaver(self, context: dict):
        
        saverSize = getCurrentSaversSize(self)


        x = random.randint(int((self.rect.x * 2) + 1), int((self.width - saverSize[0] + self.rect.x) - 1))        
        y = random.randint(int((self.rect.y * 2) + 1), int((self.height - saverSize[1] + self.rect.y) - 1))

        speed = self._app.getSpeed()
        
        dirX = random.choice([1,-1])
        dirY = random.choice([1,-1])
        
        self.addSaver(context, x, y, speed, dirX, dirY)

    def handleEvents(self):

        for event in self._app.events:
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                
                isFocused = False
                
                for saver in self._savers:
                    
                    if saver.rect.collidepoint(event.pos):
                        
                        isFocused = True
                        saver.focus = True
                        
                    else:
                        
                        saver.focus = False
                        
                self.focusedOnSaver = isFocused
                
            elif event.type == pygame.KEYDOWN:
                
                if event.key == 127: # 127 = del
                    
                    if self.focusedOnSaver:
                        
                        for saver in self._savers:
                            
                            if saver.focus:
                                
                                self._savers.remove(saver)
                                
                        self.focusedOnSaver = False

    def render(self):
        
        self._root.fill(WHITE)
        
        pygame.draw.rect(self._root, BLACK, (self.rect.x, self.rect.y, self.rect.width - self.rect.x, self.rect.height - self.rect.y), 2)
        
        self._app.draw(self._root, self.rect)
        
        for saver in self._savers:
            
            saver.draw()
    
    def resize(self):
        
        self.width = self._app.width * BOARDRATIO
        self.height = self._app.height * BOARDRATIO

        self._root = pygame.Surface((self.width, self.height))
        
        self.rect = self._root.get_rect(topleft = (self._app.width * OFFSETRATIO, self._app.height * OFFSETRATIO))
        
        for saver in self._savers:
            
            saver.resizeOnBoard()

    def updateSavers(self):
        
        if self.focusedOnSaver: return

        for saver in self._savers:
            
            saver.update()       

class Saver:
    
    def __init__(self, 
                 app:App, 
                 board:Board, 
                 context, 
                 x:int, y:int, 
                 speed:int, 
                 startDirX:int = 1, 
                 startDirY:int = 1):
        
        self._app = app
        
        self.board = board
        
        self.width = board.width * IMAGERATIO
        self.height = board.height * IMAGERATIO
        
        self.speed = speed
        
        self.resourceManager = SaverResourceManager(self)
        self.resourceManager.loadResourcesFromContext(context)
        
        actualX = x
        if actualX == -1:
            actualX = (self.board.width / 2) - self.width
            
        actualY = y
        if actualY == -1:
            actualY = (self.board.height / 2) - self.height
        
        self.rect = self.resourceManager.idleImage.image.get_rect(topleft=(actualX, actualY))
        
        self.wallHitted = False

        self.focus = False

        self.cornerHitted = False
        self.lastCornerHitTime = None
        
        self.directionX = startDirX
        self.directionY = startDirY
    
    def resizeOnBoard(self):
        
        self.width = self.board.width * IMAGERATIO
        self.height = self.board.height * IMAGERATIO
        
        self.resourceManager.createImages() #recreate images again
        
        self.rect = self.resourceManager.idleImage.image.get_rect(topleft=(self.rect.x, self.rect.y))
        
    def hitWall(self):
        
        self.wallHitted = True
        
        self.resourceManager.hitWall()
    
    def cornerHit(self):
        
        self.cornerHitted = True
        self.wallHitted = False
        
        self.lastCornerHitTime = self._app.getTime()
        
    def update(self):
        
        if self.cornerHitted:
            
            if self._app.getTime() - self.lastCornerHitTime > 2500:
                
                self.cornerHitted = False
                
            return
        
        self.rect.x += self.speed * self.directionX
        self.rect.y += self.speed * self.directionY
        
        xHitted = False
        
        if self.rect.x >= self.board.width - self.width + self.board.rect.x:
            
            self.directionX = -self.directionX
            
            self.rect.x = (self.board.width - self.width + self.board.rect.x) - 1
            
            self.hitWall()
            
            xHitted = True
            
        elif self.rect.x <= self.board.rect.x * 2:
            
            self.directionX = -self.directionX
            
            self.rect.x = (self.board.rect.x * 2) + 1
            
            self.hitWall()
            
            xHitted = True
            
        if self.rect.y >= self.board.height - self.height + self.board.rect.y:
            
            self.directionY = -self.directionY
            
            self.rect.y = (self.board.height - self.height + self.board.rect.y) - 1
            
            self.hitWall()
            
            if xHitted:
                
                self.cornerHit()
                
            else:
                
                self.hitWall()  
                
        elif self.rect.y <= self.board.rect.y * 2:
            
            self.directionY = -self.directionY
            
            self.rect.y = (self.board.rect.y * 2) + 1
            
            if xHitted:
                
                self.cornerHit()
                
            else:
                
                self.hitWall()  

    def draw(self):
        
        surface = pygame.Surface((self.rect.width, self.rect.height))
        
        if self.focus:
            
            surface.fill(RED)
        else:
            
            surface = self.resourceManager.render()
            
        app.draw(surface, self.rect)
       
class GuiElement:
    
    def __init__(self, 
                 app:App, 
                 indexInColumn:int, 
                 width:float, 
                 height:float, 
                 x:int, y:int, 
                 text:str = "", 
                 bgColor:tuple[int, int, int] = WHITE, 
                 textColor:tuple[int, int, int] = BLACK):
        
        self.app = app
        
        self.indexInColumn = indexInColumn
        
        self.width = width
        self.height = height
        
        self.text = text
        
        self.surface = pygame.Surface((self.width, self.height))
        
        self.rect = self.surface.get_rect(topleft = (x, y))
        
        self.bgColor = bgColor
        self.textColor = textColor
    
    def renderText(self) -> pygame.Surface:
        
        return resizeImage(SANS.render(self.text, True, self.textColor), self.width, self.height)
    
    def draw(self):
        
        self.surface.fill(self.bgColor)
        
        self.app.draw(self.surface, self.rect)
        
        if self.text != "": self.app.draw(self.renderText(), self.rect)
    
    def resize(self):
        
        self.width = self.app.width * GUIWIDTHRATIO
        self.height = self.app.height * GUIHEIGHTRATIO
        
        self.surface = pygame.Surface((self.width, self.height))
        
        self.rect = self.surface.get_rect(topleft = (
           self.app.width * GUIXRATIO, 
           (self.app.height * OFFSETRATIO) + ((self.app.height * GUIBETWEENRATIO) * self.indexInColumn) 
        ))
      
    def handleEvents(self):
        
        pass

class Button(GuiElement):
    
    def __init__(self, app:App, indexInColumn:int, width:float, height:float, x:int, y:int, text="", bgColor:tuple[int,int,int]=WHITE, textColor:tuple[int,int,int]=BLACK, command=None, args=None):
        super().__init__(app, indexInColumn, width, height, x, y, text, bgColor, textColor)
        
        self.command = command
        self.args = args
        
    def handleEvents(self):
        
        for event in self.app.events:
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                
                if self.rect.collidepoint(event.pos):
                    
                    if self.command: 
                        
                        if self.args:
                            
                            self.command(self.args)
                            
                        else:
                            
                            self.command()

class InputField(GuiElement):

    def __init__(self, 
                 app:App, 
                 indexInColumn:int, 
                 width:float, 
                 height:float,
                 x:int, y:int,
                 caption:str = "",
                 text:str = "",
                 bgColor:tuple[int, int, int] = WHITE, 
                 textColor:tuple[int, int, int] = BLACK):

        super().__init__(app, indexInColumn, width, height, x, y, text, bgColor, textColor)

        self.caption = caption
        
        self.captionSurface = self.renderCaption()
        self.captionRect = self.captionSurface.get_rect(topleft=(self.rect.x, self.rect.y + (self.captionSurface.get_height() / 2) + 4))

        self.focused = False

    def clearLastSymbol(self):
        
        self.text = self.text[0:len(self.text) - 1]

    def renderCaption(self):
        
        return resizeImage(SANS.render(self.caption, True, self.textColor), self.width, self.height)

    def resize(self):
        
        super().resize()
        
        self.captionSurface = self.renderCaption()
        
        self.captionRect = self.captionSurface.get_rect(topleft=(self.rect.x, self.rect.y + (self.captionSurface.get_height() / 2) + 4))

    def draw(self):
        
        self.surface.fill(self.bgColor)
        
        if self.focused:
            
            self.surface.fill(RED)
            
        self.app.draw(self.surface, self.rect)
        
        if self.text != "": self.app.draw(self.renderText(), self.rect)
        
        self.app.draw(self.captionSurface, self.captionRect)

    def handleEvents(self):

        for event in self.app.events:
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                
                if self.rect.collidepoint(event.pos):
                    
                    self.focused = True
                    
                else:
                    
                    self.focused = False
                    
            elif event.type == pygame.KEYDOWN:
                
                if self.focused and event.key >= 48 and event.key <= 57 and len(self.text) < 4: #only numbers
                    
                    self.text += chr(event.key)
                    
                elif event.key == 8:
                    
                    self.clearLastSymbol()

class ImageResource:
    
    def __init__(self, resourceName:str, file:str, width:float, height:float):
        
        self.resourceName = resourceName
        
        self.sourceFile = file
        
        self.width = width
        self.height = height
        
        self.image = None
        self.createImage()
        
    def createImage(self):
        
        self.image = resizeImage(pygame.image.load(self.sourceFile), self.width, self.height)
        
    def getImage(self):
        
        return self.image.copy()

class VanishingImageResource(ImageResource):
    
    def __init__(self, resourceName:str, file:str, width:float, height:float, alphaSpeed:int):
        
        super().__init__(resourceName, file, width, height)
        
        self.alphaSpeed = alphaSpeed
        self.currentAlpha = 0
    
    def getImage(self):
        
        if self.currentAlpha <= 0:
            
            return None
        
        image = super().getImage()
        image.set_alpha(self.currentAlpha)
        
        self.currentAlpha -= self.alphaSpeed
        
        return image

class AnimatedImageResource(ImageResource):

    def __init__(self, resourceName:str, file:str, width:float, height:float):
        
        super().__init__(resourceName, file, width, height)
        
        self._frames = []
        
        self.currentFrameIndex = 0
        
        self.loadAnimation()
    
    def loadAnimation(self):
        
        with Image.open(self.sourceFile) as source:
            
            for index in range(1, source.n_frames):
                
                source.seek(index)
                
                self._frames.append(resizeImage(pygame.image.fromstring(source.tobytes(), source.size, source.mode).convert(), self.width, self.height))

        
    def getImage(self) -> pygame.Surface:
        
        frame = self._frames[self.currentFrameIndex]
        
        self.currentFrameIndex += 1
        
        if self.currentFrameIndex == len(self._frames):
            
            self.currentFrameIndex = 0
            
        return frame.copy()

class VanishingAnimatedImageResource(AnimatedImageResource):
    
    def __init__(self, resourceName:str, file:str, width:float, height:float, alphaSpeed:int):
        
        super().__init__(resourceName, file, width, height)
        
        self.alphaSpeed = alphaSpeed
        self.currentAlpha = 0
        
    def getImage(self) -> pygame.Surface:
        
        if self.currentAlpha <= 0:
            
            return None
        
        frame = super().getImage()
        
        frame.set_alpha(self.currentAlpha)
        
        self.currentAlpha -= self.alphaSpeed
        
        return frame
        
class SaverResourceManager:
    
    def __init__(self, saver:Saver):
        
        self.saver = saver
        
        self.alphaSpeed = int(self.saver.speed * 1.2)
        
        self.idleImage = None
        self.wallHitImage = None
        self.cornerHitImage = None
        
        self.wallHitEnabled = True
        self.cornerHitEnabled = True
        
        self.resourcesName = "" 
        self._sourceFiles = {}
        
        self.animationReset = None
    
    def hitWall(self):
        
        if (self.wallHitEnabled):
            
            self.wallHitImage.currentAlpha = 300
            
            if self.animationReset and self.wallHitImage.__class__ is VanishingAnimatedImageResource:
                
                self.wallHitImage.currentFrameIndex = 0
    
    def render(self) -> pygame.Surface:
        
        surface = self.idleImage.getImage()
        
        if self.saver.wallHitted and self.wallHitEnabled:
            
            wallHitImage = self.wallHitImage.getImage()
            
            if wallHitImage: surface.blit(wallHitImage, (0, 0, surface.get_width(), surface.get_height()))
            
        if self.saver.cornerHitted and self.cornerHitEnabled:
            
            surface.blit(self.cornerHitImage.getImage(), (0, 0, surface.get_width(), surface.get_height()))
            
        return surface
    
    def createImages(self):
        
        idleResource = self._sourceFiles["idle"]
        
        if isResourceIsAnimation(idleResource):
            
            self.idleImage = AnimatedImageResource(self.resourcesName, idleResource, self.saver.width, self.saver.height)
            
        else:
            
            self.idleImage = ImageResource(self.resourcesName, idleResource, self.saver.width, self.saver.height)
        
        if self.wallHitEnabled:
            
            wallhitResource = self._sourceFiles["wallhit"]
            
            if isResourceIsAnimation(wallhitResource):
                
                self.wallHitImage = VanishingAnimatedImageResource(self.resourcesName, wallhitResource, self.saver.width, self.saver.height, self.alphaSpeed)
                
            else:
                
                self.wallHitImage = VanishingImageResource(self.resourcesName, wallhitResource, self.saver.width, self.saver.height, self.alphaSpeed)
            
        if self.cornerHitEnabled:
            
            cornerhitResource = self._sourceFiles["cornerhit"]
            
            if isResourceIsAnimation(cornerhitResource):
                
                self.cornerHitImage = AnimatedImageResource(self.resourcesName, cornerhitResource, self.saver.width, self.saver.height)
                
            else:
                
                self.cornerHitImage = ImageResource(self.resourcesName, cornerhitResource, self.saver.width, self.saver.height)
        
    def loadResourcesFromContext(self, context):
        
        self.resourcesName = context["resourceName"]
        
        self.animationReset = context["resetAnimation"]
        
        self.wallHitEnabled = context["wallhitenabled"]
        
        self.cornerHitEnabled = context["cornerhitenabled"]
        
        self._sourceFiles["idle"] = generatePathToImageResource(self.resourcesName, context["idle"])
        
        if self.wallHitEnabled:
            
            self._sourceFiles["wallhit"] = generatePathToImageResource(self.resourcesName, context["wallhit"])
            
        if self.cornerHitEnabled:
            
            self._sourceFiles["cornerhit"] = generatePathToImageResource(self.resourcesName, context["cornerhit"])
        
        self.createImages()

class ResourceManager:
    
    def __init__(self):
        
        self.mainDirectory = RESOURCESDIRECTORY
        
        self._resources:list[dict] = []
    
    def getRandomResource(self) -> dict:
        
        return random.choice(self._resources)
    
    def getAllResources(self) -> list[dict]:
        
        return self._resources
    
    def getResourceByName(self, name) -> dict:
        
        for resource in self._resources:
            
            if resource["resourceName"] == name:
                
                return resource
            
        return None
    
    def loadResourcesFromMainDirectory(self):
        
        for file in os.listdir(self.mainDirectory):
            
            directory = os.path.join(self.mainDirectory, file)
            
            if os.path.isdir(directory):
                
                self.loadResourceFromDirectory(directory)
                
    def loadResourceFromDirectory(self, directory:str):
        
        resourceDirectory = directory.replace(f"{self.mainDirectory}\\", "")
        
        print(f"Loading resource: \"{resourceDirectory}\"")
        
        contextPath = f"{directory}\\context.json"
        
        #check if context exist
        if not os.path.exists(contextPath):
            
            print(f"Resource \"{resourceDirectory}\" has no context, skipping")
            return
        
        #create context
        context = {}
        
        with open(contextPath) as contextFile:
            
            rawContextData = json.load(contextFile)
            
            try:
               
                resourceName = rawContextData["resourceName"]
                if resourceName == "$asDirectory": #marker for fast naming
                    
                    context["resourceName"] = resourceDirectory
                    
                else:
                    
                    context["resourceName"] = resourceName
                   
                resourceIdleImage = rawContextData["idle"]
                if not os.path.exists(f"{directory}\\{resourceIdleImage}"):
                    print(f"Resource \"{resourceDirectory}\" has no idle image, which is required, skipping")
                    return

                context["idle"] = resourceIdleImage
                
                resourceWallHitImage = rawContextData["wallhit"]
                if not os.path.exists(f"{directory}\\{resourceWallHitImage}"):
                    
                    print(f"Resource \"{resourceDirectory}\" has no wallhit image, which is optional")
                    
                    context["wallhitenabled"] = False
                    
                else:
                    
                    context["wallhitenabled"] = True
                    
                    context["wallhit"] = resourceWallHitImage
                    
                resourceCornerHitImage = rawContextData["cornerhit"]
                if not os.path.exists(f"{directory}\\{resourceCornerHitImage}"):
                    
                    print(f"Resource \"{resourceDirectory}\" has no cornerhit image, which is optional")
                    
                    context["cornerhitenabled"] = False
                    
                else:
                    
                    context["cornerhitenabled"] = True
                    
                    context["cornerhit"] = resourceCornerHitImage
                
                animationReset = False
                
                try:
                    
                    animationReset = rawContextData["resetAnimation"]
                    
                except KeyError:
                    
                    print(f"Resource \"{resourceDirectory}\" has no attribute \"animationReset\", automatically set to false")
                    
                context["resetAnimation"] = animationReset
                
            except KeyError: 
                
                print(f"Resource \"{resourceDirectory}\" context is missing required info, check help.txt")
                return
        
        self._resources.append(context)
        
        print(f"Resource: \"{resourceDirectory}\" was added successfully!")

def isResourceIsAnimation(resource) -> bool:
    
    return os.path.splitext(resource)[1] == ".gif"
         
def generatePathToImageResource(resourceName, image) -> str:
    
    return f"{RESOURCESDIRECTORY}\\{resourceName}\\{image}"   
 
def getCurrentSaversSize(board) -> tuple[float, float]:
    
    return (board.width * IMAGERATIO, board.height * IMAGERATIO)

def resizeImage(image:pygame.Surface, width:int, height:int) -> pygame.Surface:
    
    return pygame.transform.scale(image, (width, height))

if __name__ == "__main__":
    
    app = App()
    
    app.idle()