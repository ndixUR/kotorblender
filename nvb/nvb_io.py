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

    obj = bpy.context.object
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

    fp = os.fsencode(filepath)
    asciiLines = [line.strip().split() for line in open(fp, 'r')]

    print('Importing: ' + filepath)
    mdl = nvb_mdl.Mdl()
    mdl.loadAscii(asciiLines)
    mdl.importToScene(scene)

    # Try to load walkmeshes ... pwk (placeable) and dwk (door)
    # If the files are and the option is activated we'll import them
    if importWalkmesh:
        filetypes = ['pwk', 'dwk']
        (wkmPath, wkmFilename) = os.path.split(filepath)
        for wkmType in filetypes:
            wkmFilepath = os.path.join(wkmPath, os.path.splitext(wkmFilename)[0] + '.' + wkmType)
            fp = os.fsencode(wkmFilepath)
            try:
                asciiLines = [line.strip().split() for line in open(fp, 'r')]
                wkm = nvb_mdl.Xwk(wkmType)
                wkm.loadAscii(asciiLines)
                wkm.importToScene(scene)
            except IOError:
                print("Neverblender - WARNING: No walkmesh found " + wkmFilepath)

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
        print('Exporting: ' + mdlRoot.name)
        mdl = nvb_mdl.Mdl()
        asciiLines = []
        mdl.generateAscii(asciiLines, mdlRoot)
        with open(os.fsencode(filepath), 'w') as f:
            f.write('\n'.join(asciiLines))

        if 'WALKMESH' in exports:
            if mdl.classification == nvb_def.Classification.TILE:
                wkm     = nvb_mdl.Wok()
                wkmRoot = mdlRoot
                wkmType = 'wok'
            else:
                wkmRoot = None

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
                # TODO: If we can't find one by name we'll look for an arbitrary one

            if wkmRoot:
                asciiLines = []
                wkm.generateAscii(asciiLines, wkmRoot)

                (wkmPath, wkmFilename) = os.path.split(filepath)
                wkmFilepath = os.path.join(wkmPath, os.path.splitext(wkmFilename)[0] + '.' + wkm.walkmeshType)
                with open(os.fsencode(wkmFilepath), 'w') as f:
                    f.write('\n'.join(asciiLines))

    return {'FINISHED'}
