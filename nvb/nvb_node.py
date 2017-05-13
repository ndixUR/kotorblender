"""TODO: DOC."""
import mathutils
import bpy
import bpy_extras.image_utils
import bmesh
from bpy_extras.io_utils import unpack_list, unpack_face_list

from . import nvb_glob
from . import nvb_def
from . import nvb_utils
from . import nvb_aabb
from . import nvb_parse

class FaceList():
    def __init__(self):
        self.faces = []  # int 3-tuple, vertex indices
        self.shdgr = []  # int, shading group for this face
        self.uvIdx = []  # int 3-tuple, texture/uv vertex indices
        self.matId = []  # int, material index


class FlareList():
    def __init__(self):
        self.textures    = []
        self.sizes       = []
        self.positions   = []
        self.colorshifts = []


class GeometryNode():
    """
    Basic node from which every other is derived
    """
    def __init__(self, name = 'UNNAMED'):
        self.nodetype = 'undefined'

        self.name        = name
        self.parentName  = nvb_def.null
        self.position    = (0.0, 0.0, 0.0)
        self.orientation = (0.0, 0.0, 0.0, 0.0)
        self.scale       = 1.0
        self.wirecolor   = (0.0, 0.0, 0.0)

        # Name of the corresponding object in blender
        # (used to resolve naming conflicts)
        self.objref   = ''


    def __eq__(self, other):
        if isinstance(other, Base):
            return self.name == other.name


    def __ne__(self, other):
        return not self.__eq__(self, other)


    def __str__(self):
        return 'node ' + self.nodetype + ' ' + self.name


    def parse1f(self, asciiBlock, floatList):
        l_float = float
        for line in asciiBlock:
            floatList.append(l_float(line[0]))


    def parse2f(self, asciiBlock, floatList):
        l_float = float
        for line in asciiBlock:
            floatList.append( (l_float(line[0]), l_float(line[1])) )


    def parse3f(self, asciiBlock, floatList):
        l_float = float
        for line in asciiBlock:
            floatList.append( (l_float(line[0]), l_float(line[1]), l_float(line[2])) )


    def loadAscii(self, asciiNode):
        l_float = float
        l_isNumber = nvb_utils.isNumber

        for line in asciiNode:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if (label == 'node'):
                    self.name = nvb_utils.getName(line[2])
                elif (label == 'endnode'):
                    return
                elif (label == 'parent'):
                    self.parentName = nvb_utils.getName(line[1])
                elif (label == 'position'):
                    self.position = (l_float(line[1]),
                                     l_float(line[2]),
                                     l_float(line[3]))
                elif (label == 'orientation'):
                    self.orientation = (l_float(line[1]),
                                        l_float(line[2]),
                                        l_float(line[3]),
                                        l_float(line[4]))
                elif (label == 'scale'):
                    self.scale = l_float(line[1])
                elif (label == 'wirecolor'):
                    self.wirecolor = (l_float(line[1]),
                                      l_float(line[2]),
                                      l_float(line[3]))

    def setObjectData(self, obj):
        self.objref = obj.name  # used to resolve naming conflicts
        nvb_utils.setObjectRotationAurora(obj, self.orientation)
        obj.scale         = (self.scale, self.scale, self.scale)
        obj.location      = self.position
        obj.nvb.wirecolor = self.wirecolor

    def addToScene(self, scene):
        obj = bpy.data.objects.new(self.name, None)
        self.setObjectData(obj)
        scene.objects.link(obj)
        return obj

    def getAdjustedMatrix(self, obj):

        if obj.parent:
            parent_mw = obj.parent.matrix_world
        else:
            parent_mw = mathutils.matrix()

        p_mw_scale = parent_mw.to_scale()

        # scale_m = mathutils.Matrix([[p_mw_scale[0],0,0,0],
        #                             [0,p_mw_scale[1],0,0],
        #                             [0,0,p_mw_scale[2],0],
        #                             [0,0,0            ,1]])

        scaled = obj.matrix_local.copy()
        scaled[0][3] = scaled[0][3] * p_mw_scale[0]
        scaled[1][3] = scaled[1][3] * p_mw_scale[1]
        scaled[2][3] = scaled[2][3] * p_mw_scale[2]
        return scaled

    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        if obj.parent:
            asciiLines.append('  parent ' + obj.parent.name)
        else:
            asciiLines.append('  parent ' + nvb_def.null)
        # Scaling fix
        transmat = self.getAdjustedMatrix(obj)
        loc = transmat.to_translation()
        s = '  position {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(loc[0], 7), round(loc[1], 7), round(loc[2], 7))
        asciiLines.append(s)

        rot = nvb_utils.euler2nwangle(transmat.to_euler('XYZ'))
        s = '  orientation {: 8.7f} {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(rot[0], 7), round(rot[1], 7), round(rot[2], 7), round(rot[3], 7))
        asciiLines.append(s)
        '''
        loc = obj.location
        s = '  position {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(loc[0], 7), round(loc[1], 7), round(loc[2], 7))
        asciiLines.append(s)

        rot = nvb_utils.getAuroraRotFromObject(obj)
        s = '  orientation {: 8.7f} {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(rot[0], 7), round(rot[1], 7), round(rot[2], 7), round(rot[3], 7))
        asciiLines.append(s)
        '''
        color = obj.nvb.wirecolor
        asciiLines.append('  wirecolor ' + str(round(color[0], 2)) + ' ' +
                                           str(round(color[1], 2)) + ' ' +
                                           str(round(color[2], 2)) )
        scale = round(nvb_utils.getAuroraScale(obj), 3)
        if (scale != 1.0):
            asciiLines.append('  scale ' + str(scale))

    def toAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        asciiLines.append('node ' + self.nodetype + ' ' + obj.name)
        self.addDataToAscii(obj, asciiLines, exportObjects, classification, simple)
        asciiLines.append('endnode')


class Dummy(GeometryNode):
    '''

    '''
    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype  = 'dummy'

        self.dummytype = nvb_def.Dummytype.NONE

    def loadAscii(self, asciiNode):
        GeometryNode.loadAscii(self, asciiNode)

    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)

        obj.nvb.dummytype = self.dummytype

        obj.nvb.dummysubtype = nvb_def.DummySubtype.NONE
        subtypes = nvb_def.DummySubtype.SUFFIX_LIST
        for element in subtypes:
            if self.name.endswith(element[0]):
                obj.nvb.dummysubtype = element[1]
                break

    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        if obj.parent:
            asciiLines.append('  parent ' + obj.parent.name)
        else:
            asciiLines.append('  parent ' + nvb_def.null)

        dummytype = obj.nvb.dummytype
        if dummytype == nvb_def.Dummytype.MDLROOT:
            # Only parent for rootdummys
            return

        # scale = round(nvb_utils.getAuroraScale(obj), 3)
        # Scaling fix
        asciiLines.append('  scale 1.0')
        '''
        if (scale != 1.0):
            asciiLines.append('  scale ' + str(scale))
        '''

        # Scaling fix
        transmat = self.getAdjustedMatrix(obj)
        loc = transmat.to_translation()
        s = '  position {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(loc[0], 7), round(loc[1], 7), round(loc[2], 7))
        asciiLines.append(s)

        rot = nvb_utils.euler2nwangle(transmat.to_euler('XYZ'))
        s = '  orientation {: 8.7f} {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(rot[0], 7), round(rot[1], 7), round(rot[2], 7), round(rot[3], 7))
        asciiLines.append(s)
        '''
        loc = obj.location
        s = '  position {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(loc[0], 7), round(loc[1], 7), round(loc[2], 7))
        asciiLines.append(s)

        rot = nvb_utils.getAuroraRotFromObject(obj)
        s = '  orientation {: 8.7f} {: 8.7f} {: 8.7f} {: 8.7f}'.format(round(rot[0], 7), round(rot[1], 7), round(rot[2], 7), round(rot[3], 7))
        asciiLines.append(s)
        '''

        color = obj.nvb.wirecolor
        asciiLines.append('  wirecolor ' + str(round(color[0], 2)) + ' ' +
                                           str(round(color[1], 2)) + ' ' +
                                           str(round(color[2], 2)) )

        # TODO: Handle types and subtypes, i.e. Check and modify name
        subtype = obj.nvb.dummysubtype
        if subtype == nvb_def.Dummytype.NONE:
            pass


