"""TODO: DOC."""

import mathutils
import collections
import bpy
import re
from math import sqrt,asin,cos

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
        # Emitters
        self.alphastart = []
        self.alphamid = []
        self.alphaend = []
        self.birthrate = []
        self.m_frandombirthrate = []
        self.bounce_co = []
        self.combinetime = []
        self.drag = []
        self.fps = []
        self.frameend = []
        self.framestart = []
        self.grav = []
        self.lifeexp = []
        self.mass = []
        self.p2p_bezier2 = []
        self.p2p_bezier3 = []
        self.particlerot = []
        self.randvel = []
        self.sizestart = []
        self.sizemid = []
        self.sizeend = []
        self.sizestart_y = []
        self.sizemid_y = []
        self.sizeend_y = []
        self.spread = []
        self.threshold = []
        self.velocity = []
        self.xsize = []
        self.ysize = []
        self.blurlength = []
        self.lightningdelay = []
        self.lightningradius = []
        self.lightningsubdiv = []
        self.lightningscale = []
        self.lightningzigzag = []
        self.percentstart = []
        self.percentmid = []
        self.percentend = []
        self.targetsize = []
        self.numcontrolpts = []
        self.controlptradius = []
        self.controlptdelay = []
        self.tangentspread = []
        self.tangentlength = []
        self.colorstart = []
        self.colormid = []
        self.colorend = []
        # Unknown. Import as text
        self.rawascii = ''

    def hasAlpha(self):
        return len(self.alpha) > 0


