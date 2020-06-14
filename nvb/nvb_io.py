"""TODO: DOC."""

import os
import re
import bpy

from . import nvb_glob
from . import nvb_def
from . import nvb_mdl
from . import nvb_utils


def findRootDummy():
    # Look for a rootdummy:
    # 1. Current selected object ?
    # 2. Search 'Empty' objects in the current scene
    # 4. Search all objects

    obj = None
    selected_objects = [ o for o in bpy.context.scene.objects if o.select ]
    if len(selected_objects):
        obj = selected_objects[0]
    # Selected object
    if nvb_utils.isRootDummy(obj, nvb_def.Dummytype.MDLROOT):
        return obj
    else:
        # Search ancestors of active object
        obj = nvb_utils.ancestorNode(bpy.context.active_object, nvb_utils.isRootDummy)
        if obj:
            return obj
        # Search objects in active scene
        if nvb_glob.scene:
            for obj in nvb_glob.scene.objects:
                if nvb_utils.isRootDummy(obj, nvb_def.Dummytype.MDLROOT):
                    return obj
        # Search all data
        for obj in bpy.data.objects:
            if nvb_utils.isRootDummy(obj, nvb_def.Dummytype.MDLROOT):
                return obj

    return None


def loadMdl(operator,
            context,
            filepath = '',
            importGeometry = True,
            importWalkmesh = True,
            importSmoothGroups = True,
            importAnim = True,
            materialMode = 'SIN',
            textureSearch = False,
            minimapMode = False,
            minimapSkipFade = False):
    '''
    Called from blender ui
    '''
    nvb_glob.importGeometry     = importGeometry
    nvb_glob.importSmoothGroups = importSmoothGroups
    nvb_glob.importAnim         = importAnim


    nvb_glob.materialMode = materialMode

    nvb_glob.texturePath   = os.path.dirname(filepath)
    nvb_glob.textureSearch = textureSearch

    nvb_glob.minimapMode     = minimapMode
    nvb_glob.minimapSkipFade = minimapSkipFade

    scene = bpy.context.scene

    # Try to load walkmeshes ... pwk (placeable) and dwk (door)
    # If the files are and the option is activated we'll import them
    wkm = None
    if importWalkmesh:
        filetypes = ['pwk', 'dwk', 'wok']
        (wkmPath, wkmFilename) = os.path.split(filepath)
        for wkmType in filetypes:
            if wkmFilename.endswith('.ascii'):
                wkmFilename = os.path.splitext(wkmFilename)[0]
            wkmFilepath = os.path.join(wkmPath,
                                       os.path.splitext(wkmFilename)[0] +
                                       '.' + wkmType)
            fp = os.fsencode(wkmFilepath)
            if not os.path.isfile(fp):
                fp = os.fsencode(wkmFilepath + '.ascii')
            try:
                asciiLines = [line.strip().split() for line in open(fp, 'r')]
                wkm = nvb_mdl.Xwk(wkmType)
                wkm.loadAscii(asciiLines)
                # adding walkmesh to scene has to be done within mdl import now
                #wkm.importToScene(scene)
            except IOError:
                print("Kotorblender - WARNING: No walkmesh found " +
                      wkmFilepath)

    # read the ascii mdl text
    fp = os.fsencode(filepath)
    ascii_mdl = ''
    f = open(fp, 'r')
    ascii_mdl = f.read()
    f.close()

    # strip any comments from the text immediately,
    # newer method of text processing is not robust against comments
    ascii_mdl = re.sub(r'#.+$', '', ascii_mdl, flags=re.MULTILINE)

    # prepare the old style data
    asciiLines = [line.strip().split() for line in ascii_mdl.splitlines()]

    print('Importing: ' + filepath)
    mdl = nvb_mdl.Mdl()
    #mdl.loadAscii(asciiLines)
    mdl.loadAscii(ascii_mdl)
    mdl.importToScene(scene, wkm)

    # processing to use AABB node as trimesh for walkmesh file
    if wkm is not None and wkm.walkmeshType == 'wok' and mdl.nodeDict and wkm.nodeDict:
        aabb = None
        wkmesh = None
        # find aabb node in model
        for (nodeKey, node) in mdl.nodeDict.items():
            if node.nodetype == 'aabb':
                aabb = node
        # find mesh node in wkm
        for (nodeKey, node) in wkm.nodeDict.items():
            if node.nodetype == 'aabb' or node.nodetype == 'trimesh':
                wkmesh = node
        if aabb and wkmesh:
            #print(aabb.lytposition)
            aabb.computeLayoutPosition(wkmesh)
            #print(aabb.lytposition)
            if len(wkmesh.roomlinks):
                aabb.roomlinks = wkmesh.roomlinks
                aabb.setRoomLinks(scene.objects[aabb.name].data)


    return {'FINISHED'}