class Patch(GeometryNode):
    """Same as a plain Dummy."""

    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype = 'patch'

        self.dummytype = nvb_def.Dummytype.PATCH

    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)

        obj.nvb.dummytype = self.dummytype


class Reference(GeometryNode):
    """Contains a reference to another mdl."""

    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype = 'reference'

        self.dummytype = nvb_def.Dummytype.REFERENCE
        self.refmodel     = nvb_def.null
        self.reattachable = 0

    def loadAscii(self, asciiNode):
        GeometryNode.loadAscii(self, asciiNode)
        l_isNumber = nvb_utils.isNumber

        for line in asciiNode:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if not l_isNumber(label):
                if (label == 'refmodel'):
                    # self.refmodel = line[1].lower()
                    self.refmodel = line[1]
                elif (label == 'reattachable'):
                    self.reattachable = int(line[1])


    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)
        obj.nvb.dummytype    = self.dummytype
        obj.nvb.refmodel     = self.refmodel
        obj.nvb.reattachable = (self.reattachable == 1)


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        GeometryNode.addDataToAscii(self, obj, asciiLines, exportObjects, classification)
        asciiLines.append('  refmodel ' + obj.nvb.refmodel)
        asciiLines.append('  reattachable ' + str(int(obj.nvb.reattachable)))


