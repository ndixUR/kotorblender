"""TODO: DOC."""
import os
import collections
import enum
from datetime import datetime

import bpy

from . import nvb_node
from . import nvb_anim
from . import nvb_glob
from . import nvb_def
from . import nvb_utils


class Mdl():
    def __init__(self):
        self.nodeDict      = collections.OrderedDict()
        self.animDict      = dict() # No need to retain order

        self.name           = 'UNNAMED'
        self.supermodel     = nvb_def.null
        self.animscale      = 1.0
        self.classification = nvb_def.Classification.UNKNOWN
        self.unknownC1      = 0
        self.ignorefog      = False
        self.compress_quats = False
        self.headlink       = False

        self.validExports   = [] # needed for skinmeshes and animations


    def loadAsciiNode(self, asciiBlock):
        if asciiBlock is None:
            raise nvb_def.MalformedMdlFile('Empty Node')

        nodeType = ''
        try:
            nodeType = asciiBlock[0][1].lower()
        except (IndexError, AttributeError):
            raise nvb_def.MalformedMdlFile('Invalid node type')

        switch = {'dummy':      nvb_node.Dummy,
                  'patch':      nvb_node.Patch,
                  'reference':  nvb_node.Reference,
                  'trimesh':    nvb_node.Trimesh,
                  'danglymesh': nvb_node.Danglymesh,
                  'lightsaber': nvb_node.Lightsaber,
                  'skin':       nvb_node.Skinmesh,
                  'emitter':    nvb_node.Emitter,
                  'light':      nvb_node.Light,
                  'aabb':       nvb_node.Aabb}
        try:
            node = switch[nodeType]()
        except KeyError:
            raise nvb_def.MalformedMdlFile('Invalid node type')

        # tell the node if it is part of a walkmesh (mdl is default)
        if isinstance(self, Xwk):
            node.roottype = self.walkmeshType

        # tell the node what model it is part of
        node.rootname = self.name

        node.loadAscii(asciiBlock)
        self.addNode(node)

    def loadAsciiAnimation(self, asciiBlock):
        if asciiBlock is None:
            raise nvb_def.MalformedMdlFile('Empty Animation')

        animation = nvb_anim.Animation()
        animation.getAnimFromAscii(asciiBlock)

        self.addAnimation(animation)

    def addNode(self, newNode):
        # Blender requires unique object names. Names in mdls are only
        # unique for a parent, i.e. another object with the same name but
        # with a different parent may exist.
        # We'd need to save all names starting from root to resolve
        # this, but that's too much effort.
        # ParentName + Name should be enough.
        if newNode:
            key = newNode.parentName + newNode.name
            if key in self.nodeDict:
                print('Kotorblender - WARNING: Node name conflict ' + key + '.')
            else:
                self.nodeDict[key] = newNode

    def addAnimation(self, anim):
        if anim:
            if anim.name in self.animDict:
                print('Kotorblender - WARNING: Animation name conflict.')
            else:
                self.animDict[anim.name] = anim

    def importToScene(self, scene, wkm):
        rootDummy = None
        objIdx = 0
        if (nvb_glob.importGeometry) and self.nodeDict:
            it = iter(self.nodeDict.items())

            # The first node should be the rootdummy.
            # If the first node has a parent or isn't a dummy we don't
            # even try to import the mdl
            (nodeKey, node) = next(it)
            if (type(node) == nvb_node.Dummy) and (nvb_utils.isNull(node.parentName)):
                obj                = node.addToScene(scene)
                obj.nvb.dummytype      = nvb_def.Dummytype.MDLROOT
                obj.nvb.supermodel     = self.supermodel
                obj.nvb.classification = self.classification
                obj.nvb.unknownC1      = self.unknownC1
                obj.nvb.ignorefog      = (self.ignorefog >= 1)
                obj.nvb.compress_quats = (self.compress_quats >= 1)
                obj.nvb.headlink       = (self.headlink >= 1)
                rootDummy = obj

                obj.nvb.imporder = objIdx
                objIdx += 1
            else:
                raise nvb_def.MalformedMdlFile('First node has to be a dummy without a parent.')

            for (nodeKey, node) in it:
                obj = node.addToScene(scene)
                obj.nvb.imporder = objIdx
                objIdx += 1
                if (nvb_utils.isNull(node.parentName)):
                    # Node without parent and not the mdl root.
                    raise nvb_def.MalformedMdlFile(node.name + ' has no parent.')
                else:
                    # Check if such an object exists
                    if obj.parent is not None:
                        print("WARNING: Node already parented: {}".format(obj.name))
                        pass
                    elif node.parentName in bpy.data.objects and \
                         nvb_utils.ancestorNode(bpy.data.objects[node.parentName],
                                                nvb_utils.isRootDummy).name == self.name:
                        # parent named node exists and is under a root dummy
                        # that shares our model's name, so use it.
                        obj.parent = bpy.data.objects[node.parentName]
                        if node.parentName != self.name:
                            # child of non-root, preserve orientation
                            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
                    else:
                        found = False
                        for altname in [node.parentName + '.{:03d}'.format(i) for i in range(1,20)]:
                            if altname in bpy.data.objects and \
                               nvb_utils.ancestorNode(bpy.data.objects[altname],
                                                      nvb_utils.isRootDummy).name == self.name:
                                # parent named node exists with suffix
                                # shares mdl root dummy name, so use it.
                                obj.parent = bpy.data.objects[altname]
                                obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
                                found = True
                                break
                        # Node with invalid parent.
                        if not found:
                            raise nvb_def.MalformedMdlFile(node.name + ' has no parent ' + node.parentName)

        # Import the walkmesh, it will use any placeholder dummies just imported,
        # and the walkmesh nodes will be copied during animation import
        if (nvb_glob.importWalkmesh) and not wkm is None and wkm.walkmeshType != 'wok':
            wkm.importToScene(scene)

        # Attempt to import animations
        # Search for the rootDummy if not already present
        if not rootDummy:
            for obj in scene.objects:
                if nvb_utils.isRootDummy(obj, nvb_def.Dummytype.MDLROOT):
                    rootDummy = obj
                    break
            # Still none ? Don't try to import anims then
            if not rootDummy:
                return

        for (animName, anim) in self.animDict.items():
            anim.addAnimToScene(scene, rootDummy)

    def loadAscii(self, asciiLines):
        State = enum.Enum('State', 'START HEADER GEOMETRY GEOMETRYNODE ANIMATION')
        cs    = State.START
        blockStart = -1
        for idx, line in enumerate(asciiLines):
            try:
                label = line[0]
            except IndexError:
                # Probably empty line or whatever, just skip it
                continue

            if (cs == State.START):
                if (label == 'newmodel'):
                    try:
                        self.name = line[1]
                    except IndexError:
                        raise nvb_def.MalformedMdlFile('Model has no name')
                    cs = State.HEADER

            elif (cs == State.HEADER):
                if (label == 'beginmodelgeom'):
                    # After this, a list of nodes has to follow
                    cs = State.GEOMETRY
                elif (label == 'setsupermodel'):
                    try:
                        # line should be ['setsupermodel', modelname, supermodelname]
                        self.supermodel = line[2]
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read supermodel. Default value " + self.supermodel)

                elif (label == 'classification'):
                    try:
                        self.classification = line[1].title()
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read classification. Default value " + self.classification)

                    if self.classification not in nvb_def.Classification.ALL:
                        print("Kotorblender - WARNING: Invalid classification '" + self.classification + "'")
                        self.classification = nvb_def.Classification.UNKNOWN
                elif (label == 'classification_unk1'):
                    try:
                        self.unknownC1 = int(line[1])
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read classification unknown. Default value " + self.unknownC1)
                elif (label == 'ignorefog'):
                    try:
                        self.ignorefog = int(line[1])
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read ignorefog. Default value " + self.ignorefog)
                elif (label == 'compress_quaternions'):
                    try:
                        self.compress_quats = int(line[1])
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read compress_quaternions. Default value " + self.compress_quats)
                elif (label == 'headlink'):
                    try:
                        self.headlink = int(line[1])
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read headlink. Default value " + self.headlink)
                elif (label == 'setanimationscale'):
                    try:
                        self.animscale = line[1]
                    except IndexError:
                        print("Kotorblender - WARNING: Unable to read animationscale. Default value " + self.animscale)

            elif (cs == State.GEOMETRY):
                if (label == 'node'):
                    blockStart = idx
                    cs = State.GEOMETRYNODE
                if (label == 'endmodelgeom'):
                    # After this, either animations or eof.
                    # Or maybe we don't want animations at all.
                    if (nvb_glob.importAnim) and (not nvb_glob.minimapMode):
                        cs = State.ANIMATION
                    else:
                        return

            elif (cs == State.GEOMETRYNODE):
                if (label == 'endnode'):
                    #node = self.parseGeometryNode(lines[blockStart:idx+1])
                    self.loadAsciiNode(asciiLines[blockStart:idx+1])
                    blockStart = -1
                    cs = State.GEOMETRY
                elif (label == 'node'):
                    raise nvb_def.MalformedMdlFile('Unexpected "endnode" at line' + str(idx))

            elif (cs == State.ANIMATION):
                if (label == 'newanim'):
                    if (blockStart < 0):
                        blockStart = idx
                    else:
                        raise nvb_def.MalformedMdlFile('Unexpected "newanim" at line' + str(idx))
                if (label == 'doneanim'):
                    if (blockStart > 0):
                        self.loadAsciiAnimation(asciiLines[blockStart:idx+1])
                        blockStart = -1
                    else:
                        raise nvb_def.MalformedMdlFile('Unexpected "doneanim" at line' + str(idx))

    def geometryToAscii(self, bObject, asciiLines, simple = False):

        nodeType = nvb_utils.getNodeType(bObject)
        switch = {'dummy':      nvb_node.Dummy,
                  'patch':      nvb_node.Patch,
                  'reference':  nvb_node.Reference,
                  'trimesh':    nvb_node.Trimesh,
                  'danglymesh': nvb_node.Danglymesh,
                  'skin':       nvb_node.Skinmesh,
                  'emitter':    nvb_node.Emitter,
                  'light':      nvb_node.Light,
                  'aabb':       nvb_node.Aabb}
        try:
            node = switch[nodeType]()
        except KeyError:
            raise nvb_def.MalformedMdlFile('Invalid node type')

        node.toAscii(bObject, asciiLines, self.validExports, self.classification, simple)

        '''
        for child in bObject.children:
            self.geometryToAscii(child, asciiLines, simple)
        '''
        childList = []
        for child in bObject.children:
            childList.append((child.nvb.imporder, child))
        childList.sort(key=lambda tup: tup[0])

        for (imporder, child) in childList:
            self.geometryToAscii(child, asciiLines, simple)

    def animationsToAscii(self, asciiLines):
        for scene in bpy.data.scenes:
            animRootDummy = nvb_utils.getAnimationRootdummy(scene)
            if animRootDummy and self.validExports:
                # Check the name of the roodummy
                # if animRootDummy.name.rfind(self.validExports[0]):
                anim = nvb_anim.Animation()
                anim.toAscii(scene, animRootDummy, asciiLines, self.name)

    def generateAscii(self, asciiLines, rootDummy, exports = {'ANIMATION', 'WALKMESH'}):
        self.name           = rootDummy.name
        self.classification = rootDummy.nvb.classification
        self.supermodel     = rootDummy.nvb.supermodel
        self.unknownC1      = rootDummy.nvb.unknownC1
        self.ignorefog      = rootDummy.nvb.ignorefog
        self.compress_quats = rootDummy.nvb.compress_quats
        self.headlink       = rootDummy.nvb.headlink
        self.animscale      = rootDummy.nvb.animscale

        # The Names of exported geometry nodes. We'll need this for skinmeshes
        # and animations
        nvb_utils.getValidExports(rootDummy, self.validExports)

        # Header
        currentTime   = datetime.now()
        blendFileName = os.path.basename(bpy.data.filepath)
        if not blendFileName:
            blendFileName = 'unknown'
        asciiLines.append('# Exported from blender at ' + currentTime.strftime('%A, %Y-%m-%d'))
        asciiLines.append('filedependancy ' + blendFileName)
        asciiLines.append('newmodel ' + self.name)
        asciiLines.append('setsupermodel ' + self.name + ' ' + self.supermodel)
        asciiLines.append('classification ' + self.classification)
        asciiLines.append('classification_unk1 ' + str(self.unknownC1))
        asciiLines.append('ignorefog ' + str(int(self.ignorefog)))
        if self.compress_quats:
            # quaternion compression does not work with the rotations we export,
            # for unknown reasons...
            # therefore, just export it as disabled for now...
            asciiLines.append('compress_quaternions 0')
            #asciiLines.append('compress_quaternions ' + str(int(self.compress_quats)))
        if self.headlink:
            asciiLines.append('headlink ' + str(int(self.headlink)))
        asciiLines.append('setanimationscale ' + str(round(self.animscale, 2)))
        #res = nvb_utils.searchNode(rootDummy, lambda o: o.active_material.active_texture.nvb.bumpmapped)
        #if res is not None:
        #    asciiLines.extend([
        #        "", "bumpmapped_texture " + res.active_material.active_texture.name, ""
        #    ])
        # Geometry
        asciiLines.append('beginmodelgeom ' + self.name)
        aabb = nvb_utils.searchNode(rootDummy, lambda x: x.nvb.meshtype == nvb_def.Meshtype.AABB)
        if aabb is not None and aabb.nvb.lytposition != (0.0, 0.0, 0.0):
            lytposition = (aabb.nvb.lytposition[0] + rootDummy.location[0], aabb.nvb.lytposition[1] + rootDummy.location[1], aabb.nvb.lytposition[2] + rootDummy.location[2])
            asciiLines.append('  layoutposition {: .7g} {: .7g} {: .7g}'.format(*lytposition))
        self.geometryToAscii(rootDummy, asciiLines, False)
        asciiLines.append('endmodelgeom ' + self.name)
        # Animations
        if 'ANIMATION' in exports:
            asciiLines.append('')
            asciiLines.append('# ANIM ASCII')
            self.animationsToAscii(asciiLines)
        # The End
        asciiLines.append('donemodel ' + self.name)
        asciiLines.append('')

