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


class NVB_PANEL_TEXTURE(bpy.types.Panel):
    """Texture properties panel, mostly for managing TXI files"""
    bl_idname = 'nvb.propertypanel.texture'
    bl_label = 'Odyssey Texture Properties'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'texture'

    @classmethod
    def poll(cls, context):
        try:
            # yes for image textures
            return context.object.active_material.active_texture.image
        except:
            return False

    def draw_summ_prop(self, texture, layout, propname):
        """UI Summary prop entries which include default-reset control"""
        row = layout.row(align=True)
        row.prop(texture.nvb, propname)
        prop_names = [o.name for o in texture.nvb.modified_properties]
        if propname in prop_names:
            row.label(icon='FILE_TICK')
            op = row.operator('nvb.texture_info_ops', text='', icon='X', emboss=False)
            op.action = 'RESET'
            op.propname = propname
        else:
            row.label(icon='RADIOBUT_OFF')

    def draw_box_header(self, texture, layout, boxname, text):
        """UI Title and visibility toggle for texture property sub-groups"""
        row = layout.row()
        row.alignment = 'LEFT'
        state = getattr(texture.nvb, 'box_visible_' + boxname)
        if not state:
            row.operator('nvb.texture_info_box_ops', text=text, icon="TRIA_RIGHT", emboss=False).boxname = boxname
            return False
        else:
            row.operator('nvb.texture_info_box_ops', text=text, icon="TRIA_DOWN", emboss=False).boxname = boxname
            return True

    def draw(self, context):
        layout = self.layout
        texture = context.object.active_material.active_texture
        #print(dir(context))
        #print(dir(context.object))
        self.layout.prop(context.object.active_material.active_texture.nvb, 'bumpmapped', text='Allow Normal Mapping')
        #self.layout.prop(context.object.nvb, 'bumpmapped', text='Bumpmapped')

        # TXI file operations
        row = layout.row(align=True)
        row.operator('nvb.texture_info_io', text=" Import", icon='FILESEL').action = 'LOAD'
        row.operator('nvb.texture_info_io', text=" Export", icon='SAVE_COPY').action = 'SAVE'

        # Texture type
        if len(texture.nvb.modified_properties):
            box = layout.row().box()
            #row = box.row()
            #row.alignment = 'LEFT'
            #row.label(text="TXI File Summary")
            #row.operator('nvb.texture_info_box_ops', text="TXI File Summary", icon="TRIA_DOWN", emboss=False)
            #bbif not texture.nvb.box_visible_summary:
            #    row.operator('nvb.texture_info_box_ops', text="TXI File Summary", icon="TRIA_RIGHT", emboss=False).boxname = 'summary'
            #else:
            #    row.operator('nvb.texture_info_box_ops', text="TXI File Summary", icon="TRIA_DOWN", emboss=False).boxname = 'summary'
            if self.draw_box_header(texture, box, 'summary', 'TXI File Summary'):
                for propname in texture.nvb.modified_properties:
                    self.draw_summ_prop(texture, box, propname.name)

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'textures', 'Shader Textures'):
            box.prop(texture.nvb, 'envmaptexture')
            box.prop(texture.nvb, 'bumpmaptexture')
            box.prop(texture.nvb, 'bumpyshinytexture')

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'procedural', 'Procedural Properties'):
            box.prop(texture.nvb, 'proceduretype')
            if texture.nvb.proceduretype == 'water':
                box.label(text="Water Settings")
                box.prop(texture.nvb, 'wateralpha')
                box.prop(texture.nvb, 'waterwidth')
                box.prop(texture.nvb, 'waterheight')
            elif texture.nvb.proceduretype == 'arturo':
                box.label(text="Arturo Settings")
                box.prop(texture.nvb, 'arturowidth')
                box.prop(texture.nvb, 'arturoheight')
            elif texture.nvb.proceduretype == 'cycle':
                box.label(text="Cycle Settings")
                box.prop(texture.nvb, 'defaultwidth')
                box.prop(texture.nvb, 'defaultheight')
                box.prop(texture.nvb, 'numx')
                box.prop(texture.nvb, 'numy')
                box.prop(texture.nvb, 'fps')
                box.prop(texture.nvb, 'filerange')
            box.separator()
            box.prop(texture.nvb, 'forcecyclespeed')
            box.prop(texture.nvb, 'anglecyclespeed')
            box.prop(texture.nvb, 'channelscale0')
            box.prop(texture.nvb, 'channelscale1')
            box.prop(texture.nvb, 'channelscale2')
            box.prop(texture.nvb, 'channelscale3')
            box.prop(texture.nvb, 'channeltranslate0')
            box.prop(texture.nvb, 'channeltranslate1')
            box.prop(texture.nvb, 'channeltranslate2')
            box.prop(texture.nvb, 'channeltranslate3')
            box.prop(texture.nvb, 'distort')
            box.prop(texture.nvb, 'distortangle')
            box.prop(texture.nvb, 'distortionamplitude')
            box.prop(texture.nvb, 'speed')

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'bumpmap', 'Bumpmap Properties'):
            box.prop(texture.nvb, 'isbumpmap')
            box.prop(texture.nvb, 'isdiffusebumpmap')
            box.prop(texture.nvb, 'isspecularbumpmap')
            box.prop(texture.nvb, 'bumpmapscaling')
            box.prop(texture.nvb, 'bumpintensity')
            box.prop(texture.nvb, 'diffusebumpintensity')
            box.prop(texture.nvb, 'specularbumpintensity')
            box.prop(texture.nvb, 'specularcolor')

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'envmap', 'Environment Map Properties'):
            box.prop(texture.nvb, 'isenvironmentmapped')
            box.prop(texture.nvb, 'envmapalpha')

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'general', 'General Properties'):
            box.prop(texture.nvb, 'blending')
            box.prop(texture.nvb, 'clamp')
            box.prop(texture.nvb, 'downsamplemin')
            box.prop(texture.nvb, 'downsamplemax')
            box.prop(texture.nvb, 'compresstexture')
            box.prop(texture.nvb, 'filter')
            box.prop(texture.nvb, 'mipmap')
            box.prop(texture.nvb, 'maptexelstopixels')
            box.prop(texture.nvb, 'gamma')
            box.prop(texture.nvb, 'alphamean')
            box.prop(texture.nvb, 'cube')
            box.prop(texture.nvb, 'islightmap')
            box.prop(texture.nvb, 'renderbmlmtype')
            box.prop(texture.nvb, 'temporary')
            box.prop(texture.nvb, 'useglobalalpha')
            box.prop(texture.nvb, 'decal')

        box = layout.row().box()
        if self.draw_box_header(texture, box, 'font', 'Font Properties'):
            box.prop(texture.nvb, 'numchars')
            box.prop(texture.nvb, 'fontheight')
            box.prop(texture.nvb, 'baselineheight')
            box.prop(texture.nvb, 'texturewidth')
            box.prop(texture.nvb, 'spacingR')
            box.prop(texture.nvb, 'spacingB')
            #box.prop(texture.nvb, 'upperleftcoords')
            #box.prop(texture.nvb, 'lowerrightcoords')

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

            try:
                row = box.row()
                row.prop(obj.active_material.active_texture.nvb, 'bumpmapped', text='Bumpmapped Texture')
                row = box.row()
                row.label(text = '(Warning: Affects all objects using texture)')
            except:
                pass

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