class Trimesh(GeometryNode):
    """TODO: Doc."""

    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype = 'trimesh'

        self.meshtype         = nvb_def.Meshtype.TRIMESH
        self.center           = (0.0, 0.0, 0.0) # Unused ?
        self.tilefade         = 0
        self.lightmapped      = 0
        self.render           = 1
        self.shadow           = 1
        self.beaming          = 0
        self.inheritcolor     = 0  # Unused ?
        self.alpha            = 1.0
        self.transparencyhint = 0
        self.selfillumcolor   = (0.0, 0.0, 0.0)
        self.ambient          = (0.0, 0.0, 0.0)
        self.diffuse          = (0.0, 0.0, 0.0)
        self.specular         = (0.0, 0.0, 0.0)
        self.shininess        = 0
        self.bitmap           = nvb_def.null
        self.bitmap2          = nvb_def.null
        self.rotatetexture    = 0
        self.verts            = [] # list of vertices
        self.facelist         = FaceList()
        self.tverts           = [] # list of texture vertices
        self.tverts1          = [] # list of texture vertices

    def createImage(self, imgName, imgPath):
        image = bpy_extras.image_utils.load_image(imgName + '.tga',
                                                  imgPath,
                                                  recursive=nvb_glob.textureSearch,
                                                  place_holder=False,
                                                  ncase_cmp=True)
        if (image is None):
            print('Neverblender - WARNING: Could not load image ' + imgName)
            print(imgPath)
            image = bpy.data.images.new(imgName, 512, 512)
        else:
            image.name = imgName

        return image

    def loadAscii(self, asciiNode):
        GeometryNode.loadAscii(self, asciiNode)

        l_int   = int
        l_float = float
        l_isNumber = nvb_utils.isNumber
        for idx, line in enumerate(asciiNode):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if (label == 'tilefade'):
                    self.tilefade = l_int(line[1])
                elif (label == 'render'):
                    self.render = l_int(line[1])
                elif (label == 'shadow'):
                    self.shadow = l_int(line[1])
                elif (label == 'lightmapped'):
                    self.lightmapped = l_int(line[1])
                elif (label == 'beaming'):
                    self.beaming = l_int(line[1])
                elif (label == 'inheritcolor '):
                    self.inheritcolor = l_int(line[1])
                elif (label == 'rotatetexture'):
                    self.rotatetexture = l_int(line[1])
                elif (label == 'alpha'):
                    self.alpha = l_float(line[1])
                elif (label == 'transparencyhint'):
                    self.transparencyhint = l_int(line[1])
                elif (label == 'selfillumcolor'):  # Self illumination color
                    self.selfillumcolor = (l_float(line[1]),
                                           l_float(line[2]),
                                           l_float(line[3]))
                elif (label == 'ambient'):
                    self.ambient = (l_float(line[1]),
                                    l_float(line[2]),
                                    l_float(line[3]))
                elif (label == 'diffuse'):
                    self.diffuse = (l_float(line[1]),
                                    l_float(line[2]),
                                    l_float(line[3]))
                elif (label == 'specular'):
                    self.specular = (l_float(line[1]),
                                     l_float(line[2]),
                                     l_float(line[3]))
                elif (label == 'shininess'):
                    self.shininess = l_int(l_float(line[1]))
                elif (label == 'center'):
                    # Unused ? Becuase we don't do anything with this
                    try:
                        self.center = (l_float(line[1]),
                                       l_float(line[2]),
                                       l_float(line[3]))
                    except:
                        # Probably an 'undefined' string which cannot be
                        # converted to float
                        pass
                elif (label == 'bitmap'):
                    self.bitmap = line[1]
                elif (label == 'bitmap2'):
                    self.bitmap2 = line[1]
                elif (label == 'verts'):
                    numVals = l_int(line[1])
                    nvb_parse.f3(asciiNode[idx+1:idx+numVals+1], self.verts)
                    #self.verts = [(float(l[0]), float(l[1]), float(l[2])) for l in asciiNode[idx+1:idx+numVals+1]]
                elif (label == 'faces'):
                    numVals = l_int(line[1])
                    self.parseFaceList(asciiNode[idx+1:idx+numVals+1])
                elif (label == 'tverts'):
                    numVals = l_int(line[1])
                    nvb_parse.f2(asciiNode[idx+1:idx+numVals+1], self.tverts)
                    #self.tverts = [(float(l[0]), float(l[1])) for l in asciiNode[idx+1:idx+numVals+1]]
                elif (label == 'tverts1'):
                    numVals = l_int(line[1])
                    nvb_parse.f2(asciiNode[idx+1:idx+numVals+1], self.tverts1)

    def parseFaceList(self, asciiFaces):
        l_int = int
        for line in asciiFaces:
            self.facelist.faces.append((l_int(line[0]),
                                        l_int(line[1]),
                                        l_int(line[2])))
            self.facelist.shdgr.append(l_int(line[3]))
            self.facelist.uvIdx.append((l_int(line[4]),
                                        l_int(line[5]),
                                        l_int(line[6])))
            self.facelist.matId.append(l_int(line[7]))

    def createMaterial(self, name, bitmap):
        material = None
        texName  = self.bitmap.lower()
        if nvb_glob.materialMode == 'SIN':
            # Avoid duplicate materials, search for similar ones.
            material = nvb_utils.materialExists(self.diffuse,
                                                self.specular,
                                                texName,
                                                self.alpha)

        if not material:
            material = bpy.data.materials.new(name)
            material.diffuse_color     = self.diffuse
            material.diffuse_intensity = 1.0
            material.specular_color    = self.specular

            if not nvb_utils.isNull(self.bitmap):
                textureSlot = material.texture_slots.add()
                # If a texture with the same name was already created treat
                # them as if they were the same, i.e. just use the old one
                if (texName in bpy.data.textures):
                    textureSlot.texture = bpy.data.textures[texName]
                else:
                    textureSlot.texture = bpy.data.textures.new(texName, type='IMAGE')
                textureSlot.texture_coords        = 'UV'
                textureSlot.use_map_color_diffuse = True

                # Load the image for the texture, but check if it was
                # already loaded before. If so, use that one.
                imgName = bitmap
                if (imgName in bpy.data.images):
                    image = bpy.data.images[imgName]
                    textureSlot.texture.image = image
                else:
                    image = self.createImage(imgName, nvb_glob.texturePath)
                    if image is not None:
                        textureSlot.texture.image = image

            nvb_utils.setMaterialAuroraAlpha(material, self.alpha)

        return material


    def createMesh(self, name):
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(self.verts))
        mesh.vertices.foreach_set('co', unpack_list(self.verts))
        mesh.tessfaces.add(len(self.facelist.faces))
        mesh.tessfaces.foreach_set('vertices_raw', unpack_face_list(self.facelist.faces))

        # Create material
        if nvb_glob.materialMode != 'NON':
            material = self.createMaterial(name, self.bitmap)
            mesh.materials.append(material)

            # Lightmap material?
            if (not nvb_utils.isNull(self.bitmap2)):
                # configure material:
                material.use_shadeless = True
                texName = self.bitmap2.lower()
                textureSlot = material.texture_slots.add()
                # If a texture with the same name was already created treat
                # them as if they were the same, i.e. just use the old one
                if (texName in bpy.data.textures):
                    textureSlot.texture = bpy.data.textures[texName]
                else:
                    textureSlot.texture = bpy.data.textures.new(texName, type='IMAGE')
                textureSlot.texture_coords        = 'UV'
                textureSlot.use_map_color_diffuse = True
                textureSlot.blend_type            = 'OVERLAY'
                # set slot 0's uv layer now

                # Load the image for the texture, but check if it was
                # already loaded before. If so, use that one.
                imgName = self.bitmap2
                if (imgName in bpy.data.images):
                    image = bpy.data.images[imgName]
                    textureSlot.texture.image = image
                else:
                    image = self.createImage(imgName, nvb_glob.texturePath)
                    if image is not None:
                        textureSlot.texture.image = image

            # Create UV map
            if (len(self.tverts) > 0) and (mesh.tessfaces) and (not nvb_utils.isNull(self.bitmap)):
                uv = mesh.tessface_uv_textures.new(name + '.uv')
                mesh.tessface_uv_textures.active = uv

                for i in range(len(self.facelist.uvIdx)):
                    # Get a tessface
                    tessface = mesh.tessfaces[i]
                    # Apply material (there is only ever one)
                    tessface.material_index = 0
                    # Grab a uv for the face
                    tessfaceUV = mesh.tessface_uv_textures[0].data[i]
                    # Get the indices of the 3 uv's for this face
                    uvIdx = self.facelist.uvIdx[i]

                    # BEGIN EEEKADOODLE FIX
                    # BUG: Evil eekadoodle problem where faces that have
                    # vert index 0 at location 3 are shuffled.
                    vertIdx = self.facelist.faces[i]
                    if vertIdx[2] == 0:
                        uvIdx = uvIdx[1], uvIdx[2], uvIdx[0]
                    # END EEEKADOODLE FIX

                    # Add uv coordinates to face
                    tessfaceUV.uv1 = self.tverts[uvIdx[0]]
                    tessfaceUV.uv2 = self.tverts[uvIdx[1]]
                    tessfaceUV.uv3 = self.tverts[uvIdx[2]]

                    # Apply texture to uv face
                    if material.texture_slots[0]:
                        tessfaceUV.image = material.texture_slots[0].texture.image

            # Create lightmap UV map
            if (len(self.tverts1) > 0) and (mesh.tessfaces) and (not nvb_utils.isNull(self.bitmap2)):
                uv = mesh.tessface_uv_textures.new(name + '_lm.uv')
                #mesh.tessface_uv_textures.active = uv

                for i in range(len(self.facelist.uvIdx)):
                    # Get a tessface
                    tessface = mesh.tessfaces[i]
                    # Apply material (there is only ever one)
                    tessface.material_index = 0
                    # Grab a uv for the face
                    tessfaceUV = mesh.tessface_uv_textures[1].data[i]
                    # Get the indices of the 3 uv's for this face
                    uvIdx = self.facelist.uvIdx[i]

                    # BEGIN EEEKADOODLE FIX
                    # BUG: Evil eekadoodle problem where faces that have
                    # vert index 0 at location 3 are shuffled.
                    vertIdx = self.facelist.faces[i]
                    if vertIdx[2] == 0:
                        uvIdx = uvIdx[1], uvIdx[2], uvIdx[0]
                    # END EEEKADOODLE FIX

                    # Add uv coordinates to face
                    tessfaceUV.uv1 = self.tverts1[uvIdx[0]]
                    tessfaceUV.uv2 = self.tverts1[uvIdx[1]]
                    tessfaceUV.uv3 = self.tverts1[uvIdx[2]]

                    # Apply texture to uv face
                    if material.texture_slots[1]:
                        tessfaceUV.image = material.texture_slots[1].texture.image
                material.texture_slots[1].uv_layer = name + '_lm.uv'
                material.texture_slots[0].uv_layer = name + '.uv'

        # Import smooth groups as sharp edges
        if nvb_glob.importSmoothGroups:
            bm = bmesh.new()
            mesh.update()
            bm.from_mesh(mesh)
            if hasattr(bm.edges, "ensure_lookup_table"):
                bm.edges.ensure_lookup_table()
            # Mark edge as sharp if its faces belong to different smooth groups
            for e in bm.edges:
                f = e.link_faces
                if (len(f) > 1) and (self.facelist.shdgr[f[0].index] != self.facelist.shdgr[f[1].index]):
                    edgeIdx = e.index
                    mesh.edges[edgeIdx].use_edge_sharp = True
            bm.free()
            del bm
            mesh.show_edge_sharp = True

        mesh.update()
        return mesh


    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)

        obj.nvb.meshtype         = self.meshtype
        obj.nvb.tilefade         = self.tilefade
        obj.nvb.lightmapped      = (self.lightmapped == 1)
        obj.nvb.render           = (self.render == 1)
        obj.nvb.shadow           = (self.shadow == 1)
        obj.nvb.beaming          = (self.beaming == 1)
        obj.nvb.inheritcolor     = (self.inheritcolor == 1)
        obj.nvb.rotatetexture    = (self.rotatetexture == 1)
        obj.nvb.transparencyhint = self.transparencyhint
        obj.nvb.selfillumcolor   = self.selfillumcolor
        obj.nvb.ambientcolor     = self.ambient
        obj.nvb.shininess        = self.shininess


    def addToScene(self, scene):
        if nvb_glob.minimapMode:
            if (self.tilefade and nvb_glob.minimapSkipFade) or not self.render:
                # Fading objects won't be imported in minimap mode
                # We may need it for the tree stucture, so import it as an empty
                return Dummy.addToScene(self, scene)
        mesh = self.createMesh(self.name)
        obj  = bpy.data.objects.new(self.name, mesh)
        self.setObjectData(obj)
        scene.objects.link(obj)
        return obj


    def addMaterialDataToAscii(self, obj, asciiLines):
        # Check if this object has a material assigned to it
        material = obj.active_material
        if material:
            color = material.diffuse_color
            asciiLines.append('  diffuse ' +    str(round(color[0], 2)) + ' ' +
                                                str(round(color[1], 2)) + ' ' +
                                                str(round(color[2], 2))  )
            color = material.specular_color
            asciiLines.append('  specular ' +   str(round(color[0], 2)) + ' ' +
                                                str(round(color[1], 2)) + ' ' +
                                                str(round(color[2], 2))  )

            # Check if this material has a texture assigned
            texture = material.active_texture
            imgName = nvb_def.null
            if texture:
                # Only image textures will be exported
                if (texture.type == 'IMAGE') and (texture.image):
                    imgName = nvb_utils.getImageFilename(texture.image)
                else:
                    imgName = nvb_def.null
            asciiLines.append('  bitmap ' + imgName)
            asciiLines.append('  alpha ' + str(round(nvb_utils.getAuroraAlpha(obj), 2)))
            # Test for lightmap assigned as second texture
            if material.texture_slots[1]:
                texture  = material.texture_slots[1].texture
                imgName = nvb_def.null
                if obj.nvb.lightmapped and texture and (texture.type == 'IMAGE') and (texture.image):
                    imgName = nvb_utils.getImageFilename(texture.image)
                # Write bitmap2 NULL if texture is removed/non-image or lightmapped was clicked off.
                # this is for when a model that imported with lightmapping is being exported without it,
                # possibly w/o disabling everything properly
                asciiLines.append('  bitmap2 ' + imgName)

        else:
            # No material, set some default values
            asciiLines.append('  diffuse 1.0 1.0 1.0')
            asciiLines.append('  specular 0.0 0.0 0.0')
            asciiLines.append('  alpha 1.0')
            asciiLines.append('  bitmap ' + nvb_def.null)


    def addUVToList(self, uv, uvList, vert, vertList):
        """Helper function to keep UVs unique."""
        if uv in uvList and vert in vertList:
            return uvList.index(uv)
        else:
            uvList.append(uv)
            vertList.append(vert)
            return (len(uvList)-1)


    def addMeshDataToAscii(self, obj, asciiLines, simple = False):
        mesh = obj.to_mesh(nvb_glob.scene, nvb_glob.applyModifiers, nvb_glob.meshConvert)
        for p in mesh.polygons:
            p.use_smooth = True

        # Scaling fix
        # TODO: Find out how exactly blender handles scaling, which matrices to use etc
        scale = obj.matrix_world.to_scale()
        scale_matrix = mathutils.Matrix([[scale[0],0,0,0],
                                         [0,scale[1],0,0],
                                         [0,0,scale[2],0],
                                         [0,0,0       ,1]])
        mesh.transform(scale_matrix)

        # Triangulation (doing it with bmesh to retain edges marked as sharp)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        del bm

        # Recalculate tessfaces for export
        mesh.calc_tessface()

        # Calculate smooth groups
        smoothGroups    = []
        numSmoothGroups = 0
        if (obj.nvb.smoothgroup == 'SEPR') or (not nvb_glob.exportSmoothGroups):
            # 0 = Do not use smoothgroups
            smoothGroups    = [0] * len(mesh.polygons)
            numSmoothGroups = 1
        elif (obj.nvb.smoothgroup == 'SING'):
            # All faces belong to smooth group 1
            smoothGroups    = [1] * len(mesh.polygons)
            numSmoothGroups = 1
        else:
            (smoothGroups, numSmoothGroups) = mesh.calc_smooth_groups()

        faceList = [] # List of triangle faces
        uvList   = [] # List of uv indices
        uvVertList = [] # Temp list of uv verts used for each geometry vert
        # separate lists for the lightmap UVs if they exist
        uvListLM     = [] # List of uv indices
        uvVertListLM = [] # Temp list of uv verts used for each geometry vert

        # Add vertices
        asciiLines.append('  verts ' + str(len(mesh.vertices)))
        l_round = round
        formatString = '    {: 8.7f} {: 8.7f} {: 8.7f}'
        for v in mesh.vertices:
            s = formatString.format(l_round(v.co[0], 7), l_round(v.co[1], 7), l_round(v.co[2], 7))
            asciiLines.append(s)

        # Add faces and corresponding tverts and shading groups
        tessfaces     = mesh.tessfaces
        tessfaces_uvs = mesh.tessface_uv_textures.active
        tessfaces_uvs_lm = False
        if len(mesh.tessface_uv_textures) > 1:
            tessfaces_uvs_lm = mesh.tessface_uv_textures[1]
        for idx in range(len(tessfaces)):
            tface   = tessfaces[idx]
            smGroup = smoothGroups[idx]
            matIdx  = tface.material_index

            # We triangulated, so faces are always triangles
            uv1 = 0
            uv2 = 0
            uv3 = 0
            if tessfaces_uvs:
                uvData = tessfaces_uvs.data[idx]
                uv1 = self.addUVToList(uvData.uv1, uvList, tface.vertices[0], uvVertList)
                uv2 = self.addUVToList(uvData.uv2, uvList, tface.vertices[1], uvVertList)
                uv3 = self.addUVToList(uvData.uv3, uvList, tface.vertices[2], uvVertList)
            # constructing lightmap (second texture) UV list
            uv1LM = 0
            uv2LM = 0
            uv3LM = 0
            if tessfaces_uvs_lm:
                uvData = tessfaces_uvs_lm.data[idx]
                uv1LM = self.addUVToList(uvData.uv1, uvListLM, tface.vertices[0], uvVertListLM)
                uv2LM = self.addUVToList(uvData.uv2, uvListLM, tface.vertices[1], uvVertListLM)
                uv3LM = self.addUVToList(uvData.uv3, uvListLM, tface.vertices[2], uvVertListLM)

            faceList.append([tface.vertices[0], tface.vertices[1], tface.vertices[2], smGroup,
                             uv1, uv2, uv3, matIdx, uv1LM, uv2LM, uv3LM])

        # Check a texture, we don't want uv's when there is no texture
        material = obj.active_material
        texture  = None
        if material:
            texture = material.active_texture

        if simple or not texture:
            asciiLines.append('  faces ' + str(len(faceList)))

            vertDigits        = str(len(str(len(mesh.vertices))))
            smoothGroupDigits = str(len(str(numSmoothGroups)))
            formatString = '    {:' + vertDigits + 'd} {:' + vertDigits + 'd} {:' + vertDigits + 'd}  ' + \
                               '{:' + smoothGroupDigits + 'd}  ' + \
                               '0 0 0  ' + \
                               '{:2d}'
            for f in faceList:
                s = formatString.format(f[0], f[1], f[2], f[3], f[7])
                asciiLines.append(s)
        else:
            asciiLines.append('  faces ' + str(len(faceList)))

            vertDigits        = str(len(str(len(mesh.vertices))))
            smoothGroupDigits = str(len(str(numSmoothGroups)))
            uvDigits          = str(len(str(len(uvList))))
            formatString = '    {:' + vertDigits + 'd} {:' + vertDigits + 'd} {:' + vertDigits + 'd}  ' + \
                               '{:' + smoothGroupDigits + 'd}  ' + \
                               '{:' + uvDigits + 'd} {:' + uvDigits + 'd} {:' + uvDigits + 'd}  ' + \
                               '{:2d}'
            for f in faceList:
                s = formatString.format(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7])
                asciiLines.append(s)

            if (len(uvList) > 0):
                asciiLines.append('  tverts ' + str(len(uvList)))
                formatString = '    {: 6.7f} {: 6.7f}'
                for uv in uvList:
                    s = formatString.format(round(uv[0], 7), round(uv[1], 7))
                    asciiLines.append(s)

            if (len(uvListLM) > 0):
                asciiLines.append('  tverts1 ' + str(len(uvListLM)))
                formatString = '    {: 6.7f} {: 6.7f} 0'
                for uv in uvListLM:
                    s = formatString.format(round(uv[0], 7), round(uv[1], 7))
                    asciiLines.append(s)
                asciiLines.append('  texindices1 ' + str(len(faceList)))
                formatString = '    {:3d} {:3d} {:3d}'
                for f in faceList:
                    asciiLines.append(formatString.format(f[8], f[9], f[10]))

        bpy.data.meshes.remove(mesh)


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        GeometryNode.addDataToAscii(self, obj, asciiLines, exportObjects, classification, simple)

        color = obj.nvb.ambientcolor
        asciiLines.append('  ambient ' +    str(round(color[0], 2)) + ' ' +
                                            str(round(color[1], 2)) + ' ' +
                                            str(round(color[2], 2))  )
        self.addMaterialDataToAscii(obj, asciiLines)
        asciiLines.append('  shininess ' + str(obj.nvb.shininess))
        if not simple:


            color = obj.nvb.selfillumcolor
            asciiLines.append('  selfillumcolor ' + str(round(color[0], 2)) + ' ' +
                                                    str(round(color[1], 2)) + ' ' +
                                                    str(round(color[2], 2))  )

            asciiLines.append('  render ' + str(int(obj.nvb.render)))
            asciiLines.append('  shadow ' + str(int(obj.nvb.shadow)))
            asciiLines.append('  beaming ' + str(int(obj.nvb.beaming)))
            asciiLines.append('  inheritcolor ' + str(int(obj.nvb.inheritcolor)))
            asciiLines.append('  transparencyhint ' + str(obj.nvb.transparencyhint))
            # These two are for tiles only
            if classification == 'TILE':
                asciiLines.append('  rotatetexture ' + str(int(obj.nvb.rotatetexture)))
                asciiLines.append('  tilefade ' + str(int(obj.nvb.tilefade)))

        self.addMeshDataToAscii(obj, asciiLines, simple)


