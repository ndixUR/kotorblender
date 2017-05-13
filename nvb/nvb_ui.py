import bpy

from . import nvb_def

class NVB_UILIST_LIGHTFLARES(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'NONE'

        # Supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(item.texture, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label('', icon = custom_icon)


class NVB_UILIST_ANIMEVENTS(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'NONE'

        # Supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label('', icon = custom_icon)


class NVB_PANEL_EMPTY(bpy.types.Panel):
    '''
    Property panel for additional properties needed for the mdl file
    format. This is only available for EMPTY objects.
    It is located under the object data panel in the properties window
    '''
    bl_idname = 'nvb.propertypanel.object'
    bl_label = 'Odyssey Dummy Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'EMPTY')

    def draw(self, context):
        obj    = context.object
        layout = self.layout

        row = layout.row()
        row.prop(obj.nvb, 'dummytype', text='Type')
        sep = layout.separator()

        # Display properties depending on type of the empty
        if (obj.nvb.dummytype == nvb_def.Dummytype.MDLROOT):
            if not obj.nvb.isanimation:
                # Animation Helper. Creates a new scene, copies all objects to it
                # and renames them
                row = layout.row()
                box = row.box()
                row = box.row()
                row.prop(obj.nvb, 'isanimation', text = 'Animation')
                sub = row.row()
                sub.enabled = False
                sub.prop(obj.nvb, 'animname', text = '')
                row = box.row(align = True)
                row.prop(obj.nvb, 'newanimname', text = 'Create')
                row.operator('nvb.animscene_add', text = '', icon='ZOOMIN')

                sep = layout.separator()

                row = layout.row()
                box = row.box()
                split = box.split()
                col = split.column()
                col.label(text = 'Classification:')
                col.label(text = 'Supermodel:')
                col.label(text = 'Animation Scale:')
                col = split.column()
                col.prop(obj.nvb, 'classification', text = '')
                col.prop(obj.nvb, 'supermodel', text = '')
                col.prop(obj.nvb, 'animscale', text = '')

                sep = layout.separator()

                # Minimap Helper.
                row = layout.row()
                box = row.box()
                box.label(text = 'Minimap Helper')
                row = box.row()
                row.prop(obj.nvb, 'minimapzoffset', text = 'z Offset')
                row = box.row()
                row.prop(obj.nvb, 'minimapsize', text = 'Minimap size')
                row = box.row()
                row.operator('nvb.render_minimap', text = 'Render Minimap', icon='NONE')
            else:
                # MDL Rootdummy in an animation scene
                row = layout.row()
                box = row.box()
                row = box.row()
                row.prop(obj.nvb, 'isanimation', text = 'Animation')
                sub = row.row()
                sub.enabled = False
                sub.prop(obj.nvb, 'animname', text = '')
                row = box.row(align = True)
                row.prop(obj.nvb, 'newanimname', text = 'Rename/Copy')
                row.operator('nvb.animscene_rename', text = '', icon='FILE_REFRESH')
                row.operator('nvb.animscene_add', text = '', icon='ZOOMIN')
                row = box.row()
                row.prop_search(obj.nvb, 'animroot', bpy.data, 'objects', text = 'Root')
                row = box.row()
                row.prop(obj.nvb, 'transtime')

                sep = layout.separator()
                # Event Helper. Display and add/remove events.
                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text = 'Event List')

                row = box.row()
                row.template_list('NVB_UILIST_ANIMEVENTS', 'The_List', obj.nvb, 'eventList', obj.nvb, 'eventListIdx')
                col = row.column(align = True)
                col.operator('nvb.animevent_new', text = '', icon='ZOOMIN')
                col.operator('nvb.animevent_delete', text = '', icon='ZOOMOUT')
                col.separator()
                col.operator('nvb.animevent_move', icon='TRIA_UP', text = '').direction = 'UP'
                col.operator('nvb.animevent_move', icon='TRIA_DOWN', text = '').direction = 'DOWN'
                if obj.nvb.eventListIdx >= 0 and len(obj.nvb.eventList) > 0:
                    item = obj.nvb.eventList[obj.nvb.eventListIdx]
                    row = box.row()
                    row.prop(item, 'name')
                    row.prop(item, 'frame')

        elif (obj.nvb.dummytype == nvb_def.Dummytype.PWKROOT):
            pass

        elif (obj.nvb.dummytype == nvb_def.Dummytype.DWKROOT):
            pass

        elif (obj.nvb.dummytype == nvb_def.Dummytype.REFERENCE):
            row = layout.row()
            box = row.box()

            row = box.row()
            row.prop(obj.nvb, 'refmodel')
            row = box.row()
            row.prop(obj.nvb, 'reattachable')

        else:
            row = layout.row()
            box = row.box()

            row = box.row()
            row.prop(obj.nvb, 'wirecolor')
            row = box.row()
            row.prop(obj.nvb, 'dummysubtype')


class NVB_PANEL_LIGHT(bpy.types.Panel):
    '''
    Property panel for additional light or lamp properties. This
    holds all properties not supported by blender at the moment,
    but used by OpenGL and the aurora engine. This is only available
    for LAMP objects.
    It is located under the object data panel in the properties window
    '''
    bl_idname = 'nvb.propertypanel.light'
    bl_label = 'Odyssey Light Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'LAMP')

    def draw(self, context):
        obj    = context.object
        layout = self.layout

        row = layout.row()
        row.prop(obj.nvb, 'lighttype', text='Type')

        sep = layout.separator()

        row = layout.row()
        box = row.box()

        row = box.row()
        row.prop(obj.nvb, 'wirecolor', text='Wirecolor')
        row = box.row()
        row.prop(obj.nvb, 'lightpriority', text='Priority')

        split = box.split()
        col = split.column(align=True)
        col.prop(obj.nvb, 'ambientonly', text='Ambient Only')
        col.prop(obj.nvb, 'shadow', text='Shadows')
        col = split.column(align=True)
        col.prop(obj.nvb, 'fadinglight', text='Fading')
        col.prop(obj.nvb, 'isdynamic', text='Is dynamic')
        col.prop(obj.nvb, 'affectdynamic', text='Affect dynamic')

        sep = layout.separator()

        # Lens flares
        row = layout.row()
        row.enabled = (obj.nvb.lighttype == 'NONE')
        box = row.box()
        row = box.row()
        row.prop(obj.nvb, 'lensflares')
        sub = row.row(align=True)
        sub.active = obj.nvb.lensflares
        sub.prop(obj.nvb, 'flareradius', text='Radius')
        row = box.row()
        row.active = obj.nvb.lensflares
        row.template_list('NVB_UILIST_LIGHTFLARES', 'The_List', obj.nvb, 'flareList', obj.nvb, 'flareListIdx')
        col = row.column(align = True)
        col.operator('nvb.lightflare_new', icon='ZOOMIN', text = '')
        col.operator('nvb.lightflare_delete', icon='ZOOMOUT', text = '')
        col.separator()
        col.operator('nvb.lightflare_move', icon='TRIA_UP', text = '').direction = 'UP'
        col.operator('nvb.lightflare_move', icon='TRIA_DOWN', text = '').direction = 'DOWN'
        if obj.nvb.flareListIdx >= 0 and len(obj.nvb.flareList) > 0:
            item = obj.nvb.flareList[obj.nvb.flareListIdx]
            row = box.row()
            row.active = obj.nvb.lensflares
            row.prop(item, 'texture')
            row = box.row()
            row.active = obj.nvb.lensflares
            row.prop(item, 'colorshift')
            row = box.row()
            row.active = obj.nvb.lensflares
            row.prop(item, 'size')
            row.prop(item, 'position')



class NVB_PANEL_MESH(bpy.types.Panel):
    '''
    Property panel for additional mesh properties. This
    holds all properties not supported by blender at the moment,
    but used by OpenGL and the aurora engine. This is only available
    for MESH objects.
    It is located under the object data panel in the properties window
    '''
    bl_idname = 'nvb.propertypanel.mesh'
    bl_label = 'Odyssey Mesh Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'MESH') #context.mesh and context.object.type != 'EMPTY')

    def draw(self, context):
        obj      = context.object
        obj_type = obj.type
        layout   = self.layout

        row = layout.row()
        row.prop(obj.nvb, 'meshtype', text='Type')

        sep = layout.separator()

        if (obj.nvb.meshtype == nvb_def.Meshtype.EMITTER):
            row = layout.row()
            box = row.box()

            row = box.row()
            row.prop(obj.nvb, 'wirecolor', text='Wirecolor')
            row = box.row()
            row.prop_search(obj.nvb, 'rawascii', bpy.data, 'texts', text='Data')

        else: # Trimesh, danglymesh, skin
            row = layout.row()
            box = row.box()

            row = box.row()
            row.prop(obj.nvb, 'wirecolor', text='Wirecolor')
            row = box.row()
            row.prop(obj.nvb, 'selfillumcolor', text='Selfillum. color')
            row = box.row()
            row.prop(obj.nvb, 'ambientcolor', text='Ambient')

            row = box.row()
            row.prop(obj.nvb, 'shininess', text='Shininess')
            split = box.split()
            col = split.column()
            col.prop(obj.nvb, 'render', text='Render')
            col.prop(obj.nvb, 'shadow', text='Shadow')
            col.prop(obj.nvb, 'lightmapped', text='Lightmapped')
            col = split.column()
            col.prop(obj.nvb, 'beaming', text='Beaming')
            col.prop(obj.nvb, 'inheritcolor', text='Inherit Color')
            col.prop(obj.nvb, 'rotatetexture', text='Rotate Texture')

            row = box.row()
            row.prop(obj.nvb, 'transparencyhint', text='Transparency Hint')
            row = box.row()
            row.label(text = 'Smoothgroups')
            row.prop(obj.nvb, 'smoothgroup', text='Smooth Group', expand = True)

            # Additional props for danglymeshes
            if (obj.nvb.meshtype == nvb_def.Meshtype.DANGLYMESH):
                sep = layout.separator()

                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text = 'Danglymesh Properties')
                row = box.row()
                row.prop_search(obj.nvb, 'constraints', obj, 'vertex_groups', text='Constraints')
                row = box.row()
                row.prop(obj.nvb, 'period', text='Period')
                row = box.row()
                row.prop(obj.nvb, 'tightness', text='Tightness')
                row = box.row()
                row.prop(obj.nvb, 'displacement', text='Displacement')

            # Additional props for skins
            elif (obj.nvb.meshtype == nvb_def.Meshtype.SKIN):
                sep = layout.separator()

                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text = 'Create vertex group: ')
                row = box.row(align = True)
                row.prop_search(obj.nvb, 'skingroup_obj', context.scene, 'objects')
                row.operator('nvb.skingroup_add', text = '', icon='ZOOMIN')

            # Additional props for aabb walkmeshes
            elif (obj.nvb.meshtype == nvb_def.Meshtype.AABB):
                sep = layout.separator()

                row = layout.row()
                box = row.box()
                row = box.row()
                row.operator('nvb.load_wok_mats', text = 'Load walkmesh materials', icon='NONE')
                row = box.row()
                row.label(text = '(Warning: Removes current materials)')
