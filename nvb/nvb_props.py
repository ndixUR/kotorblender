import bpy
from . import nvb_def


def nvb_update_shadow_prop(self, context):
    '''
    Set the lamps shadow to match the aurora shadow property
    '''
    select_object = context.object
    if (select_object) and (select_object.type == 'LAMP'):
        try:
            if (select_object.nvb.shadow):
                select_object.data.shadow_method = 'RAY_SHADOW'
            else:
                select_object.data.shadow_method = 'NOSHADOW'
        except:
            pass


class NVB_PG_ANIMEVENT(bpy.types.PropertyGroup):
    '''
    Properties for a single event in the even list
    '''

    name = bpy.props.StringProperty(
           name = 'Name',
           description = 'Name for this event',
           default = 'Unnamed')

    frame = bpy.props.IntProperty(
           name = 'Frame',
           description = 'Frame at which the event should fire',
           default = 1)


class NVB_PG_FLARE(bpy.types.PropertyGroup):
    '''
    Properties for a single flare in the flare list
    '''

    texture = bpy.props.StringProperty(name = 'Texture',
                                       description = 'Texture name',
                                       default = nvb_def.null)
    size = bpy.props.FloatProperty(name = 'Size',
                                 description = 'Flare size',
                                 default = 1)
    position = bpy.props.FloatProperty(name = 'Position',
                                       description = 'Flare position',
                                       default = 1)
    colorshift = bpy.props.FloatVectorProperty( name = 'Colorshift',
                                                description = 'Colorshift',
                                                subtype = 'COLOR_GAMMA',
                                                default = (0.0, 0.0, 0.0),
                                                min = -1.0, max = 1.0,
                                                soft_min = 0.0, soft_max = 1.0)