class Danglymesh(Trimesh):
    """

    """
    def __init__(self, name = 'UNNAMED'):
        Trimesh.__init__(self, name)
        self.nodetype = 'danglymesh'

        self.meshtype     = nvb_def.Meshtype.DANGLYMESH
        self.period       = 1.0
        self.tightness    = 1.0
        self.displacement = 1.0
        self.constraints  = []


    def loadAscii(self, asciiNode):
        Trimesh.loadAscii(self, asciiNode)

        l_int   = int
        l_float = float
        l_isNumber = nvb_utils.isNumber
        for idx, line in enumerate(asciiNode):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if   (label == 'period'):
                    self.period = l_float(line[1])
                elif (label == 'tightness'):
                    self.tightness = l_float(line[1])
                elif (label == 'displacement'):
                    self.displacement = l_float(line[1])
                elif (label == 'constraints'):
                    numVals = l_int(line[1])
                    nvb_parse.f1(asciiNode[idx+1:idx+numVals+1], self.constraints)
                    #self.constraints = [float(l[0]) for l in asciiNode[idx+1:idx+numVals+1]]

    def addConstraintsToObject(self, obj):
        '''
        Creates a vertex group for the object to contain the vertex
        weights for the danglymesh. The weights are called "constraints"
        in NWN. Range is [0.0, 255.0] as opposed to [0.0, 1.0] in Blender
        '''
        vgroup = obj.vertex_groups.new('constraints')
        for vertexIdx, constraint in enumerate(self.constraints):
            weight = constraint/255
            vgroup.add([vertexIdx], weight, 'REPLACE')
        obj.nvb.constraints = vgroup.name


    def setObjectData(self, obj):
        Trimesh.setObjectData(self, obj)

        obj.nvb.period       = self.period
        obj.nvb.tightness    = self.tightness
        obj.nvb.displacement = self.displacement
        self.addConstraintsToObject(obj)


    def addConstraintsToAscii(self, obj, asciiLines):
        vgroupName = obj.nvb.constraints
        vgroup     = obj.vertex_groups[vgroupName]

        numVerts = len(obj.data.vertices)
        asciiLines.append('  constraints ' + str(numVerts))
        for i, v in enumerate(obj.data.vertices):
            try:
                asciiLines.append('    ' + str(round(vgroup.weight(i)*255, 3)))
            except:
                # Vertex is not part of this group
                asciiLines.append('    0.0')


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        Trimesh.addDataToAscii(self, obj, asciiLines, exportObjects, classification)

        asciiLines.append('  period '       + str(round(obj.nvb.period, 3)))
        asciiLines.append('  tightness '    + str(round(obj.nvb.tightness, 3)))
        asciiLines.append('  displacement ' + str(round(obj.nvb.displacement, 3)))
        self.addConstraintsToAscii(obj, asciiLines)