class Xwk(Mdl):
    def __init__(self, wkmType = 'pwk'):
        Mdl.__init__(self)

        self.walkmeshType   = wkmType

    def loadAsciiAnimation(self, asciiBlock):
        pass # No animations in walkmeshes

    def loadAscii(self, asciiLines):
        # Parse the walkmesh
        blockStart = -1
        for idx, line in enumerate(asciiLines):
            try:
                label = line[0]
            except IndexError:
                # Probably empty line or whatever, just skip it
                continue
            if (label == 'node'):
                blockStart = idx
            elif (label == 'endnode'):
                if (blockStart >= 0):
                    self.loadAsciiNode(asciiLines[blockStart:idx+1])
                    blockStart = -1
                else:
                    # "endnode" before "node"
                    raise nvb_def.MalformedMdlFile('Unexpected "endnode" at line' + str(idx))

    def generateAscii(self, asciiLines, rootDummy, exports = {'ANIMATION', 'WALKMESH'}):
        self.name = rootDummy.name

        # Header
        currentTime = datetime.now()
        asciiLines.append('# Exported from blender at ' + currentTime.strftime('%A, %Y-%m-%d'))
        # Geometry
        for child in rootDummy.children:
            self.geometryToAscii(child, asciiLines, True)

    def importToScene(self, scene):
        if self.nodeDict:
            # Walkmeshes have no rootdummys. We need to create one ourselves
            # Unless the rootdummy is in the model already, because that happens

            # Also, kotormax puts the rootdummy into the PWK and probably DWK,
            # making this not work.
            # Even worse, it parents the use dummies to the mesh,
            # making this doubly not work.

            # Our format expectations are more like what mdlops exports,
            # which is in line with the format used in NWN.

            # Look for the node parents for the list of parents. They should
            # all have the same name
            nameList = []
            for (nodeKey, node) in self.nodeDict.items():
                if node.parentName not in nameList:
                    nameList.append(node.parentName)
            #    print(node.name)
            #    print('parent ' + node.name)
            #    if (nvb_utils.isNull(node.parentName)):
            #        # Node without
            #        raise nvb_def.MalformedMdlFile(node.name + ' has no parent.')
            #    else:
            #        if node.parentName not in nameList:
            #            nameList.append(node.parentName)
            #if len(nameList) == 1:
            #    self.name = nameList[0]
            #else:
            #    raise nvb_def.MalformedMdlFile('Invalid parents in walkmesh.')
            self.name = nameList[0]

            if self.name in scene.objects and bpy.data.objects[self.name].nvb.dummytype != nvb_def.Dummytype.MDLROOT:
                node = bpy.data.objects[self.name].nvb
                if self.walkmeshType == 'dwk':
                    node.dummytype = nvb_def.Dummytype.DWKROOT
                else:
                    node.dummytype = nvb_def.Dummytype.PWKROOT
                rootdummy = bpy.data.objects[self.name]
            else:
                #print('self ' + self.name)
                mdl_name = self.name
                wkm_name = self.name
                if not wkm_name.lower().endswith('_' + self.walkmeshType):
                    wkm_name += '_' + self.walkmeshType
                if mdl_name.lower().endswith('_' + self.walkmeshType):
                    mdl_name = mdl_name[0:-4]
                #print('wkm ' + wkm_name)
                #print('mdl ' + mdl_name)
                node = nvb_node.Dummy(wkm_name)
                if self.walkmeshType == 'dwk':
                    node.dummytype = nvb_def.Dummytype.DWKROOT
                else:
                    node.dummytype = nvb_def.Dummytype.PWKROOT
                node.name = wkm_name
                rootdummy = node.addToScene(scene)
                if mdl_name in bpy.data.objects:
                    rootdummy.parent = bpy.data.objects[mdl_name]
                else:
                    pass
                    #print(mdl_name + ' ' + wkm_name + ' ' + self.name)
            #print('root ' + rootdummy.name)
            mdlroot = nvb_utils.ancestorNode(rootdummy, lambda o: o.nvb.dummytype == nvb_def.Dummytype.MDLROOT)
            if mdlroot is None and rootdummy.parent:
                mdlroot = rootdummy.parent
            #print('mdlroot ' + mdlroot.name)
            if self.walkmeshType == 'dwk':
                dp_open1 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_dp' in o.name.lower() and o.name.lower().endswith('open1_01'))
                dp_open2 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_dp' in o.name.lower() and o.name.lower().endswith('open2_01'))
                dp_closed01 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_dp' in o.name.lower() and o.name.lower().endswith('closed_01'))
                dp_closed02 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_dp' in o.name.lower() and o.name.lower().endswith('closed_02'))
                wg_open1 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_wg' in o.name.lower() and o.name.lower().endswith('open1'))
                wg_open2 = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_wg' in o.name.lower() and o.name.lower().endswith('open2'))
                wg_closed = nvb_utils.searchNode(mdlroot, lambda o: 'dwk_wg' in o.name.lower() and o.name.lower().endswith('closed'))
            if self.walkmeshType == 'pwk':
                pwk_wg = nvb_utils.searchNode(mdlroot, lambda o: o.name.lower().endswith('_wg'))
                pwk_use01 = nvb_utils.searchNode(mdlroot, lambda o: o.name.lower().endswith('pwk_use01'))
                pwk_use02 = nvb_utils.searchNode(mdlroot, lambda o: o.name.lower().endswith('pwk_use02'))
                #if pwk_use01:
                #    print('use01 ' + pwk_use01.name)
                #if pwk_use02:
                #    print('use02 ' + pwk_use02.name)

            for (nodeKey, node) in self.nodeDict.items():
                # the node names may only be recorded in the MDL,
                # this means that the named dummy nodes already exist in-scene,
                # use these names to translate the WKM's special node names
                if 'dp_open1_01' in node.name.lower() and dp_open1:
                    node.name = dp_open1.name
                if 'dp_open2_01' in node.name.lower() and dp_open2:
                    node.name = dp_open2.name
                if 'dp_closed_01' in node.name.lower() and dp_closed01:
                    node.name = dp_closed01.name
                if 'dp_closed_02' in node.name.lower() and dp_closed02:
                    node.name = dp_closed02.name
                if 'dwk_wg_open1' in node.name.lower() and wg_open1:
                    node.name = wg_open1.name
                if 'dwk_wg_open2' in node.name.lower() and wg_open2:
                    node.name = wg_open2.name
                if 'dwk_wg_closed' in node.name.lower() and wg_closed:
                    node.name = wg_closed.name
                if node.name.lower().endswith('_wg') and pwk_wg:
                    node.name = pwk_wg.name
                if node.name.lower().endswith('pwk_use01') and pwk_use01:
                    node.name = pwk_use01.name
                if node.name.lower().endswith('pwk_use02') and pwk_use02:
                    node.name = pwk_use02.name
                # remove pre-existing nodes that were added as part of a model
                if node.name in scene.objects:
                    obj = scene.objects[node.name]
                    scene.objects.unlink(obj)
                    bpy.data.objects.remove(obj)
                obj = node.addToScene(scene)
                # Check if such an object exists
                if node.parentName in bpy.data.objects:
                    obj.parent                = bpy.data.objects[node.parentName]
                    obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
                else:
                    # Node with invalid parent.
                    raise nvb_def.MalformedMdlFile(node.name + ' has no parent ' + node.parentName)


class Wok(Xwk):
    def __init__(self, name = 'UNNAMED', wkmType = 'wok'):
        self.nodeDict       = collections.OrderedDict()
        self.name           = name
        self.walkmeshType   = 'wok'
        self.classification = nvb_def.Classification.UNKNOWN

    def geometryToAscii(self, bObject, asciiLines, simple):

        nodeType = nvb_utils.getNodeType(bObject)
        if nodeType == 'aabb':
            node = nvb_node.Aabb()
            node.roottype = 'wok'
            node.nodetype = 'trimesh'
            node.getRoomLinks(bObject.data)
            node.toAscii(bObject, asciiLines, simple)
            return  # We'll take the first aabb object
        else:
            for child in bObject.children:
                self.geometryToAscii(child, asciiLines, simple)

    def generateAscii(self, asciiLines, rootDummy, exports = {'ANIMATION', 'WALKMESH'}):
        self.name = rootDummy.name

        # Header
        currentTime   = datetime.now()
        asciiLines.append('# Exported from blender at ' + currentTime.strftime('%A, %Y-%m-%d'))
        # Geometry = AABB
        self.geometryToAscii(rootDummy, asciiLines, True)

    def importToScene(self, scene):
        pass