class NVB_PG_OBJECT(bpy.types.PropertyGroup):
    '''
    This class defines all additional properties needed by the mdl file
    format. It hold the properties for meshes, lamps and empties.
    '''

    # For all objects
    wirecolor = bpy.props.FloatVectorProperty(name = 'Wirecolor',
                                              description = 'Color of the wireframe',
                                              subtype = 'COLOR_GAMMA',
                                              default = (1.0, 1.0, 1.0),
                                              min = 0.0, max = 1.0,
                                              soft_min = 0.0, soft_max = 1.0)
    imporder = bpy.props.IntProperty(name = "Order of Import", default = 0)

    # For all emptys
    dummytype  = bpy.props.EnumProperty(name = 'Type',
                                        items = [(nvb_def.Dummytype.NONE,      'None',                'Simple dummy object',                                        0), \
                                                 (nvb_def.Dummytype.DWKROOT,   'DWK Rootdummy',       'All children are considered part of a door walkmesh',        1), \
                                                 (nvb_def.Dummytype.MDLROOT,   'MDL Rootdummy',       'All children are considered part of a mdl',                  2), \
                                                 (nvb_def.Dummytype.PWKROOT,   'PWK Rootdummy',       'All children are considered part of a placeable walkmesh',   3), \
                                                 (nvb_def.Dummytype.REFERENCE, 'Reference node',      'Used in spells. Points to "fx_ref" by default',              4), \
                                                 (nvb_def.Dummytype.PATCH,     'Patch node',          'Used in spells. Unknown purpose. ',                          5) ],
                                        default = nvb_def.Dummytype.NONE)
    # For MDL Rootdummy
    supermodel     = bpy.props.StringProperty(name = 'Supermodel', description = 'Name of the model to inherit animations from', default = nvb_def.null)
    classification = bpy.props.EnumProperty(name  = 'Classification',
                                            items = [ (nvb_def.Classification.UNKNOWN,   'Unknown',   'Unknown classification',              0), \
                                                      (nvb_def.Classification.EFFECT,    'Effect',    'Effects',                             1), \
                                                      (nvb_def.Classification.TILE,      'Tile',      'Tiles for a tileset',                 2), \
                                                      (nvb_def.Classification.CHARACTER, 'Character', 'Creatures, characters or placeables', 4), \
                                                      (nvb_def.Classification.DOOR,      'Door',      'Doors',                               8), \
                                                      (nvb_def.Classification.SABER,     'Lightsaber','Lightsaber weapon',                   16), \
                                                      (nvb_def.Classification.ITEM,      'Placeable', 'Items or placeables',                 32) ],
                                            default = nvb_def.Classification.UNKNOWN)
    dummysubtype   = bpy.props.EnumProperty(name = 'Subtype',
                                            items = [('NONE', 'None',            'Simple dummy object',                     0), \
                                                     ('HAND', 'Hand',            'Hand node for spells and effects. \n (for door and placeable models)',        1), \
                                                     ('HEAD', 'Head',            'Head node for spells and effects. \n (for door and placeable models)',        2), \
                                                     ('HHIT', 'Head hit',        'Head hit node for spells and effects. \n (for door and placeable models)',    3), \
                                                     ('IMPC', 'Impact',          'Impact node for spells and effects. \n (for door and placeable models)',      4), \
                                                     ('GRND', 'Ground',          'Ground node for spells and effects. \n (for door and placeable models)',      5), \
                                                     ('USE1', 'PWK: Use 1',      '1st node for "Use" animation',            6), \
                                                     ('USE2', 'PWK: Use 2',      '2nd node for "Use" animation',            7), \
                                                     ('O101', 'DWK: Open 1 1st', 'Open 1 State, 1st node for "Use" anim',   8), \
                                                     ('O102', 'DWK: Open 1 2nd', 'Open 1 State, 2nd node for "Use" anim',   9), \
                                                     ('O201', 'DWK: Open 2 1st', 'Open 2 State, 1st node for "Use" anim',  10), \
                                                     ('O202', 'DWK: Open 2 2nd', 'Open 2 State, 2nd node for "Use" anim',  11), \
                                                     ('CL01', 'DWK: Closed 1st', 'Closed State, 1st node for "Use" anim',  12), \
                                                     ('CL02', 'DWK: Closed 2nd', 'Closed State, 2nd node for "Use" anim',  13) ],
                                            default = 'NONE')
    animscale   = bpy.props.FloatProperty(name = 'Animationscale', description = 'Animation scale for all animations', default = 1.00, min = 0.0)
    isanimation = bpy.props.BoolProperty(name = 'Animation', description = 'Whether this dummy and it\'s children are in an animation scene', default = False)
    # For MDL Rootdummies in animations
    animname     = bpy.props.StringProperty(name = 'Animation name', description = 'Name of the animation', default = '')
    newanimname  = bpy.props.StringProperty(name = 'New name', description = 'Name of the new animation', default = '')
    transtime    = bpy.props.FloatProperty(name = 'Transitiontime', description = 'Used for for animations only. Set for each Scene individually', default = 1.00, min = 0.0)
    animroot     = bpy.props.StringProperty(name = 'Animation Root', description = 'Entry point of the animation', default = '')
    eventList    = bpy.props.CollectionProperty(type = NVB_PG_ANIMEVENT)
    eventListIdx = bpy.props.IntProperty(name = "Index for event List", default = 0)
    # For reference emptys
    refmodel     = bpy.props.StringProperty(name = 'Reference Model', description = 'Name of another mdl file', default = 'fx_ref')
    reattachable = bpy.props.BoolProperty(name = 'Reattachable', default = False)
    # Minimap generation
    minimapzoffset = bpy.props.FloatProperty(name = 'Minimap Z Offset', default = 0.00, min = 0.00)
    minimapsize    = bpy.props.IntProperty(name = 'Size', default = 512, min = 16)

    # For mesh objects
    meshtype   = bpy.props.EnumProperty(name = 'Type',
                                        items = [   (nvb_def.Meshtype.TRIMESH, 'Trimesh', '0 desc', 0), \
                                                    (nvb_def.Meshtype.DANGLYMESH, 'Danglymesh', '1 desc', 1), \
                                                    (nvb_def.Meshtype.SKIN, 'Skinmesh', '2 desc', 2), \
                                                    (nvb_def.Meshtype.AABB, 'AABB Walkmesh', '3 desc', 3), \
                                                    (nvb_def.Meshtype.EMITTER, 'Emitter', '4 desc', 4)],
                                        default = nvb_def.Meshtype.TRIMESH)
    smoothgroup    = bpy.props.EnumProperty(name = 'Smoothgroup',
                                            items = [   ('SEPR', 'Seperate', 'All faces have their own smoothgroup',   0),
                                                        ('NONE', 'Single', 'All Faces belong to the same smoothgroup', 1),
                                                        ('AUTO', 'Auto',   'Generate smoothgroups either from edges marked as sharp or edge angles when no sharp edges are present',  2)
                                                         ],
                                            default = 'SEPR')

    shadow           = bpy.props.BoolProperty(name = 'Shadow', description = 'Whether to cast shadows', default = True, update=nvb_update_shadow_prop)
    tilefade         = bpy.props.BoolProperty(name = 'Tilefade', description = 'Object will fade when the player is nearby. (Tilesets only)', default = False)
    render           = bpy.props.BoolProperty(name = 'Render', description = 'Whether to render this object in the scene', default = True)
    lightmapped      = bpy.props.BoolProperty(name = 'Lightmapped', description = 'Whether this object has shading baked into a lightmap', default = False)
    beaming          = bpy.props.BoolProperty(name = 'beaming', description = 'Object casts beams (?)', default = False)
    inheritcolor     = bpy.props.BoolProperty(name = 'Inheritcolor', description = 'Unused (?)', default = False)
    rotatetexture    = bpy.props.BoolProperty(name = 'Rotatetexture', description = 'Automatically rotates texture to prevent seams', default = False)
    transparencyhint = bpy.props.IntProperty(name = 'Transparency Hint', default = 0, min = 0, max = 32)
    selfillumcolor   = bpy.props.FloatVectorProperty(name = 'Selfilluminationcolor',
                                                     description = 'Makes the object seem to glow but does not emit light',
                                                     subtype = 'COLOR_GAMMA',
                                                     default = (0.0, 0.0, 0.0),
                                                     min = 0.0, max = 1.0,
                                                     soft_min = 0.0, soft_max = 1.0)
    ambientcolor     = bpy.props.FloatVectorProperty(name = 'Ambientcolor',
                                                     description = 'Ambient color',
                                                     subtype = 'COLOR_GAMMA',
                                                     default = (1.0, 1.0, 1.0),
                                                     min = 0.0, max = 1.0,
                                                     soft_min = 0.0, soft_max = 1.0)
    shininess        = bpy.props.IntProperty(name = 'Shininess', default = 1, min = 0, max = 32)
    lytposition      = bpy.props.FloatVectorProperty(name = 'Layout Position',
                                                     description = 'Room position in LYT file.',
                                                     subtype = 'XYZ',
                                                     default = (0.0, 0.0, 0.0))

    # For danglymeshes
    period       = bpy.props.FloatProperty(name = 'Period', default = 1.0, min = 0.0, max = 32.0)
    tightness    = bpy.props.FloatProperty(name = 'Tightness', default = 1.0, min = 0.0, max = 32.0)
    displacement = bpy.props.FloatProperty(name = 'Displacement', default = 0.5, min = 0.0, max = 32.0)
    constraints  = bpy.props.StringProperty(name = 'Danglegroup', description = 'Name of the vertex group to use for the danglymesh', default = '')

    # For skingroups
    skingroup_obj = bpy.props.StringProperty(name = 'Bone', description = 'Name of the bone to create the skingroup for', default = '')

    # For lamps
    lighttype     = bpy.props.EnumProperty(name = 'Type', items=[('NONE', 'None', 'Simple light', 0), ('MAINLIGHT1', 'Mainlight 1', 'Mainlight for Tiles (Editable in toolset)', 1), ('MAINLIGHT2', 'Mainlight 2', 'Mainlight for Tiles (Editable in toolset)', 2), ('SOURCELIGHT1', 'Sourcelight 1', 'Editable in toolset', 3), ('SOURCELIGHT2', 'Sourcelight 2', 'Editable in toolset', 4)], default = 'NONE')
    ambientonly   = bpy.props.BoolProperty(name = 'Ambient Only', default = False)
    lightpriority = bpy.props.IntProperty(name = 'Lightpriority', default = 3, min = 1, max = 5)
    fadinglight   = bpy.props.BoolProperty(name = 'Fading light', default = False)
    isdynamic     = bpy.props.BoolProperty(name = 'Is Dynamic', default = False)
    affectdynamic = bpy.props.BoolProperty(name = 'Affect Dynamic', description = 'Affect dynamic objects', default = False)
    negativelight = bpy.props.BoolProperty(name = 'Negative Light', default = False)
    lensflares    = bpy.props.BoolProperty(name = 'Lensflares', default = False)
    flareradius   = bpy.props.FloatProperty(name = 'Flare Radius', default = 0.0, min = 0.0, max = 100.0)
    flareList     = bpy.props.CollectionProperty(type = NVB_PG_FLARE)
    flareListIdx  = bpy.props.IntProperty(name = "Index for flare list", default = 0)

    # For emitters
    rawascii = bpy.props.StringProperty(name = 'Text node', description = 'Name of the raw text node', default = '')