class Skinmesh(Trimesh):
    """Skinmeshes are Trimeshes where every vertex has a weight."""

    def __init__(self, name = 'UNNAMED'):
        Trimesh.__init__(self, name)
        self.nodetype = 'skin'

        self.meshtype = nvb_def.Meshtype.SKIN
        self.weights = []

    def loadAscii(self, asciiNode):
        Trimesh.loadAscii(self, asciiNode)
        l_int      = int
        l_isNumber = nvb_utils.isNumber
        for idx, line in enumerate(asciiNode):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if (label == 'weights'):
                    numVals = l_int(line[1])
                    self.getWeightsFromAscii(asciiNode[idx+1:idx+numVals+1])
                    break  # Only one value here, abort loop when read


    def getWeightsFromAscii(self, asciiBlock):
        lfloat = float
        lchunker = nvb_utils.chunker
        for line in asciiBlock:
            # A line looks like this
            # [group_name, vertex_weight, group_name, vertex_weight]
            # We create a list looking like this:
            # [[group_name, vertex_weight], [group_name, vertex_weight]]
            memberships = []
            for chunk in lchunker(line, 2):
                memberships.append([chunk[0], lfloat(chunk[1])])

            self.weights.append(memberships)


    def addSkinGroupsToObject(self, obj):
        skinGroupDict = {}
        for vertIdx, vertMemberships in enumerate(self.weights):
            for membership in vertMemberships:
                if membership[0] in skinGroupDict:
                    skinGroupDict[membership[0]].add([vertIdx], membership[1], 'REPLACE')
                else:
                    vgroup = obj.vertex_groups.new(membership[0])
                    skinGroupDict[membership[0]] = vgroup
                    vgroup.add([vertIdx], membership[1], 'REPLACE')

    def setObjectData(self, obj):
        Trimesh.setObjectData(self, obj)

        self.addSkinGroupsToObject(obj)

    def addWeightsToAscii(self, obj, asciiLines, exportObjects):
        # Get a list of skingroups for this object:
        # A vertex group is a skingroup if there is an object in the mdl
        # with the same name as the group
        skingroups = []
        for objName in exportObjects:
            if objName in obj.vertex_groups:
                skingroups.append(obj.vertex_groups[objName])

        vertexWeights = []
        for i, v in enumerate(obj.data.vertices):
            weights = []
            for group in skingroups:
                try:
                    weights.append([group.name, group.weight(i)])
                except:
                    # Vertex not part of this group
                    pass
            vertexWeights.append(weights)

        numVerts = len(obj.data.vertices)
        asciiLines.append('  weights ' + str(numVerts))
        for weights in vertexWeights:
            line = '  '
            if weights:
                for w in weights:
                    line += '  ' + w[0] + ' ' + str(round(w[1], 3))
            else:
                # No weights for this vertex ... this is a problem
                print('Neverblender - WARNING: Missing vertex weight in ' + obj.name)
                line = 'ERROR: no weight'
            asciiLines.append(line)


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        Trimesh.addDataToAscii(self, obj, asciiLines, exportObjects, classification)

        self.addWeightsToAscii(obj, asciiLines, exportObjects)