def saveMdl(operator,
         context,
         filepath = '',
         exports = {'ANIMATION', 'WALKMESH'},
         exportSmoothGroups = True,
         exportTxi = True,
         applyModifiers = True,
         ):
    '''
    Called from blender ui
    '''
    nvb_glob.exports            = exports
    nvb_glob.exportSmoothGroups = exportSmoothGroups
    nvb_glob.exportTxi          = exportTxi
    nvb_glob.applyModifiers     = applyModifiers
    nvb_glob.scene              = bpy.context.scene

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    # reset exported status to false because save operation about to begin
    if exportTxi:
        for texture in bpy.data.textures:
            try:
                if texture.type == 'IMAGE' and texture.image:
                    texture.nvb.exported_in_save = False
            except:
                pass

    mdlRoot = findRootDummy()
    if mdlRoot:
        print('Kotorblender: Exporting ' + mdlRoot.name)
        mdl = nvb_mdl.Mdl()
        asciiLines = []
        mdl.generateAscii(asciiLines, mdlRoot)
        with open(os.fsencode(filepath), 'w') as f:
            f.write('\n'.join(asciiLines))

        if 'WALKMESH' in exports:
            wkmRoot = None
            aabb = nvb_utils.searchNode(mdlRoot, lambda x: x.nvb.meshtype == nvb_def.Meshtype.AABB)
            if aabb is not None:
                wkm     = nvb_mdl.Wok()
                wkmRoot = aabb
                wkmType = 'wok'
            else:
                # We need to look for a walkmesh rootdummy
                wkmRootName = mdl.name + '_pwk'
                if (wkmRootName in bpy.data.objects):
                    wkmRoot = bpy.data.objects[wkmRootName]
                    wkm     = nvb_mdl.Xwk('pwk')
                wkmRootName = mdl.name + '_PWK'
                if (not wkmRoot) and (wkmRootName in bpy.data.objects):
                    wkmRoot = bpy.data.objects[wkmRootName]
                    wkm     = nvb_mdl.Xwk('pwk')

                wkmRootName = mdl.name + '_dwk'
                if (not wkmRoot) and (wkmRootName in bpy.data.objects):
                    wkmRoot = bpy.data.objects[wkmRootName]
                    wkm     = nvb_mdl.Xwk('dwk')
                wkmRootName = mdl.name + '_DWK'
                if (not wkmRoot) and (wkmRootName in bpy.data.objects):
                    wkmRoot = bpy.data.objects[wkmRootName]
                    wkm     = nvb_mdl.Xwk('dwk')

            if wkmRoot:
                asciiLines = []
                wkm.generateAscii(asciiLines, wkmRoot)

                (wkmPath, wkmFilename) = os.path.split(filepath)
                wkmType = wkm.walkmeshType
                if wkmFilename.endswith('.ascii'):
                    wkmFilename = os.path.splitext(wkmFilename)[0]
                    wkmType += '.ascii'
                wkmFilepath = os.path.join(wkmPath, os.path.splitext(wkmFilename)[0] + '.' + wkmType)
                with open(os.fsencode(wkmFilepath), 'w') as f:
                    f.write('\n'.join(asciiLines))
        # reset exported status to false because save operation is concluding
        if exportTxi:
            for texture in bpy.data.textures:
                try:
                    if texture.type == 'IMAGE' and texture.image:
                        texture.nvb.exported_in_save = False
                except:
                    pass

    return {'FINISHED'}
