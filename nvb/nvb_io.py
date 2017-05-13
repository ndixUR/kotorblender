"""TODO: DOC."""

import os
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
    # Selected object
    if nvb_utils.isRootDummy(obj, nvb_def.Dummytype.MDLROOT):
        return obj
    else:
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
        filetypes = ['pwk', 'dwk']
        (wkmPath, wkmFilename) = os.path.split(filepath)
        for wkmType in filetypes:
            wkmFilepath = os.path.join(wkmPath,
                                       os.path.splitext(wkmFilename)[0] +
                                       '.' + wkmType)
            fp = os.fsencode(wkmFilepath)
            try:
                asciiLines = [line.strip().split() for line in open(fp, 'r')]
                wkm = nvb_mdl.Xwk(wkmType)
                wkm.loadAscii(asciiLines)
                # adding walkmesh to scene has to be done within mdl import now
                #wkm.importToScene(scene)
            except IOError:
                print("Neverblender - WARNING: No walkmesh found " +
                      wkmFilepath)

    fp = os.fsencode(filepath)
    asciiLines = [line.strip().split() for line in open(fp, 'r')]

    print('Importing: ' + filepath)
    mdl = nvb_mdl.Mdl()
    mdl.loadAscii(asciiLines)
    mdl.importToScene(scene, wkm)

    return {'FINISHED'}


def saveMdl(operator,
         context,
         filepath = '',
         exports = {'ANIMATION', 'WALKMESH'},
         exportSmoothGroups = True,
         applyModifiers = True,
         ):
    '''
    Called from blender ui
    '''
    nvb_glob.exports            = exports
    nvb_glob.exportSmoothGroups = exportSmoothGroups
    nvb_glob.applyModifiers     = applyModifiers
    nvb_glob.scene              = bpy.context.scene

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    mdlRoot = findRootDummy()
    if mdlRoot:
        print('Neverblender: Exporting ' + mdlRoot.name)
        mdl = nvb_mdl.Mdl()
        asciiLines = []
        mdl.generateAscii(asciiLines, mdlRoot)
        with open(os.fsencode(filepath), 'w') as f:
            f.write('\n'.join(asciiLines))

        if 'WALKMESH' in exports:
            wkmRoot = None
            if mdl.classification == nvb_def.Classification.TILE:
                wkm     = nvb_mdl.Wok()
                wkmRoot = mdlRoot
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

                wkmFileExt = '.pwk'
                if mdlRoot.nvb.classification == nvb_def.Classification.DOOR:
                    wkmFileExt = '.dwk'
                elif mdlRoot.nvb.classification == nvb_def.Classification.TILE:
                    wkmFileExt = '.wok'

                (wkmPath, wkmFilename) = os.path.split(filepath)
                wkmFilepath = os.path.splitext(filepath)[0] + wkmFileExt
                with open(os.fsencode(wkmFilepath), 'w') as f:
                    f.write('\n'.join(asciiLines))

    return {'FINISHED'}