class Node():
    KEY_TYPE = {
        'position': {
            'values': 3,
            'axes': 3,
            'objdata': 'location',
            },
        'orientation': {
            'values': 4,
            'axes': 3,
            'objdata': 'rotation_euler',
            },
        'scale': {
            'values': 1,
            'axes': 3,
            'objdata': 'scale',
            },
        'alpha': {
            'values': 1,
            'axes': 1,
            'objdata': None,
            },
        'selfillumcolor': {
            'values': 3,
            'axes': 3,
            'objdata': 'nvb.selfillumcolor',
            },
        'color': {
            'values': 3,
            'axes': 3,
            'objdata': 'color',
            },
        'radius': {
            'values': 1,
            'axes': 1,
            'objdata': 'distance',
            },
        }
    EMITTER_KEY_TYPE = {
        "alphaStart": {
            "values": 1,
            "axes": 1,
        },
        "alphaMid": {
            "values": 1,
            "axes": 1,
        },
        "alphaEnd": {
            "values": 1,
            "axes": 1,
        },
        "birthrate": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "m_fRandomBirthRate": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "bounce_co": {
            "values": 1,
            "axes": 1,
        },
        "combinetime": {
            "values": 1,
            "axes": 1,
        },
        "drag": {
            "values": 1,
            "axes": 1,
        },
        "fps": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "frameEnd": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "frameStart": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "grav": {
            "values": 1,
            "axes": 1,
        },
        "lifeExp": {
            "values": 1,
            "axes": 1,
        },
        "mass": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier2": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier3": {
            "values": 1,
            "axes": 1,
        },
        "particleRot": {
            "values": 1,
            "axes": 1,
        },
        "randvel": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd_y": {
            "values": 1,
            "axes": 1,
        },
        "spread": {
            "values": 1,
            "axes": 1,
        },
        "threshold": {
            "values": 1,
            "axes": 1,
        },
        "velocity": {
            "values": 1,
            "axes": 1,
        },
        "xsize": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "ysize": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "blurlength": {
            "values": 1,
            "axes": 1,
        },
        "lightningDelay": {
            "values": 1,
            "axes": 1,
        },
        "lightningRadius": {
            "values": 1,
            "axes": 1,
        },
        "lightningSubDiv": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "lightningScale": {
            "values": 1,
            "axes": 1,
        },
        "lightningzigzag": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "percentStart": {
            "values": 1,
            "axes": 1,
        },
        "percentMid": {
            "values": 1,
            "axes": 1,
        },
        "percentEnd": {
            "values": 1,
            "axes": 1,
        },
        "targetsize": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "numcontrolpts": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "controlptradius": {
            "values": 1,
            "axes": 1,
        },
        "controlptdelay": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "tangentspread": {
            "values": 1,
            "axes": 1,
            "conversion":int,
        },
        "tangentlength": {
            "values": 1,
            "axes": 1,
        },
        "colorStart": {
            "values": 3,
            "axes": 3,
        },
        "colorMid": {
            "values": 3,
            "axes": 3,
        },
        "colorEnd": {
            "values": 3,
            "axes": 3,
        },
    }

    def __init__(self, name = 'UNNAMED'):
        self.name       = name
        self.nodetype   = 'dummy'
        self.parentName = nvb_def.null

        # Keyed
        self.keys = Keys()

        self.isEmpty = True

    def __bool__(self):
        '''
        Return false if the node is empty, i.e. it has no anims attached
        '''
        return not self.isEmpty

    def requiresUniqueData(self):
        return self.keys.hasAlpha()

    def parseKeys9f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 9 floats (not counting the time value)
        '''
        nvb_parse._f(asciiBlock, keyList, 10)
        self.isEmpty = False

    def parseKeys3f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 3 floats (not counting the time value)
        '''
        nvb_parse.f4(asciiBlock, keyList)
        self.isEmpty = False


    def parseKeys4f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 4 floats (not counting the time value)
        '''
        nvb_parse.f5(asciiBlock, keyList)
        self.isEmpty = False


    def parseKeys1f(self, asciiBlock, keyList):
        '''
        Parse animation keys containing 1 float (not counting the time value)
        '''
        nvb_parse.f2(asciiBlock, keyList)
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
        return next((i for i, v in enumerate(asciiBlock) if len(v) and not l_isNumber(v[0])), -1)

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
            elif label in self.KEY_TYPE.keys() or \
                 label in (attr + 'key' for attr in self.KEY_TYPE.keys()) or \
                 label in (attr + 'bezierkey' for attr in self.KEY_TYPE.keys()):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = [attr for attr in self.KEY_TYPE.keys() if label.startswith(attr)][0]
                attr_type = self.KEY_TYPE[attrname]
                key_type = ''
                key_type = 'key' if label.endswith('key') else key_type
                key_type = 'bezierkey' if label.endswith('bezierkey') else key_type
                #print('found {}{} {:d} values'.format(attrname, key_type, attr_type['values']))
                numVals = attr_type['values']
                if key_type:
                    if key_type == 'bezierkey':
                        numVals *= 3
                    numKeys = self.findEnd(asciiBlock[idx+1:])
                    subblock = asciiBlock[idx+1:idx+numKeys+1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                nvb_parse._f(subblock, getattr(self.keys, attrname), numVals + 1)
                self.isEmpty = False
            elif label in (attr.lower() for attr in self.EMITTER_KEY_TYPE.keys()) or \
                 label in (attr.lower() + 'key' for attr in self.EMITTER_KEY_TYPE.keys()) or \
                 label in (attr.lower() + 'bezierkey' for attr in self.EMITTER_KEY_TYPE.keys()):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = [attr for attr in self.EMITTER_KEY_TYPE.keys() if attr.lower() in label][0]
                propname = attrname.lower()
                attr_type = self.EMITTER_KEY_TYPE[attrname]
                key_type = ''
                key_type = 'key' if label.endswith('key') else key_type
                key_type = 'bezierkey' if label.endswith('bezierkey') else key_type
                #print('found {}{} {:d} values'.format(attrname, key_type, attr_type['values']))
                numVals = attr_type['values']
                if key_type:
                    if key_type == 'bezierkey':
                        numVals *= 3
                    numKeys = self.findEnd(asciiBlock[idx+1:])
                    subblock = asciiBlock[idx+1:idx+numKeys+1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                if 'conversion' in attr_type and attr_type['conversion'] is int:
                    nvb_parse._i(subblock, getattr(self.keys, propname), numVals + 1)
                    #print(getattr(self.keys, attrname))
                else:
                    nvb_parse._f(subblock, getattr(self.keys, propname), numVals + 1)
                #print(attrname + ' ' + label)
                self.isEmpty = False
            # Some unknown text.
            # Probably keys for emitters = incompatible with blender. Import as text.
            elif not l_isNumber(line[0]):
                numKeys = self.findEnd(asciiBlock[idx+1:])
                if numKeys:
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
            for index, key in enumerate(self.keys.alpha):
                self.addKeyframeToCurve(curve, self.keys.alpha, index, 1, 1)
                #curve.keyframe_points.insert(nvb_utils.nwtime2frame(key[0]), key[1])
        elif self.alpha is not None:
            curve.keyframe_points.insert(0, self.alpha)

        targetMaterial.animation_data_create()
        targetMaterial.animation_data.action = action


    def addKeyframeToCurve(self, curve, key_coll, key_idx, value_idx, num_values):
        '''
        Add Keyframe to animation F-Curve, in bezier or linear style
        '''
        key = key_coll[key_idx]
        frame = nvb_utils.nwtime2frame(key[0])
        kfp = curve.keyframe_points.insert(frame, key[value_idx])
        kfp.interpolation = 'LINEAR'
        if len(key) > num_values + 1:
            kfp.interpolation = 'BEZIER'
            kfp.handle_left_type = 'FREE'
            kfp.handle_right_type = 'FREE'
            if key_idx > 0 and len(key_coll):
                prevframe = nvb_utils.nwtime2frame(key_coll[key_idx - 1][0])
                cp1frame = frame - ((frame - prevframe) / 3.0)
                kfp.handle_left[:] = [ cp1frame, key[value_idx + num_values] + key[value_idx] ]
            if key_idx < len(key_coll) - 1:
                nextframe = nvb_utils.nwtime2frame(key_coll[key_idx + 1][0])
                cp2frame = frame + ((nextframe - frame) / 3.0)
                kfp.handle_right[:] = [ cp2frame, key[value_idx + (2 * num_values)] + key[value_idx] ]


    def addAnimToObject(self, targetObject, animName = ''):
        '''
        Add the animations in this node to target object
        '''
        #actionName           = animName + '.' + targetObject.name
        actionName           = targetObject.name
        action               = bpy.data.actions.new(name=actionName)
        action.use_fake_user = True

        # test for all key types, if present, create timelines for them
        for attrname in self.KEY_TYPE.keys():
            if not getattr(self.keys, attrname) or \
               not self.KEY_TYPE[attrname]['objdata']:
                continue
            key_type = self.KEY_TYPE[attrname]
            curves = []
            # one fcurve per 'axis' (xyz, rgb, etc.)
            for x in range(0, key_type['axes']):
                curves.append(action.fcurves.new(data_path=key_type['objdata'], index=x))
            if attrname == 'orientation':
                currEul = None
                prevEul = None
                eulVals = []
            # handle each keyframe
            for index, key in enumerate(getattr(self.keys, attrname)):
                frame = nvb_utils.nwtime2frame(key[0])
                if attrname == 'orientation':
                    # orientation is special
                    eul   = nvb_utils.nwangle2euler(key[1:5])
                    currEul = nvb_utils.eulerFilter(eul, prevEul)
                    prevEul = currEul
                    kfs = []
                    for x in range(0, key_type['axes']):
                        kfs.append(curves[x].keyframe_points.insert(frame, currEul[x]))
                        kfs[x].interpolation = 'LINEAR'
                else:
                    # handle each axis, matching values to curves
                    for x in range(0, key_type['axes']):
                        # handle key/bezierkey for all types in addKeyframeToCurve
                        self.addKeyframeToCurve(
                            curves[x], getattr(self.keys, attrname), index,
                            min(x + 1, key_type['values']), key_type['values'])
        # test for all key types, if present, create timelines for them
        for attrname in self.EMITTER_KEY_TYPE.keys():
            propname = attrname.lower()
            if not getattr(self.keys, propname):
                continue
            #print('emitter ' + propname)
            key_type = self.EMITTER_KEY_TYPE[attrname]
            curves = []
            # one fcurve per 'axis' (xyz, rgb, etc.)
            for x in range(0, key_type['axes']):
                curves.append(action.fcurves.new(data_path='nvb.' + propname, index=x))
            # handle each keyframe
            for index, key in enumerate(getattr(self.keys, propname)):
                frame = nvb_utils.nwtime2frame(key[0])
                # handle each axis, matching values to curves
                for x in range(0, key_type['axes']):
                    # handle key/bezierkey for all types in addKeyframeToCurve
                    self.addKeyframeToCurve(
                        curves[x], getattr(self.keys, propname), index,
                        min(x + 1, key_type['values']), key_type['values'])

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
                # handle material property alpha separately
                if dataPath.endswith('alpha_factor') or \
                   dataPath.endswith('alpha'):
                    name = 'alphakey'
                    ktype = self.KEY_TYPE['alpha']
                for keyname in self.KEY_TYPE.keys():
                    ktype = self.KEY_TYPE[keyname]
                    if ktype['objdata'] is not None and \
                       dataPath == ktype['objdata']:
                        name = keyname + 'key'
                        break
                for keyname in self.EMITTER_KEY_TYPE.keys():
                    if dataPath == 'nvb.' + keyname.lower():
                        ktype = self.EMITTER_KEY_TYPE[keyname]
                        name = keyname + 'key'
                        break

                for kfp in fcurve.keyframe_points:
                    if name.startswith('orientation'):
                        # bezier keyed orientation animation currently unsupported
                        break
                    if kfp.interpolation == 'BEZIER':
                        name = re.sub(r'^(.+)key$', r'\1bezierkey', name)
                        break

                for kfkey, kfp in enumerate(fcurve.keyframe_points):
                    frame = int(round(kfp.co[0]))
                    if name not in keyDict:
                        keyDict[name] = collections.OrderedDict()
                    keys  = keyDict[name]
                    if frame in keys:
                        values = keys[frame]
                    else:
                        values = [0.0, 0.0, 0.0, 0.0]
                    values[axis] = values[axis] + kfp.co[1]
                    #print(values)
                    if name.endswith('bezierkey'):
                        if kfp.interpolation == 'BEZIER':
                            values[ktype['axes'] + (axis * 2):(ktype['axes'] + 1) + (axis * 2)] = \
                                [ kfp.handle_left[1] - kfp.co[1], kfp.handle_right[1] - kfp.co[1] ]
                        elif kfp.interpolation == 'LINEAR':
                            # do the linear emulation,
                            # distance between keyframes / 3 point on linear interpolation @ frame
                            # y = y0 + ((x - x0) * ((y1 - y0)/(x1 - x0)))
                            # right handle is on the segment controlled by this keyframe
                            if kfkey < len(fcurve.keyframe_points) - 1:
                                next_kfp = fcurve.keyframe_points[kfkey + 1]
                                next_frame = int(round((next_kfp.co[0] - kfp.co[0]) / 3.0))
                                right_handle = kfp.co[1] + ((next_frame - frame) * ((next_kfp.co[1] - kfp.co[1]) / (next_kfp.co[0] - kfp.co[0])))
                                # make exported right handle value relative to keyframe value:
                                right_handle = right_handle - kfp.co[1]
                            else:
                                right_handle = 0.0
                            # left handle is on the segment controlled by the previous keyframe
                            if kfkey > 0 and fcurve.keyframe_points[kfkey - 1].interpolation == 'LINEAR':
                                prev_kfp = fcurve.keyframe_points[kfkey - 1]
                                prev_frame = int(round((kfp.co[0] - prev_kfp.co[0]) / 3.0))
                                left_handle = prev_kfp.co[1] + ((prev_frame - prev_kfp.co[0]) * ((kfp.co[1] - prev_kfp.co[1]) / (kfp.co[0] - prev_kfp.co[0])))
                                # make exported left handle value relative to keyframe value:
                                left_handle = left_handle - kfp.co[1]
                            elif kfkey > 0 and kfp.handle_left and kfp.handle_left[1]:
                                left_handle = kfp.handle_left[1] - kfp.co[1]
                            else:
                                left_handle = 0.0
                            values[ktype['axes'] + (axis * 2):(ktype['axes'] + 1) + (axis * 2)] = \
                                [ left_handle, right_handle ]
                        else:
                            # somebody mixed an unknown keyframe type ...
                            # give them some bad data
                            values[ktype['axes'] + (axis * 2):(ktype['axes'] + 1) + (axis * 2)] = [ 0.0, 0.0 ]
                            #values.extend([ 0.0, 0.0 ])
                    keys[frame] = values


    def addKeysToAsciiIncompat(self, obj, asciiLines):
        #if obj.nvb.meshtype != nvb_def.Meshtype.EMITTER:
        #    return
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
        keyDict = {}

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

        for attrname in self.KEY_TYPE.keys():
            bezname = attrname + 'bezierkey'
            keyname = attrname + 'key'
            if (bezname not in keyDict or not len(keyDict[bezname])) and \
               (keyname not in keyDict or not len(keyDict[keyname])):
                continue
            ktype = self.KEY_TYPE[attrname]
            # using a bezierkey
            if bezname in keyDict and len(keyDict[bezname]):
                keyname = bezname
            asciiLines.append('    {} {}'.format(keyname, l_str(len(keyDict[keyname]))))
            for frame, key in keyDict[keyname].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                # orientation value conversion
                if keyname.startswith('orientation'):
                    key = nvb_utils.euler2nwangle(mathutils.Euler((key[0:3]), 'XYZ'))
                # export title and
                line = '      {: .7g}' + (' {: .7g}' * ktype['values'])
                s = line.format(time, *key[0:ktype['values']])
                # export bezierkey control points
                if keyname == bezname:
                    # left control point(s)
                    s += (' {: .7g}' * ktype['values']).format(*key[ktype['axes']::2])
                    # right control point(s)
                    s += (' {: .7g}' * ktype['values']).format(*key[ktype['axes'] + 1::2])
                asciiLines.append(s)
        for attrname in self.EMITTER_KEY_TYPE.keys():
            bezname = attrname + 'bezierkey'
            keyname = attrname + 'key'
            if (bezname not in keyDict or not len(keyDict[bezname])) and \
               (keyname not in keyDict or not len(keyDict[keyname])):
                continue
            ktype = self.EMITTER_KEY_TYPE[attrname]
            # using a bezierkey
            if bezname in keyDict and len(keyDict[bezname]):
                keyname = bezname
            asciiLines.append('    {} {}'.format(keyname, l_str(len(keyDict[keyname]))))
            for frame, key in keyDict[keyname].items():
                time = l_round(nvb_utils.frame2nwtime(frame), 5)
                # orientation value conversion
                # export title and
                value_str = " {: .7g}"
                if "conversion" in ktype and ktype["conversion"] is int:
                    #print(attrname)
                    #print(key)
                    #print(ktype)
                    value_str = " {: d}"
                    key[0:ktype['values']] = [int(k) for k in key[0:ktype['values']]]
                    #print('converted')
                    #print(key)
                line = '      {: .7g}' + (value_str * ktype['values'])
                s = line.format(time, *key[0:ktype['values']])
                # export bezierkey control points
                if keyname == bezname:
                    # left control point(s)
                    s += (' {: .7g}' * ktype['values']).format(*key[ktype['axes']::2])
                    # right control point(s)
                    s += (' {: .7g}' * ktype['values']).format(*key[ktype['axes'] + 1::2])
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

    def exportNeeded(self, animObj):
        '''
        Test whether this node should be included in exported ASCII model
        '''
        # this is the root node, must be included
        if animObj.parent is None:
            return True
        # this node has animation controllers, include it
        if ((animObj.animation_data and \
             animObj.animation_data.action and \
             animObj.animation_data.action.fcurves and \
             len(animObj.animation_data.action.fcurves) > 0) or \
            (animObj.active_material and \
             animObj.active_material.animation_data and \
             animObj.active_material.animation_data.action and \
             animObj.active_material.animation_data.action.fcurves and \
             len(animObj.active_material.animation_data.action.fcurves) > 0)):
            return True
        # if any children of this node will be included, this node must be
        for child in animObj.children:
            if self.exportNeeded(child):
                return True
        # no reason to include this node
        return False

    def toAscii(self, animObj, asciiLines, animName):
        originalName = self.getOriginalName(animObj.name, animName)
        originalObj  = bpy.data.objects[originalName]

        # test whether this node should be exported,
        # previous behavior was to export all nodes for all animations
        if not self.exportNeeded(animObj):
            return

        originalParent = nvb_def.null
        if animObj.parent:
            originalParent = self.getOriginalName(animObj.parent.name, animName)

        if originalObj.nvb.meshtype == nvb_def.Meshtype.EMITTER:
            asciiLines.append('  node emitter ' + originalName)
            asciiLines.append('    parent ' + originalParent)
            #self.addKeysToAsciiIncompat(animObj, asciiLines)
        else:
            asciiLines.append('  node dummy ' + originalName)
            asciiLines.append('    parent ' + originalParent)
        self.addKeysToAscii(animObj, originalObj, asciiLines)
        self.addKeysToAsciiIncompat(animObj, asciiLines)
        asciiLines.append('  endnode')