class Emitter(GeometryNode):
    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype = 'emitter'

        self.meshtype = nvb_def.Meshtype.EMITTER
        self.xsize    = 2
        self.ysize    = 2
        self.rawascii = ''


    def loadAscii(self, asciiNode):
        l_float = float
        l_isNumber = nvb_utils.isNumber

        for line in asciiNode:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if (label == 'node'):
                    self.name = nvb_utils.getName(line[2])
                    self.rawascii = self.rawascii + '\n' + ' '.join(line)
                elif (label == 'endnode'):
                    self.rawascii = self.rawascii + '\n' + ' '.join(line)
                    return
                elif (label == 'parent'):
                    self.parentName = nvb_utils.getName(line[1])
                    self.rawascii = self.rawascii + '\n  #' + ' '.join(line)
                elif (label == 'position'):
                    self.position = (l_float(line[1]),
                                     l_float(line[2]),
                                     l_float(line[3]))
                    self.rawascii = self.rawascii + '\n  #' + ' '.join(line)
                elif (label == 'orientation'):
                    self.orientation = (l_float(line[1]),
                                        l_float(line[2]),
                                        l_float(line[3]),
                                        l_float(line[4]))
                    self.rawascii = self.rawascii + '\n  #' + ' '.join(line)
                elif (label == 'scale'):
                    self.scale = l_float(line[1])
                    self.rawascii = self.rawascii + '\n  #' + ' '.join(line)
                elif (label == 'wirecolor'):
                    self.wirecolor = (l_float(line[1]),
                                      l_float(line[2]),
                                      l_float(line[3]))
                    self.rawascii = self.rawascii + '\n  #' + ' '.join(line)
                else:
                    self.rawascii = self.rawascii + '\n  ' + ' '.join(line)

    def createMesh(self, objName):
        # Create the mesh itself
        mesh = bpy.data.meshes.new(objName)
        mesh.vertices.add(4)
        mesh.vertices[0].co = ( self.xsize/2,  self.ysize/2, 0.0)
        mesh.vertices[1].co = ( self.xsize/2, -self.ysize/2, 0.0)
        mesh.vertices[2].co = (-self.xsize/2, -self.ysize/2, 0.0)
        mesh.vertices[3].co = (-self.xsize/2,  self.ysize/2, 0.0)
        mesh.tessfaces.add(1)
        mesh.tessfaces.foreach_set('vertices_raw', [0, 1, 2, 3])

        # After calling update() tessfaces become inaccessible
        mesh.validate()
        mesh.update()

        return mesh


    def addRawAscii(self, obj):
        txt = bpy.data.texts.new(obj.name)
        txt.write(self.rawascii)
        obj.nvb.rawascii = txt.name


    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)

        obj.nvb.meshtype = self.meshtype
        self.addRawAscii(obj)


    def addToScene(self, scene):
        if nvb_glob.minimapMode:
            # We don't need emitters in minimap mode
            # We may need it for the tree stucture, so import it as an empty
            return GeometryNode.addToScene(self, scene)

        mesh = self.createMesh(self.name)
        obj  = bpy.data.objects.new(self.name, mesh)

        self.setObjectData(obj)
        scene.objects.link(obj)
        return obj


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        GeometryNode.addDataToAscii(self, obj, asciiLines, exportObjects, classification, simple)

        if obj.nvb.rawascii not in bpy.data.texts:
            print('Neverblender - WARNING: No emitter data for ' + obj.name)
            return
        txt      = bpy.data.texts[obj.nvb.rawascii]
        txtLines = [l.split() for l in txt.as_string().split('\n')]
        for line in txtLines:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if (label == 'node') or (label  == 'endnode') or \
               (label == 'parent') or (label == 'position') or \
               (label == 'orientation') or (label == 'scale') or (label == 'wirecolor'):
                # We don't need any of this as we'll take it directly from
                # the object
                pass
            else:
                # We'll take everything that doesn't start with a #
                if label[0] != '#':
                    asciiLines.append('  ' + ' '.join(line))


