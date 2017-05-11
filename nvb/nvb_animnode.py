"""TODO: DOC."""

import mathutils
import collections
import bpy

from . import nvb_def
from . import nvb_utils
from . import nvb_parse


class Keys():
    def __init__(self):
        self.position       = []
        self.orientation    = []
        self.scale          = []
        self.selfillumcolor = []
        self.alpha          = []
        # Lights/lamps
        self.color  = []
        self.radius = []
        # Emitters ... incompatible. Import as text
        self.rawascii = ''

    def hasAlpha(self):
        return len(self.alpha) > 0


class Node():
    def __init__(self, name = 'UNNAMED'):
        self.name       = name
        self.nodetype   = 'dummy'
        self.parentName = nvb_def.null

        # Non-keyed
        self.position    = None
        self.orientation = None
        self.scale       = None
        self.alpha       = None
        # Keyed
        self.keys = Keys()

        self.isEmpty = True

    def __bool__(self):
        '''
        Return false if the node is empty, i.e. it has no anims attached
        '''
        return not self.isEmpty

    def requiresUniqueData(self):
        return (self.keys.hasAlpha() or self.alpha != None)


    def parseKeys3f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 3 floats (not counting the time value)
        '''
        l_float = float
        for line in asciiBlock:
            keyList.append((l_float(line[0]),
                            l_float(line[1]),
                            l_float(line[2]),
                            l_float(line[3])) )
        self.isEmpty = False


    def parseKeys4f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 4 floats (not counting the time value)
        '''
        l_float = float
        for line in asciiBlock:
            keyList.append((l_float(line[0]),
                            l_float(line[1]),
                            l_float(line[2]),
                            l_float(line[3]),
                            l_float(line[4])) )
        self.isEmpty = False


    def parseKeys1f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 1 float (not counting the time value)
        '''
        l_float = float
        for line in asciiBlock:
            keyList.append((l_float(line[0]),
                            l_float(line[1])) )
        self.isEmpty = False


    def parseKeysIncompat(self, asciiBlock):
        '''
        Parse animation keys incompatible with blender. They will be saved
        as plain text.
        '''
        for line in asciiBlock:
            self.keys.rawascii = self.keys.rawascii + '\n' + ' '.join(line)
        self.isEmpty = False

    def findEnd(self, asciiBlock):
        '''
        We don't know when a list of keys of keys will end. We'll have to
        search for the first non-numeric value
        '''
        l_isNumber = nvb_utils.isNumber
        return next((i for i, v in enumerate(asciiBlock) if not l_isNumber(v[0])), -1)

    def loadAscii(self, asciiBlock):
        l_float    = float
        l_int      = int
        l_isNumber = nvb_utils.isNumber
        for idx, line in enumerate(asciiBlock):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if label == 'node':
                self.nodeType = line[1].lower()
                self.name = nvb_utils.getName(line[2])
            elif label == 'endnode':
                return
            elif label == 'endlist':
                # Can't rely on that being here. We have our own way to get
                # the end of a key list
                pass
            elif label == 'parent':
                self.parentName = nvb_utils.getName(line[1])
            # Non-keyed animations
            elif label == 'position':
                # position: 1 key, positionkey: >= 1 key (probably)
                self.position = (l_float(line[1]),
                                 l_float(line[2]),
                                 l_float(line[3]))
                self.isEmpty = False
            elif label == 'orientation':
                # orientation: 1 key, orientationkey: >= 1 key (probably)
                self.orientation = (l_float(line[1]),
                                    l_float(line[2]),
                                    l_float(line[3]),
                                    l_float(line[4]))
                self.isEmpty = False
            elif label == 'scale':
                # scale: 1 key, scalekey: >= 1 key (probably)
                self.scale = l_float(line[1])
                self.isEmpty = False
            elif label == 'alpha':
                # alpha: 1 key, alphakey: >= 1 key (probably)
                self.alpha = l_float(line[1])
                self.isEmpty = False

            # Keyed animations
            elif label == 'positionkey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeys3f(asciiBlock[idx+1:idx+numKeys+1], self.keys.position)
                self.isEmpty = False
            elif label == 'orientationkey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeys4f(asciiBlock[idx+1:idx+numKeys+1], self.keys.orientation)
                self.isEmpty = False
            elif label == 'scalekey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                nvb_parse.f2(asciiBlock[idx+1:idx+numKeys+1], self.keys.scale)
                self.isEmpty = False
            elif label == 'alphakey':
                # If this is an emitter, alphakeys are incompatible. We'll
                # handle them later as plain text
                numKeys = self.findEnd(asciiBlock[idx+1:])
                if self.nodeType == 'emitter':
                    self.parseKeysIncompat(asciiBlock[idx:idx+numKeys+1])
                else:
                    self.parseKeys1f(asciiBlock[idx+1:idx+numKeys+1], self.keys.alpha)
                self.isEmpty = False
            elif label == 'selfillumcolorkey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeys3f(asciiBlock[idx+1:idx+numKeys+1], self.keys.selfillumcolor)
                self.isEmpty = False
            # Lights/lamps only
            elif label == 'colorkey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeys3f(asciiBlock[idx+1:idx+numKeys+1], self.keys.color)
                self.isEmpty = False
            elif label == 'radiuskey':
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeys1f(asciiBlock[idx+1:idx+numKeys+1], self.keys.radius)
                self.isEmpty = False

            # Some unknown text.
            # Probably keys for emitters = incompatible with blender. Import as text.
            elif not l_isNumber(line[0]):
                numKeys = self.findEnd(asciiBlock[idx+1:])
                self.parseKeysIncompat(asciiBlock[idx:idx+numKeys+1])
                self.isEmpty = False

    def addAnimToMaterial(self, targetMaterial, animName = ''):
        if not self.requiresUniqueData():
            return

        #actionName           = animName + '.' + targetMaterial.name
        actionName           = targetMaterial.name
        action               = bpy.data.actions.new(name=actionName)
        action.use_fake_user = True

        # If there is a texture, use texture alpha for animations
        if targetMaterial.active_texture:
            # Material has a texture
            # data_path = material.texture_slots[x].alpha_factor
            tslotIdx = targetMaterial.active_texture_index
            curve    = action.fcurves.new(data_path='texture_slots[' + str(tslotIdx) + '].alpha_factor')
        else:
            # No texture.
            # data_path = material.alpha
            curve = action.fcurves.new(data_path='alpha')

        if self.keys.alpha:
            for key in self.keys.alpha:
                curve.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[1])
        elif self.alpha is not None:
            curve.keyframe_points.insert(0, self.alpha)

        targetMaterial.animation_data_create()
        targetMaterial.animation_data.action = action


    def addAnimToObject(self, targetObject, animName = ''):
        '''
        Add the animations in this node to target object
        '''
        #actionName           = animName + '.' + targetObject.name
        actionName           = targetObject.name
        action               = bpy.data.actions.new(name=actionName)
        action.use_fake_user = True

        if (self.keys.orientation):
            curveX = action.fcurves.new(data_path='rotation_euler', index=0)
            curveY = action.fcurves.new(data_path='rotation_euler', index=1)
            curveZ = action.fcurves.new(data_path='rotation_euler', index=2)
            currEul = None
            prevEul = None
            for key in self.keys.orientation:
                frame = nvb_utils.nwtime2frame(key[0])
                eul   = nvb_utils.nwangle2euler(key[1:5])
                currEul = nvb_utils.eulerFilter(eul, prevEul)
                prevEul = currEul
                curveX.keyframe_points.insert(frame, currEul.x)
                curveY.keyframe_points.insert(frame, currEul.y)
                curveZ.keyframe_points.insert(frame, currEul.z)
        elif self.orientation is not None:
            curveX = action.fcurves.new(data_path='rotation_euler', index=0)
            curveY = action.fcurves.new(data_path='rotation_euler', index=1)
            curveZ = action.fcurves.new(data_path='rotation_euler', index=2)
            eul = nvb_utils.nwangle2euler(self.orientation)
            curveX.keyframe_points.insert(0, eul[0])
            curveY.keyframe_points.insert(0, eul[1])
            curveZ.keyframe_points.insert(0, eul[2])

        # Set location channels if there are location keys
        if (self.keys.position):
            curveX = action.fcurves.new(data_path='location', index=0)
            curveY = action.fcurves.new(data_path='location', index=1)
            curveZ = action.fcurves.new(data_path='location', index=2)
            for key in self.keys.position:
                frame = nvb_utils.nwtime2frame(key[0])
                curveX.keyframe_points.insert(frame, key[1])
                curveY.keyframe_points.insert(frame, key[2])
                curveZ.keyframe_points.insert(frame, key[3])
        elif (self.position is not None):
            curveX = action.fcurves.new(data_path='location', index=0)
            curveY = action.fcurves.new(data_path='location', index=1)
            curveZ = action.fcurves.new(data_path='location', index=2)
            curveX.keyframe_points.insert(0, self.position[0])
            curveY.keyframe_points.insert(0, self.position[1])
            curveZ.keyframe_points.insert(0, self.position[2])

        # Set scale channels if there are scale keys
        if (self.keys.scale):
            curveX = action.fcurves.new(data_path='scale', index=0)
            curveY = action.fcurves.new(data_path='scale', index=1)
            curveZ = action.fcurves.new(data_path='scale', index=2)
            for key in self.keys.scale:
                frame = nvb_utils.nwtime2frame(key[0])
                curveX.keyframe_points.insert(frame, key[1])
                curveY.keyframe_points.insert(frame, key[1])
                curveZ.keyframe_points.insert(frame, key[1])
        elif (self.scale is not None):
            curveX = action.fcurves.new(data_path='scale', index=0)
            curveY = action.fcurves.new(data_path='scale', index=1)
            curveZ = action.fcurves.new(data_path='scale', index=2)
            curveX.keyframe_points.insert(0, self.scale)
            curveY.keyframe_points.insert(0, self.scale)
            curveZ.keyframe_points.insert(0, self.scale)

        # Set selfillumcolor channels if there are selfillumcolor keys
        if (self.keys.selfillumcolor):
            curveR = action.fcurves.new(data_path='nvb.selfillumcolor', index=0)
            curveG = action.fcurves.new(data_path='nvb.selfillumcolor', index=1)
            curveB = action.fcurves.new(data_path='nvb.selfillumcolor', index=2)

            for key in self.keys.selfillumcolor:
                frame = nvb_utils.nwtime2frame(key[0])
                curveR.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[1])
                curveG.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[2])
                curveB.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[3])

        # For lamps: Set color channels
        if (self.keys.color):
            curveR = action.fcurves.new(data_path='color', index=0)
            curveG = action.fcurves.new(data_path='color', index=1)
            curveB = action.fcurves.new(data_path='color', index=2)

            for key in self.keys.color:
                frame = nvb_utils.nwtime2frame(key[0])
                curveR.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[1])
                curveG.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[2])
                curveB.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[3])

        # For lamps: Set radius channels. Import as distance
        if (self.keys.radius):
            curve = action.fcurves.new(data_path='distance', index=0)
            for key in self.keys.radius:
                frame = nvb_utils.nwtime2frame(key[0])
                curve.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[1])

        # Add imcompatible animations (emitters) as a text object
        if (self.keys.rawascii):
            txt = bpy.data.texts.new(targetObject.name)
            txt.write(self.keys.rawascii)
            targetObject.nvb.rawascii = txt.name

        # For Materials: Add animation for materials (only alpha atm)
        if targetObject.active_material:
            self.addAnimToMaterial(targetObject.active_material, animName)

        targetObject.animation_data_create()
        targetObject.animation_data.action = action


    def getKeysFromAction(self, action, keyDict):
            for fcurve in action.fcurves:
                # Get the sub dict for this particlar type of fcurve
                axis     = fcurve.array_index
                dataPath = fcurve.data_path
                name     = ''
                #print(dataPath)
                if   dataPath == 'rotation_euler':
                    name = 'orientationkey'
                elif dataPath == 'rotation_axis_angle':
                    pass
                elif dataPath == 'location':
                    name = 'positionkey'
                elif dataPath == 'scale':
                    name = 'scalekey'
                elif dataPath == 'nvb.selfillumcolor':
                    name = 'selfillumcolorkey'
                elif dataPath == 'color': # Lamps/Lights
                    name = 'colorkey'
                elif dataPath == 'distance': # Lamps/Lights
                    name = 'radiuskey'
                elif dataPath.endswith('alpha_factor'): # Texture alpha_factor
                    name = 'alphakey'
                elif dataPath.endswith('alpha'): # Material alpha
                    name = 'alphakey'

                for kfp in fcurve.keyframe_points:
                    frame = int(round(kfp.co[0]))
                    keys  = keyDict[name]
                    if frame in keys:
                        values = keys[frame]
                    else:
                        values = [0.0, 0.0, 0.0, 0.0]
                    values[axis] = values[axis] + kfp.co[1]
                    keys[frame] = values


    def addKeysToAsciiIncompat(self, obj, asciiLines):
        if obj.nvb.meshtype != nvb_def.Meshtype.EMITTER:
            return
        if obj.nvb.rawascii not in bpy.data.texts:
            return
        txt      = bpy.data.texts[obj.nvb.rawascii]
        txtLines = [l.split() for l in txt.as_string().split('\n')]
        for line in txtLines:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if  (label == 'node') or (label  == 'endnode') or \
                (label == 'parent') or (label == 'position'):
                # We don't need any of this
                pass
            else:
                # We'll take everything that doesn't start with a #
                if label[0] != '#':
                    if nvb_utils.isNumber(label):
                        asciiLines.append('      ' + ' '.join(line))
                    else:
                        asciiLines.append('    ' + ' '.join(line))


    def addKeysToAscii(self, animObj, originalObj, asciiLines):
        keyDict =  {'orientationkey'    : collections.OrderedDict(), \
                    'positionkey'       : collections.OrderedDict(), \
                    'scalekey'          : collections.OrderedDict(), \
                    'selfillumcolorkey' : collections.OrderedDict(), \
                    'colorkey'          : collections.OrderedDict(), \
                    'radiuskey'         : collections.OrderedDict(), \
                    'alphakey'          : collections.OrderedDict() }

        # Object Data
        if animObj.animation_data:
            action = animObj.animation_data.action
            if action:
                self.getKeysFromAction(action, keyDict)

        # Material/ texture data (= texture alpha_factor)
        if animObj.active_material and animObj.active_material.animation_data:
            action = animObj.active_material.animation_data.action
            if action:
                self.getKeysFromAction(action, keyDict)

        l_str   = str
        l_round = round

        name = 'orientationkey'
        if   len(keyDict[name]) > 1:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                eul = mathutils.Euler((key[0], key[1], key[2]), 'XYZ')
                val = nvb_utils.euler2nwangle(eul)
                s = '      {: 6.5f} {: 6.5f} {: 6.5f} {: 6.5f} {: 6.5f}'.format(time, val[0], val[1], val[2], val[3])
                asciiLines.append(s)
        elif len(keyDict[name]) == 1:
            # Only a single key
            frame, key = keyDict[name].popitem()
            eul = mathutils.Euler((key[0], key[1], key[2]), 'XYZ')
            val = nvb_utils.euler2nwangle(eul)
            s = '    orientation {: 8.5f} {: 8.5f} {: 8.5f} {: 8.5f}'.format(val[0], val[1], val[2], val[3])
            asciiLines.append(s)

        name = 'positionkey'
        if len(keyDict[name]) > 1:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 6.5f} {: 6.5f} {: 6.5f}'.format(time, key[0], key[1], key[2])
                asciiLines.append(s)
        elif len(keyDict[name]) == 1:
            # Only a single key
            frame, key = keyDict[name].popitem()
            s = '    position {: 8.5f} {: 8.5f} {: 8.5f}'.format(key[0], key[1], key[2])
            asciiLines.append(s)


        name = 'scalekey'
        if keyDict[name]:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 6.5f}'.format(time, key[0])
                asciiLines.append(s)

        name = 'selfillumcolorkey'
        if keyDict[name]:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 3.2f} {: 3.2f} {: 3.2f}'.format(time, key[0], key[1], key[2])
                asciiLines.append(s)

        name = 'colorkey'
        if keyDict[name]:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 3.2f} {: 3.2f} {: 3.2f}'.format(time, key[0], key[1], key[2])
                asciiLines.append(s)

        name = 'radiuskey'
        if keyDict[name]:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 6.5f}'.format(time, key[0])
                asciiLines.append(s)

        name = 'alphakey'
        if len(keyDict[name]) > 1:
            asciiLines.append('    ' + name + ' ' + l_str(len(keyDict[name])))
            for frame, key in keyDict[name].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                s = '      {: 6.5f} {: 3.2f}'.format(time, key[0])
                asciiLines.append(s)
        elif len(keyDict[name]) == 1:
            # Only a single key
            frame, key = keyDict[name].popitem()
            s = '    alpha {: 3.2f}'.format(key[0])
            asciiLines.append(s)


    def getOriginalName(self, nodeName, animName):
        '''
        A bit messy due to compatibility concerns
        '''
        if nodeName.endswith(animName):
            orig = nodeName[:len(nodeName)-len(animName)]
            if orig.endswith('.'):
                orig = orig[:len(orig)-1]
            return orig

        # Try to separate the name by the first '.'
        # This is unsafe, but we have no choice if we want to maintain some
        # flexibility. It will be up to the user to name the object properly
        orig = nodeName.partition('.')[0]
        if orig:
            return orig

        # Couldn't find anything ? Return the string itself
        return nodeName


    def toAscii(self, animObj, asciiLines, animName):
        originalName = self.getOriginalName(animObj.name, animName)
        originalObj  = bpy.data.objects[originalName]

        originalParent = nvb_def.null
        if animObj.parent:
            originalParent = self.getOriginalName(animObj.parent.name, animName)

        if originalObj.nvb.meshtype == nvb_def.Meshtype.EMITTER:
            asciiLines.append('  node emitter ' + originalName)
            asciiLines.append('    parent ' + originalParent)
            self.addKeysToAsciiIncompat(animObj, asciiLines)
        else:
            asciiLines.append('  node dummy ' + originalName)
            asciiLines.append('    parent ' + originalParent)
        self.addKeysToAscii(animObj, originalObj, asciiLines)
        asciiLines.append('  endnode')
