import collections

import bpy

from . import nvb_def
from . import nvb_utils
from . import nvb_animnode


class Animation():

    def __init__(self, name = 'UNNAMED'):
        self.name      = name
        self.length    = 1.0
        self.transtime = 1.0
        self.root      = nvb_def.null
        self.eventList = []
        self.nodeList  = collections.OrderedDict()


    def getAnimNode(self, nodeName, parentName = nvb_def.null):
        key = parentName + nodeName
        if key in self.nodeList:
            return self.nodeList[key]
        else:
            return None


    def addAsciiNode(self, asciiBlock):
        node = nvb_animnode.Node()
        node.loadAscii(asciiBlock)
        key  = node.parentName + node.name
        if key in self.nodeList:
            #TODO: Should probably raise an exception
            pass
        else:
            self.nodeList[key] = node


    def addEvent(self, event):
        self.eventList.append(event)


    def addAnimToScene(self, scene, rootDummy):
        # Create a new scene
        # Check if there is already a scene with this animation name
        animScene = None
        if (self.name not in bpy.data.scenes.keys()):
            animScene = bpy.data.scenes.new(self.name)
        else:
            animScene = bpy.data.scenes[self.name]
        animScene.render.fps    = nvb_def.fps
        animScene.frame_start   = 0
        animScene.frame_end     = nvb_utils.nwtime2frame(self.length)
        animScene.frame_current = 0

        if not rootDummy:
            return # Nope

        # Copy objects to the new scene:
        self.copyObjectToScene(animScene, rootDummy, None)


    def copyObjectToScene(self, scene, theOriginal, parent):
        '''
        Copy object and all it's children to scene.
        For object with simple (position, rotation) or no animations we
        create a linked copy.
        For alpha animation we'll need to copy the data too.
        '''
        theCopy        = theOriginal.copy()
        theCopy.parent = parent
        theCopy.name   = theOriginal.name + '.' + self.name
        theCopy.nvb.rawascii  = ''

        # rootDummy ?
        objType = theOriginal.type
        if (objType == 'EMPTY') and (theOriginal.nvb.dummytype == nvb_def.Dummytype.MDLROOT ):
            # We copied the root dummy, set some stuff
            theCopy.nvb.isanimation = True
            theCopy.nvb.animname    = self.name
            theCopy.nvb.transtime   = self.transtime
            theCopy.nvb.animroot    = self.root
            self.addEventsToObject(theCopy)

        # Add animations from the animation node to the newly created object
        if theOriginal.parent:
            animNode = self.getAnimNode(theOriginal.name, theOriginal.parent.name)
        else:
            animNode = self.getAnimNode(theOriginal.name)


        deepCopy = False
        if deepCopy:
            # Always copy all data & materials.
            # Each animation has it's own data.
            if theOriginal.data:
                data      = theOriginal.data.copy()
                data.name = theOriginal.name + '.' + self.name
                theCopy.data = data
                # Create a copy of the material
                if (theOriginal.active_material):
                    material      = theOriginal.active_material.copy()
                    material.name = theOriginal.active_material.name + '.' + self.name
                    theCopy.active_material = material
        else:
            # Create only a single copy of data and materials which is
            # shared between animations.
            # Create an extra copy only on a on-demand basis, i.e. if there
            # are animations attached which need it.
            animDataName = nvb_def.animdataPrefix + theOriginal.name
            if (objType == 'LAMP'):
                if animDataName in bpy.data.lamps:
                    data = bpy.data.lamps[animDataName]
                else:
                    data      = theOriginal.data.copy()
                    data.name = animDataName
                theCopy.data = data
            elif (objType == 'MESH'):
                if animNode.requiresUniqueData():
                    # We need to copy the material and therefore the data block
                    data         = theOriginal.data.copy()
                    data.name    = theOriginal.name + '.' + self.name
                    theCopy.data = data
                    if (theOriginal.active_material):
                        # Copy the material
                        material      = theOriginal.active_material.copy()
                        material.name = theOriginal.active_material.name + '.' + self.name
                        theCopy.active_material = material
                        # No need to copy the textures, as the texture settings
                        # belong to the material texture slot, not the
                        # texture itself
                else:
                    if animDataName in bpy.data.meshes:
                        data = bpy.data.meshes[animDataName]
                    else:
                        data      = theOriginal.data.copy()
                        data.name = animDataName
                    theCopy.data = data

        if animNode:
            '''
            # Only copy as needed
            # We need to copy the data for:
            # - Lamps
            # - Meshes & materials when there are alphakeys
            # (Textures aren't needed)
            if (objType == 'LAMP'):
                data         = theOriginal.data.copy()
                data.name    = theOriginal.name + '.' + self.name
                theCopy.data = data
            elif (objType == 'MESH'):
                if animNode.requiresUniqueData():
                    data         = theOriginal.data.copy()
                    data.name    = theOriginal.name + '.' + self.name
                    theCopy.data = data
                    # Create a copy of the material
                    if (theOriginal.active_material):
                        material      = theOriginal.active_material.copy()
                        material.name = theOriginal.active_material.name + '.' + self.name
                        theCopy.active_material = material
                        # No need to copy the textures, as the texture alpha
                        # belongs to the materials texture slot, not the
                        # texture itself
            '''
            animNode.addAnimToObject(theCopy, self.name)

        # Link copy to the anim scene
        scene.objects.link(theCopy)

        # Convert all child objects too
        for child in theOriginal.children:
            self.copyObjectToScene(scene, child, theCopy)


    def addEventsToObject(self, rootDummy):
        for event in self.eventList:
            newItem = rootDummy.nvb.eventList.add()
            newItem.frame = nvb_utils.nwtime2frame(event[0])
            newItem.name  = event[1]


    def getAnimFromScene(self, scene, rootDummyName = ''):
        pass


    def getAnimFromAscii(self, asciiBlock):
        blockStart = -1
        for idx, line in enumerate(asciiBlock):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if (label == 'newanim'):
                self.name = nvb_utils.getName(line[1])
            elif (label == 'length'):
                self.length = float(line[1])
            elif (label == 'transtime'):
                self.transtime = float(line[1])
            elif (label == 'animroot'):
                self.root = line[1]
            elif (label == 'event'):
                self.addEvent((float(line[1]), line[2]))
            elif (label == 'node'):
                blockStart = idx
            elif (label == 'endnode'):
                if (blockStart > 0):
                    self.addAsciiNode(asciiBlock[blockStart:idx+1])
                    blockStart = -1
                elif (label == 'node'):
                    raise nvb_def.MalformedMdlFile('Unexpected "endnode"')


    def animNodeToAscii(self, bObject, asciiLines):
        node = nvb_animnode.Node()
        node.toAscii(bObject, asciiLines, self.name)

        '''
        for child in bObject.children:
            self.animNodeToAscii(child, asciiLines)
        '''
        # If this mdl was imported, we need to retain the order of the
        # objects in the original mdl file. Unfortunately this order is
        # seemingly arbitrary so we need to save it at import
        # Otherwise supermodels don't work correctly.
        childList = []
        for child in bObject.children:
            childList.append((child.nvb.imporder, child))
        childList.sort(key=lambda tup: tup[0])

        for (imporder, child) in childList:
            self.animNodeToAscii(child, asciiLines)

    def toAscii(self, animScene, animRootDummy, asciiLines, mdlName = ''):
        self.name      = animRootDummy.nvb.animname
        self.length    = nvb_utils.frame2nwtime(animScene.frame_end, animScene.render.fps)
        self.transtime = animRootDummy.nvb.transtime
        self.root      = animRootDummy.nvb.animroot

        asciiLines.append('newanim ' + self.name + ' ' + mdlName)
        asciiLines.append('  length ' + str(round(self.length, 5)))
        asciiLines.append('  transtime ' + str(round(self.transtime, 3)))
        asciiLines.append('  animroot ' + self.root)

        for event in animRootDummy.nvb.eventList:
            eventTime = nvb_utils.frame2nwtime(event.frame, animScene.render.fps)
            asciiLines.append('  event ' + str(round(eventTime, 5)) + ' ' + event.name)

        self.animNodeToAscii(animRootDummy, asciiLines)
        asciiLines.append('doneanim ' + self.name + ' ' + mdlName)
        asciiLines.append('')