class Light(GeometryNode):
    def __init__(self, name = 'UNNAMED'):
        GeometryNode.__init__(self, name)
        self.nodetype = 'light'

        self.shadow        = 1
        self.radius        = 5.0
        self.multiplier    = 1
        self.lightpriority = 5
        self.color         = (0.0, 0.0, 0.0)
        self.ambientonly   = 1
        self.ndynamictype  = 1
        self.isdynamic     = 1
        self.affectdynamic = 1
        self.negativelight = 0
        self.fadinglight   = 1
        self.lensflares    = 0
        self.flareradius   = 1.0
        self.flareList     = FlareList()

    def loadAscii(self, asciiNode):
        GeometryNode.loadAscii(self, asciiNode)

        flareTextureNamesStart = 0
        numFlares              = 0
        numVals                = 0

        l_int = int
        l_float = float
        l_isNumber = nvb_utils.isNumber
        for idx, line in enumerate(asciiNode):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue

            if not l_isNumber(label):
                if (label == 'radius'):
                    self.radius = l_float(line[1])
                elif (label == 'shadow'):
                    self.shadow = l_int(line[1])
                elif (label == 'multiplier'):
                    self.multiplier = l_float(line[1])
                elif (label == 'color'):
                    self.color = (l_float(line[1]),
                                  l_float(line[2]),
                                  l_float(line[3]))
                elif (label == 'ambientonly'):
                    self.ambientonly = l_int(line[1])
                elif (label == 'ndynamictype'):
                    self.ndynamictype = l_int(line[1])
                elif (label == 'isdynamic'):
                    self.isdynamic = l_int(line[1])
                elif (label == 'affectdynamic'):
                    self.affectdynamic = l_int(line[1])
                elif (label == 'negativelight'):
                    self.negativelight = l_int(line[1])
                elif (label == 'lightpriority'):
                    self.lightpriority = l_int(line[1])
                elif (label == 'fadinglight'):
                    self.fadinglight = l_int(line[1])
                elif (label == 'lensflares'):
                    self.lensflares = l_int(line[1])
                elif (label == 'flareradius'):
                    self.flareradius = l_float(line[1])
                elif (label == 'texturenames'):
                    # List of names follows, but we don't necessarily know how
                    # many flares there are
                    # We 'll need to read them later. For now save the index
                    flareTextureNamesStart = idx+1
                elif (label == 'flaresizes'):
                    # List of floats
                    numVals = next((i for i, v in enumerate(asciiNode[idx+1:]) if not l_isNumber(v[0])), -1)
                    nvb_parse.f1(asciiNode[idx+1:idx+numVals+1], self.flareList.sizes)
                    #self.flareList.sizes = [float(l[0]) for l in asciiNode[idx+1:idx+numVals+1]]
                elif (label == 'flarepositions'):
                    # List of floats
                    numVals = next((i for i, v in enumerate(asciiNode[idx+1:]) if not l_isNumber(v[0])), -1)
                    nvb_parse.f1(asciiNode[idx+1:idx+numVals+1], self.flareList.positions)
                    #self.flareList.positions = [float(l[0]) for l in asciiNode[idx+1:idx+numVals+1]]
                elif (label == 'flarecolorshifts'):
                    # List of float 3-tuples
                    numVals = next((i for i, v in enumerate(asciiNode[idx+1:]) if not l_isNumber(v[0])), -1)
                    nvb_parse.f3(asciiNode[idx+1:idx+numVals+1], self.flareList.colorshifts)
                    #self.flareList.colorshifts = [(float(l[0]), float(l[1]), float(l[2])) for l in asciiNode[idx+1:idx+numVals+1]]

        # Load flare texture names:
        numFlares = min(len(self.flareList.sizes),
                        min(len(self.flareList.colorshifts),
                            len(self.flareList.positions)))
        for i in range(numFlares):
            texName = asciiNode[flareTextureNamesStart+i][0]
            self.flareList.textures.append(texName)

    def createLamp(self, name):
        lamp = bpy.data.lamps.new(name, 'POINT')

        # TODO: Check for negative color values and do something (works fine in blender though)
        lamp.color       = self.color
        lamp.energy      = self.multiplier
        lamp.distance    = self.radius
        #lamp.use_sphere  = True

        return lamp

    def setObjectData(self, obj):
        GeometryNode.setObjectData(self, obj)

        switch = {'ml1': 'MAINLIGHT1',
                  'ml2': 'MAINLIGHT2',
                  'sl1': 'SOURCELIGHT1',
                  'sl2': 'SOURCELIGHT2'}
        #TODO: Check light names when exporting tiles
        obj.nvb.ambientonly   = (self.ambientonly >= 1)
        obj.nvb.lighttype     = switch.get(self.name[-3:], 'NONE')
        obj.nvb.shadow        = (self.shadow >= 1)
        obj.nvb.lightpriority = self.lightpriority
        obj.nvb.fadinglight   = (self.fadinglight >= 1)
        obj.nvb.isdynamic     = (self.ndynamictype >= 1) or (self.isdynamic >= 1)
        obj.nvb.affectdynamic = (self.affectdynamic >= 1)

        if (self.flareradius > 0) or (self.lensflares >= 1):
            obj.nvb.lensflares = True
            numFlares = len(self.flareList.textures)
            for i in range(numFlares):
                newItem = obj.nvb.flareList.add()
                newItem.texture    = self.flareList.textures[i]
                newItem.colorshift = self.flareList.colorshifts[i]
                newItem.size       = self.flareList.sizes[i]
                newItem.position   = self.flareList.positions[i]

        obj.nvb.flareradius = self.flareradius

    def addToScene(self, scene):
        if nvb_glob.minimapMode:
            # We don't need lights in minimap mode
            # We may need it for the tree stucture, so import it as an empty
            return GeometryNode.addToScene(self, scene)
        lamp = self.createLamp(self.name)
        obj  = bpy.data.objects.new(self.name, lamp)
        self.setObjectData(obj)
        scene.objects.link(obj)
        return obj

    def addFlaresToAscii(self, obj, asciiLines):
        if obj.nvb.lensflares:
            asciiLines.append('  lensflares ' + str(int(obj.nvb.lensflares)))
            # print(str(len(obj.nvb.flareList)))
            if len(obj.nvb.flareList) > 0:

                # TODO: Clean this up
                asciiLines.append('  texturenames zd')
                for flare in obj.nvb.flareList:
                    asciiLines.append('    ' + flare.texture)
                asciiLines.append('  flarepositions zd')
                for flare in obj.nvb.flareList:
                    asciiLines.append('    ' + str(round(flare.position, 7)))
                asciiLines.append('  flaresizes zd')
                for flare in obj.nvb.flareList:
                    asciiLines.append('    ' + str(flare.size))
                asciiLines.append('  flarecolorshifts zd')
                for flare in obj.nvb.flareList:
                    asciiLines.append('    ' +  str(round(flare.colorshift[0], 2)) + ' ' +
                                                str(round(flare.colorshift[1], 2)) + ' ' +
                                                str(round(flare.colorshift[2], 2)) )
        asciiLines.append('  flareradius ' + str(round(obj.nvb.flareradius, 1)))

    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        GeometryNode.addDataToAscii(self, obj, asciiLines, exportObjects, classification)

        lamp = obj.data
        asciiLines.append('  radius ' + str(round(lamp.distance, 1)))
        asciiLines.append('  multiplier ' + str(round(lamp.energy, 1)))
        asciiLines.append('  color ' +  str(round(lamp.color[0], 2)) + ' ' +
                                        str(round(lamp.color[1], 2)) + ' ' +
                                        str(round(lamp.color[2], 2)) )
        asciiLines.append('  ambientonly ' + str(int(obj.nvb.ambientonly)))
        asciiLines.append('  nDynamicType ' + str(int(obj.nvb.isdynamic)))
        asciiLines.append('  affectDynamic ' + str(int(obj.nvb.affectdynamic)))
        asciiLines.append('  shadow ' + str(int(obj.nvb.shadow)))
        asciiLines.append('  lightpriority ' + str(obj.nvb.lightpriority))
        asciiLines.append('  fadingLight ' + str(int(obj.nvb.fadinglight)))
        self.addFlaresToAscii(obj, asciiLines)


class Aabb(Trimesh):
    '''
    No need to import Aaabb's. Aabb nodes in mdl files will be
    treated as trimeshes
    '''
    def __init__(self, name = 'UNNAMED'):
        Trimesh.__init__(self, name)
        self.nodetype = 'aabb'

        self.meshtype = nvb_def.Meshtype.AABB

    def addAABBToAscii(self, obj, asciiLines):
        walkmesh = obj.to_mesh(nvb_glob.scene, nvb_glob.applyModifiers, nvb_glob.meshConvert)

        faceList = []
        faceIdx  = 0
        for tessface in walkmesh.tessfaces:
            if (len(tessface.vertices) == 3):
                # Tri
                v0 = tessface.vertices[0]
                v1 = tessface.vertices[1]
                v2 = tessface.vertices[2]

                centroid = mathutils.Vector((walkmesh.vertices[v0].co + walkmesh.vertices[v1].co + walkmesh.vertices[v2].co)/3)
                faceList.append((faceIdx, [walkmesh.vertices[v0].co, walkmesh.vertices[v1].co, walkmesh.vertices[v2].co], centroid))
                faceIdx += 1

            elif (len(tessface.vertices) == 4):
                # Quad
                v0 = tessface.vertices[0]
                v1 = tessface.vertices[1]
                v2 = tessface.vertices[2]
                v3 = tessface.vertices[3]

                centroid = mathutils.Vector((walkmesh.vertices[v0].co + walkmesh.vertices[v1].co + walkmesh.vertices[v2].co)/3)
                faceList.append((faceIdx, [walkmesh.vertices[v0].co, walkmesh.vertices[v1].co, walkmesh.vertices[v2].co], centroid))
                faceIdx += 1

                centroid = mathutils.Vector((walkmesh.vertices[v2].co + walkmesh.vertices[v3].co + walkmesh.vertices[v0].co)/3)
                faceList.append((faceIdx, [walkmesh.vertices[v2].co, walkmesh.vertices[v3].co, walkmesh.vertices[v0].co], centroid))
                faceIdx += 1
            else:
                # Ngon or no polygon at all (This should never be the case with tessfaces)
                print('Neverblender - WARNING: Ngon in walkmesh. Unable to generate aabb.')
                return

        aabbTree = []
        nvb_aabb.generateTree(aabbTree, faceList)

        l_round = round
        if aabbTree:
            node = aabbTree.pop(0)
            asciiLines.append('  aabb  ' +
                              ' ' +
                              str(l_round(node[0], 7)) +
                              ' ' +
                              str(l_round(node[1], 7)) +
                              ' ' +
                              str(l_round(node[2], 7)) +
                              ' ' +
                              str(l_round(node[3], 7)) +
                              ' ' +
                              str(l_round(node[4], 7)) +
                              ' ' +
                              str(l_round(node[5], 7)) +
                              ' ' +
                              str(node[6]))
            for node in aabbTree:
                asciiLines.append('    ' +
                                  str(l_round(node[0], 7)) +
                                  ' ' +
                                  str(l_round(node[1], 7)) +
                                  ' ' +
                                  str(l_round(node[2], 7)) +
                                  ' ' +
                                  str(l_round(node[3], 7)) +
                                  ' ' +
                                  str(l_round(node[4], 7)) +
                                  ' ' +
                                  str(l_round(node[5], 7)) +
                                  ' ' +
                                  str(node[6]) )


    def addDataToAscii(self, obj, asciiLines, exportObjects = [], classification = nvb_def.Classification.UNKNOWN, simple = False):
        if obj.parent:
            asciiLines.append('  parent ' + obj.parent.name)
        else:
            asciiLines.append('  parent ' + nvb_def.null)
        loc = obj.location
        asciiLines.append('  position ' + str(round(loc[0], 7)) + ' ' +
                                          str(round(loc[1], 7)) + ' ' +
                                          str(round(loc[2], 7)) )
        rot = nvb_utils.getAuroraRotFromObject(obj)
        asciiLines.append('  orientation ' + str(round(rot[0], 7)) + ' ' +
                                             str(round(rot[1], 7)) + ' ' +
                                             str(round(rot[2], 7)) + ' ' +
                                             str(round(rot[3], 7)) )
        color = obj.nvb.wirecolor
        asciiLines.append('  wirecolor ' + str(round(color[0], 2)) + ' ' +
                                           str(round(color[1], 2)) + ' ' +
                                           str(round(color[2], 2))  )
        asciiLines.append('  ambient 1.0 1.0 1.0')
        asciiLines.append('  diffuse 1.0 1.0 1.0')
        asciiLines.append('  specular 0.0 0.0 0.0')
        asciiLines.append('  shininess 0')
        asciiLines.append('  bitmap NULL')
        Trimesh.addMeshDataToAscii(self, obj, asciiLines, simple)
        self.addAABBToAscii(obj, asciiLines)


    def createMesh(self, name):
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(self.verts))
        mesh.vertices.foreach_set('co', unpack_list(self.verts))
        mesh.tessfaces.add(len(self.facelist.faces))
        mesh.tessfaces.foreach_set('vertices_raw', unpack_face_list(self.facelist.faces))

        # Create materials
        for wokMat in nvb_def.wok_materials:
            matName = wokMat[0]
            # Walkmesh materials will be shared across multiple walkmesh
            # objects
            if matName in bpy.data.materials:
                material = bpy.data.materials[matName]
            else:
                material = bpy.data.materials.new(matName)
                material.diffuse_color      = wokMat[1]
                material.diffuse_intensity  = 1.0
                material.specular_color     = (0.0,0.0,0.0)
                material.specular_intensity = wokMat[2]
            mesh.materials.append(material)

        # Apply the walkmesh materials to each face
        for idx, face in enumerate(mesh.tessfaces):
            face.material_index = self.facelist.matId[idx]

        mesh.update()
        return mesh


    def addToScene(self, scene):
        if nvb_glob.minimapMode:
            # No walkmeshes in minimap mode and we don't need an empty as
            # replacement either as AABB nodes never have children
            return GeometryNode.addToScene(self, scene)
        mesh = self.createMesh(self.name)
        obj = bpy.data.objects.new(self.name, mesh)
        self.setObjectData(obj)
        scene.objects.link(obj)
        return obj
