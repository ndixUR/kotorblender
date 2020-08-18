import bpy
import bpy_extras
import bmesh

from . import nvb_def
from . import nvb_utils
from . import nvb_io
from . import nvb_txi

from mathutils import Matrix, Vector, Quaternion

class NVBCHILDREN_SMOOTHGROUP(bpy.types.Operator):
    bl_idname = "nvb.children_smoothgroup"
    bl_label = "Smoothgroup settings on descendants"
    #bl_property = 'action'
    bl_options = {'UNDO'}

    action = bpy.props.StringProperty()

    def execute(self, context):
        descendants = nvb_utils.searchNodeAll(
            context.object, lambda o: o.type == 'MESH'
        )
        for d in descendants:
            d.nvb.smoothgroup = self.action
        return {'FINISHED'}


class NVBSMOOTHGROUP_TOGGLE(bpy.types.Operator):
    bl_idname = "nvb.smoothgroup_toggle"
    bl_label = "Smoothgroup toggle"
    bl_options = {'UNDO'}

    sg_number = bpy.props.IntProperty()
    activity = bpy.props.IntProperty(default=0)

    def execute(self, context):
        bm = bmesh.from_edit_mesh(context.object.data)
        # the smoothgroup data layer
        sg_layer = bm.faces.layers.int.get(nvb_def.sg_layer_name)
        # convert sg_number to actual sg bitflag value
        sg_value = pow(2, self.sg_number)
        for face in bm.faces:
            if not face.select:
                continue
            #print("face sg before: {}".format(face[sg_layer]))
            if sg_value & face[sg_layer]:
                # turn off for face
                face[sg_layer] &= ~sg_value
            else:
                # turn on for face
                face[sg_layer] |= sg_value
            #print("face sg after: {}".format(face[sg_layer]))
        bmesh.update_edit_mesh(context.object.data)
        return {'FINISHED'}


class NVBSMOOTHGROUP_GENERATE(bpy.types.Operator):
    bl_idname = "nvb.smoothgroup_generate"
    bl_label = "Smoothgroup generate"
    bl_options = {'UNDO'}

    action = bpy.props.EnumProperty(items=(
        ('ALL', 'All Faces', 'Generate smoothgroups for all faces, replacing current values'),
        ('EMPTY', 'Empty Faces', 'Generate smoothgroups for all faces without current assignments'),
        ('SEL', 'Selected Faces', 'Generate smoothgroups for all selected faces, replacing current values')
    ))

    def execute(self, context):
        ob = context.object

        # switch into object mode so that the mesh gets committed,
        # and sg layer is available and modifiable
        initial_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        #ob.data.update(True, True)
        # copy the mesh, applying modifiers w/ render settings
        mesh = ob.to_mesh(scene=context.scene, apply_modifiers=True, settings='RENDER')
        #mesh.update(True, True)

        # get, or create, the smoothgroups data layer on the object mesh (not the copy)
        sg_list = ob.data.polygon_layers_int.get(nvb_def.sg_layer_name)
        if sg_list is None:
            sg_list = ob.data.polygon_layers_int.new(nvb_def.sg_layer_name)
        #ob.data.update()
        #mesh.calc_tessface()

        # make all the faces on mesh copy smooth,
        # allowing calc_smooth_groups to work
        for face in mesh.polygons:
            face.use_smooth = True
        (sg, sg_number) = mesh.calc_smooth_groups(use_bitflags=True)
        #print(sg)

        # apply the calculated smoothgroups
        if self.action == 'ALL':
            sg_list.data.foreach_set('value', sg)
        else:
            for face in mesh.polygons:
                if (self.action == 'EMPTY' and \
                    sg_list.data[face.index].value == 0) or \
                   (self.action == 'SEL' and face.select):
                    sg_list.data[face.index].value = sg[face.index]

        # return object to original mode
        bpy.ops.object.mode_set(mode=initial_mode)
        # remove the copied mesh
        bpy.data.meshes.remove(mesh)
        return {'FINISHED'}


class NVBSMOOTHGROUP_SELECT(bpy.types.Operator):
    bl_idname = "nvb.smoothgroup_select"
    bl_label = "Smoothgroup select"
    #bl_property = 'action'
    bl_options = {'UNDO'}

    sg_number = bpy.props.IntProperty()
    action = bpy.props.EnumProperty(items=(
        ('SEL', 'Select', 'Select faces with this smoothgroup'),
        ('DESEL', 'Deselect', 'Deselect faces with this smoothgroup')
    ))

    def description(self, context):
        if self.action == 'SEL':
            return "Select faces with this smoothgroup"
        else:
            return "Deselect faces with this smoothgroup"

    def execute(self, context):
        bm = bmesh.from_edit_mesh(context.object.data)
        bm.faces.ensure_lookup_table()
        # the smoothgroup data layer
        sg_layer = bm.faces.layers.int.get(nvb_def.sg_layer_name)
        #print("test with #{} and sel/desel: {}".format(self.sg_number, str(sel)))
        # convert sg_number to actual sg bitflag value
        sg_value = pow(2, self.sg_number)

        for face in bm.faces:
            if sg_value & face[sg_layer]:
                # select/deselect face
                #print("select set: {}".format(str(sel)))
                face.select_set(self.action == 'SEL')
        # using this causes ALL connected geometry to be selected,
        # including additional faces, undesirable
        #bm.select_flush(sel)
        # required to get the selection change to show in the 3D view
        bmesh.update_edit_mesh(context.object.data)
        return {'FINISHED'}


class NVBTEXTURE_IO(bpy.types.Operator):
    bl_idname = "nvb.texture_info_io"
    bl_label = "Texture Info"
    bl_property = 'action'
    bl_options = {'UNDO'}

    action = bpy.props.EnumProperty(items=(
        ('LOAD', 'Load', 'Import TXI file for this texture'),
        ('SAVE', 'Save', 'Export TXI file for this texture')
    ))

    def execute(self, context):
        if self.action == 'SAVE':
            nvb_txi.saveTxi(context.object.active_material.active_texture, self)
            #if nvb_txi.saveTxi(context.object.active_material.active_texture):
            #    self.report({'INFO'}, 'Successfully saved TXI file')
        else:
            nvb_txi.loadTxi(context.object.active_material.active_texture, self)
            #if nvb_txi.loadTxi(context.object.active_material.active_texture):
            #    self.report({'INFO'}, 'Successfully loaded TXI file')
        return {'FINISHED'}

class NVBTEXTURE_BOX_OPS(bpy.types.Operator):
    ''' Hide/show Texture Info sub-groups'''
    bl_idname = "nvb.texture_info_box_ops"
    bl_label = "Box Controls"
    bl_description = "Show/hide this property list"

    boxname = bpy.props.StringProperty(default='')

    def execute(self, context):
        if self.boxname == '':
            return {'FINISHED'}
        attrname = 'box_visible_' + self.boxname
        texture = context.object.active_material.active_texture
        current_state = getattr(texture.nvb, attrname)
        setattr(texture.nvb, attrname, not current_state)
        return {'FINISHED'}

class NVBSKIN_BONE_OPS(bpy.types.Operator):
    bl_idname = "nvb.armature"
    bl_label = "Armature Operations"
    #bl_property = 'action'
    bl_options = {'UNDO'}

    def child_pseudobones(self, obj):
        psb = []
        if obj is None or len(obj.children) < 1:
            return psb
        for c in obj.children:
            if self.is_pseudobone(c) or self.is_control_handle(c):
                psb.append(c)
        return psb

    def is_pseudobone(self, obj):
        if obj is None:
            return False
        if obj.nvb.meshtype == nvb_def.Meshtype.TRIMESH and \
           not obj.nvb.render:
            return True
        #if obj.type == 'EMPTY' and \
        #   len(obj.children) and \
        #   len(self.child_pseudobones(obj)):
        #    return True
        return False

    def is_control_handle(self, obj):
        if obj is None:
            return False
        if obj.type == 'EMPTY' and \
           len(obj.children):
            return True
        return False

    def nearest_pseudobone(self, obj, direction_up=False, first=True):
        if obj is None:
            return None
        if not first and direction_up and self.is_control_handle(obj):
            return obj
        if not first and self.is_pseudobone(obj):
            return obj
        if direction_up:
            return self.nearest_pseudobone(obj.parent, True, False)
        else:
            for c in obj.children:
                r = self.nearest_pseudobone(c, False, False)
                if r is not None:
                    return r
        return None


    def boner(self, amt, obj, parent=None, pbone=None):
        bone = None
        parent_pseudobone = (parent is not None and \
                             parent.nvb.meshtype == nvb_def.Meshtype.TRIMESH and \
                             not parent.nvb.render)
        if self.is_pseudobone(obj) or self.is_control_handle(obj): # or has_pseudobone:
            bone_name = obj.name
            # leave object name alone
            #obj.name = 'PSB_' + obj.name
            #bone = amt.edit_bones.new(obj.name + 'Bone')
            bone = amt.edit_bones.new(bone_name)
            if pbone is not None:
                bone.parent = pbone
                #bone.head = pbone.tail
            #else:
                #bone.use_connect = False
                #bone.head = obj.matrix_world.to_translation()
            #bone.head = pbone.tail
            bone.head = obj.matrix_world.to_translation()
            #bone.tail = obj.matrix_world.to_translation()
            print(obj.matrix_world.to_translation().to_tuple())
            #+ parent.matrix_world.to_translation()
            tail_loc = Vector((0.0, 0.0, 0.0))
            print('{} {} {}'.format(obj.name, len(self.child_pseudobones(obj)), len(obj.children)))
            if len(self.child_pseudobones(obj)) > 0:
                tail_loc = sum((Vector(c.matrix_world.to_translation()) for c in self.child_pseudobones(obj)), Vector()) / len(self.child_pseudobones(obj))
                print('averaged child tail:')
                print(tail_loc)
                print(tail_loc.length)
                #if obj.type == 'EMPTY':
                #    tail_loc = tail_loc.orthogonal()
                if tail_loc.length < 0.0001 or obj.type == 'EMPTY':
                    tail_loc = Vector((0.0, 0.05, 0.0)) + bone.head

                #tail_loc = Vector((0.0, 0.0, 0.0))
                #for c in self.child_pseudobones(obj):
                #    tail_loc[0] += c.matrix_world.to_translation().x
                #    tail_loc[1] += c.matrix_world.to_translation().y
                #    tail_loc[2] += c.matrix_world.to_translation().z
                #tail_loc[0] /= float(len(obj.children))
                #tail_loc[1] /= float(len(obj.children))
                #tail_loc[2] /= float(len(obj.children))
                #print('averaged child tail:')
                #print(tail_loc)
            else:
                #tail_loc = obj.matrix_world.to_translation().to_tuple()
                print(obj.name)
                print(obj.bound_box)
                tail_loc = (2 * (sum((Vector(p) for p in obj.bound_box), Vector()) / 8))
                tail_loc.rotate(obj.matrix_world)
                tail_loc += bone.head
            bone.tail = Vector(tail_loc)
        #else:
        #    pbone = None
        if bone is None:
            bone = pbone
        for c in obj.children:
            #print(obj.nvb.meshtype)
            #print(obj.nvb.render)
            self.boner(amt, c, obj, bone)

    def adjust_control_handles(self, amt_obj, edit_bone):
        if edit_bone is None:
            return
        amt = amt_obj.data
        obj_name = 'PSB_' + edit_bone.name
        obj = bpy.data.objects.get(obj_name)
        if self.is_control_handle(obj):
            print(edit_bone.name)
            print(edit_bone.matrix)
            edit_bone.use_relative_parent = True
            c_obj = self.nearest_pseudobone(obj)
            p_obj = self.nearest_pseudobone(obj, direction_up=True)
            c_bone = None
            p_bone = None
            if c_obj is not None:
                c_bone = amt.edit_bones.get(c_obj.name[4:])
                print("child_obj {}".format(c_obj.name))
            if p_obj is not None:
                p_bone = amt.edit_bones.get(p_obj.name[4:])
                print("parent_obj {}".format(p_obj.name))
                print("parent_obj {}".format(amt.edit_bones.keys()))
            vec = Vector()
            if c_bone is None and p_bone is None:
                vec = Vector((0.0, 0.05, 0.0))
            if c_bone is not None:
                vec += c_bone.vector
                print("child {}".format(c_bone.name))
            if p_bone is not None:
                vec += p_bone.vector
                print("parent {}".format(p_bone.name))
            # d = c - a, o = b - a, c = vec.tail, a = vec.head, b = edit_bone.head
            # ctl_vec = a + (o dot d)/(d dot d)*d - b
            a = edit_bone.tail
            b = edit_bone.head
            if p_bone is not None:
                #a += p_bone.vector
                # parent control handle
                a = p_bone.tail
                if a == b:
                    # parent pseudobone
                    a = p_bone.head
            c = edit_bone.head
            if c_bone is not None:
                c = c_bone.tail
            d = c - a
            o = b - a
            print("a = {}".format(a))
            print("b = {}".format(b))
            print("c = {}".format(c))
            #ctl_vec = a + ((b - a).dot(c)/(vec.dot(vec))*vec) - b
            ctl_vec = a + o.dot(d)/d.dot(d)*d - b
            print(ctl_vec)
            print(edit_bone.head)
            print(edit_bone.tail)
            # standardize ctl_vec length
            print(ctl_vec)
            print(ctl_vec.normalized())
            if p_bone is None or not self.is_control_handle(p_obj):
                ctl_vec.length = 0.05
            print(ctl_vec)
            edit_bone.tail = ctl_vec + edit_bone.head
            print(edit_bone.tail)
            print(edit_bone.matrix)
            print(amt_obj.matrix_world * edit_bone.matrix)

        for c in edit_bone.children:
            self.adjust_control_handles(amt_obj, c)


    def parent_pseudobones(self, amt, obj):
        for c in obj.children:
            self.parent_pseudobones(amt, c)
        if not amt.data.bones.get(obj.name):
            return
        obj.parent = amt
        obj.parent_bone = obj.name
        obj.parent_type = 'BONE'
        m = obj.matrix_world.copy()
        bone_matrix = amt.data.bones.get(obj.name).matrix_local.copy()
        # bone_matrix is using head as its translation point, we need tail
        # do this a really awkward way until we figure out how to do it well
        bone_scl_x = Matrix.Scale(bone_matrix.to_scale().x, 4, Vector((1, 0, 0)))
        bone_scl_y = Matrix.Scale(bone_matrix.to_scale().y, 4, Vector((0, 1, 0)))
        bone_scl_z = Matrix.Scale(bone_matrix.to_scale().z, 4, Vector((0, 0, 1)))
        tail_loc_matrix = Matrix.Translation(amt.data.bones.get(obj.name).tail_local)
        tail_matrix = (
            tail_loc_matrix *
            bone_matrix.to_quaternion().to_matrix().to_4x4() *
            (bone_scl_x * bone_scl_y * bone_scl_z)
        )
        obj.matrix_parent_inverse = tail_matrix.inverted_safe()
        obj.matrix_world = m

        # lock transformations on pseudobone object controlled by armature
        obj.lock_location = (True, True, True)
        obj.lock_rotation = (True, True, True)
        obj.lock_scale    = (True, True, True)

    def flatten_old_pseudobones(self, amt, obj):
        for c in obj.children:
            self.flatten_old_pseudobones(amt, c)
        #print(m)
        #if self.is_pseudobone(obj) or self.is_control_handle(obj):
        if obj.name[:4] == 'PSB_':
            m = obj.matrix_world
            obj.parent = bpy.data.objects['cutscenedummy']
            obj.matrix_parent_inverse = bpy.data.objects['cutscenedummy'].matrix_world.inverted()
            #print(obj.matrix_world)
            #print(obj.matrix_world)
            obj.matrix_world = m

    def child_to_bones(self, amt, obj):
        if obj is None:
            return

        #if not self.is_pseudobone(obj) and not self.is_control_handle(obj):
        #if self.is_pseudobone(obj) or self.is_control_handle(obj):
        if obj.name[:4] == 'PSB_':
            #parent_bone_name = obj.parent.name
            #if parent_bone_name[:4] == 'PSB_':
            #    parent_bone_name = parent_bone_name[4:]
            parent_bone_name = obj.name
            if parent_bone_name[:4] == 'PSB_':
                parent_bone_name = parent_bone_name[4:]
            #print("{} => {}".format(obj.name, obj.parent.name))
            print("{} => {}".format(obj.name, parent_bone_name))
            if amt.data.edit_bones.find(parent_bone_name) != -1:
                print('add constraint')
                ct = obj.constraints.new(type="CHILD_OF")
                ct.target = amt
                #ct.subtarget = amt.data.edit_bones.get(parent_bone_name)
                #ct.subtarget = amt.data.bones.get(parent_bone_name)
                #ct.inverse_matrix = amt.data.bones.get(parent_bone_name).matrix_world.inverted()
                ct.subtarget = parent_bone_name
                #obj.active = True
                ct.inverse_matrix = (
                    amt.matrix_world *
                    amt.data.edit_bones.get(parent_bone_name).matrix
                ).inverted()
                ###ctx = bpy.context.copy()
                ###ctx['constraint'] = ct
                ###print(ctx.keys())
                #ctx.active_object = obj
                #bpy.context.scene.objects.active
                ##ct_obj = bpy.context.scene.objects.active
                ##bpy.context.scene.objects.active = obj
                #ctx.scene.objects.active = obj
                ##bpy.ops.constraint.childof_set_inverse(ctx, constraint="Child Of", owner='OBJECT')
                ##bpy.context.scene.objects.active = ct_obj
        for c in obj.children:
            self.child_to_bones(amt, c)

    def execute(self, context):
        #bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=context.scene.objects['cutscenedummy'].location)
        mdl = nvb_utils.get_mdl_base()
        node_cutscenedummy = nvb_utils.get_node_by_name(mdl, 'cutscenedummy')
        node_rootdummy = nvb_utils.get_node_by_name(mdl, 'rootdummy')
        if node_cutscenedummy is None or \
           node_rootdummy is None:
            return {'FINISHED'}
        bpy.ops.object.armature_add()
        ob = bpy.context.scene.objects.active
        ob.show_x_ray = True
        # Make this modelname_amt
        amt_name = '{}.armature'.format(mdl.name)
        ob.name = amt_name
        #ob.show_axis = True
        #ob.parent = context.scene.objects['cutscenedummy']
        ob.parent = mdl
        ob.location = mdl.location #node_cutscenedummy.location
        #context.scene.objects.active = ob
        print(dir(ob))
        amt = ob.data
        print(dir(amt))
        amt.name = amt_name
        #amt.show_axes = True
        amt.show_names = True
        amt.show_axes = True
        amt.draw_type = 'STICK'
        bpy.ops.object.mode_set(mode='EDIT')
        #amt.edit_bones[0].tail = node_rootdummy.location
        amt.edit_bones[0].tail = node_cutscenedummy.location
        amt.edit_bones[0].name = 'cutscenedummy'
        #self.boner(amt, context.scene.objects['rootdummy'], pbone=amt.edit_bones[0])
        self.boner(amt, node_rootdummy, pbone=amt.edit_bones[0])
        self.adjust_control_handles(ob, amt.edit_bones[0])
        psb_rootdummy = nvb_utils.get_node_by_name(mdl, 'psb_rootdummy')
        #self.flatten_old_pseudobones(ob, psb_rootdummy)
        #self.child_to_bones(ob, node_cutscenedummy)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.parent_pseudobones(ob, mdl)
        # apply armature deformation modifier to skin meshes
        for name, obj in context.scene.objects.items():
            if obj.nvb.meshtype == nvb_def.Meshtype.SKIN and \
               'Armature' not in obj.modifiers:
                amt_mod = obj.modifiers.new(name='Armature', type='ARMATURE')
                amt_mod.object = ob
                amt_mod.use_vertex_groups = True
                amt_mod.use_deform_preserve_volume = True
                # turn off render here,
                # otherwise we get deformations in exported skin node geometry
                amt_mod.show_render = False
        # apply childOf modifier to non-pseudobone nodes in the cutscenedummy tree
        ##self.child_to_bones(ob, context.scene.objects['PSB_cutscenedummy'])
        #for name, obj in context.scene.objects.items():
        '''
        while len(obj.children):
            print(name)
            print(dir(obj))
            if obj.nvb.meshtype == nvb_def.Meshtype.TRIMESH and \
               not obj.nvb.render:
                pass
        '''
        return {'FINISHED'}


class NVBTEXTURE_OPS(bpy.types.Operator):
    bl_idname = "nvb.texture_info_ops"
    bl_label = "Texture Info Operations"
    bl_property = 'action'
    bl_options = {'UNDO'}

    action = bpy.props.EnumProperty(items=(
        ('RESET', 'Reset', 'Reset the property to default value. This will prevent it from being written to TXI file output.'),
        ('NYI', 'Other', '')
    ))
    propname = bpy.props.StringProperty(default='')

    def execute(self, context):
        if self.propname == '':
            return {'FINISHED'}
        if self.action == 'RESET':
            #print(bpy.types.ImageTexture.nvb)
            #print(bpy.types.ImageTexture.nvb[1])
            #print(bpy.types.ImageTexture.nvb[1]['type'])
            #print(bpy.types.ImageTexture.nvb[1]['type'][self.propname])
            #print(getattr(bpy.types.ImageTexture.nvb[1]['type'], self.propname))
            #print(getattr(bpy.types.ImageTexture.nvb[1]['type'], self.propname)[1])
            #print(getattr(bpy.types.ImageTexture.nvb[1]['type'], self.propname)[1]['default'])
            #print(getattr(bpy.types.ImageTexture.nvb[1], self.propname)[1]['default'])
            #attr_def = getattr(bpy.types.ImageTexture.nvb[1], self.propname)[1]['default']
            attr_def = getattr(bpy.types.ImageTexture.nvb[1]['type'], self.propname)[1]
            if 'default' in attr_def:
                setattr(context.object.active_material.active_texture.nvb, self.propname, attr_def['default'])
        return {'FINISHED'}

class NVB_LIST_OT_LightFlare_New(bpy.types.Operator):
    ''' Add a new item to the flare list '''

    bl_idname = 'nvb.lightflare_new'
    bl_label  = 'Add a new flare to a light'

    def execute(self, context):
        if (context.object.type == 'LAMP'):
            context.object.nvb.flareList.add()

        return{'FINISHED'}


class NVB_LIST_OT_LightFlare_Delete(bpy.types.Operator):
    ''' Delete the selected item from the flare list '''

    bl_idname = 'nvb.lightflare_delete'
    bl_label = 'Deletes a flare from the light'

    @classmethod
    def poll(self, context):
        ''' Enable only if the list isn't empty '''
        return len(context.object.nvb.flareList) > 0

    def execute(self, context):
        flareList = context.object.nvb.flareList
        flareIdx  = context.object.nvb.flareListIdx

        flareList.remove(flareIdx)
        if flareIdx > 0:
            flareIdx =flareIdx - 1

        return{'FINISHED'}


class NVB_LIST_OT_LightFlare_Move(bpy.types.Operator):
    ''' Move an item in the flare list '''

    bl_idname = 'nvb.lightflare_move'
    bl_label  = 'Move an item in the flare list'

    direction = bpy.props.EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))

    @classmethod
    def poll(self, context):
        return len(context.object.nvb.flareList) > 0

    def move_index(self, context):
        flareList = context.object.nvb.flareList
        flareIdx  = context.object.nvb.flareListIdx

        listLength = len(flareList) - 1 # (index starts at 0)
        newIdx = 0
        if self.direction == 'UP':
            newIdx = flareIdx - 1
        elif self.direction == 'DOWN':
            newIdx = flareIdx + 1

        newIdx   = max(0, min(newIdx, listLength))
        context.object.nvb.flareListIdx = newIdx

    def execute(self, context):
        flareList = context.object.nvb.flareList
        flareIdx  = context.object.nvb.flareListIdx

        if self.direction == 'DOWN':
            neighbour = flareIdx + 1
            flareList.move(flareIdx, neighbour)
            self.move_index(context)
        elif self.direction == 'UP':
            neighbour = flareIdx - 1
            flareList.move(neighbour, flareIdx)
            self.move_index(context)
        else:
            return{'CANCELLED'}

        return{'FINISHED'}


class NVB_LIST_OT_AnimEvent_New(bpy.types.Operator):
    ''' Add a new item to the event list '''

    bl_idname = 'nvb.animevent_new'
    bl_label  = 'Add a new event to an animation'

    def execute(self, context):
        context.object.nvb.eventList.add()

        return{'FINISHED'}


class NVB_LIST_OT_AnimEvent_Delete(bpy.types.Operator):
    ''' Delete the selected item from the event list '''

    bl_idname = 'nvb.animevent_delete'
    bl_label = 'Deletes an event from an animation'

    @classmethod
    def poll(self, context):
        ''' Enable only if the list isn't empty '''
        return len(context.object.nvb.eventList) > 0

    def execute(self, context):
        eventList = context.object.nvb.eventList
        eventIdx  = context.object.nvb.eventListIdx

        eventList.remove(eventIdx)
        if eventIdx > 0:
            eventIdx = eventIdx - 1

        return{'FINISHED'}


class NVB_LIST_OT_AnimEvent_Move(bpy.types.Operator):
    ''' Move an item in the event list '''

    bl_idname = 'nvb.animevent_move'
    bl_label  = 'Move an item in the event  list'

    direction = bpy.props.EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))

    @classmethod
    def poll(self, context):
        return len(context.object.nvb.eventList) > 0

    def move_index(self, context):
        eventList = context.object.nvb.eventList
        eventIdx  = context.object.nvb.eventListIdx

        listLength = len(eventList) - 1 # (index starts at 0)
        newIdx = 0
        if self.direction == 'UP':
            newIdx = eventIdx - 1
        elif self.direction == 'DOWN':
            newIdx = eventIdx + 1

        newIdx   = max(0, min(newIdx, listLength))
        context.object.nvb.eventListIdx = newIdx

    def execute(self, context):
        eventList = context.object.nvb.eventList
        eventIdx  = context.object.nvb.eventListIdx

        if self.direction == 'DOWN':
            neighbour = eventIdx + 1
            eventList.move(eventIdx, neighbour)
            self.move_index(context)
        elif self.direction == 'UP':
            neighbour = eventIdx - 1
            eventList.move(neighbour, eventIdx)
            self.move_index(context)
        else:
            return{'CANCELLED'}

        return{'FINISHED'}


class NVB_OP_Import(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    '''Import Odyssey Engine model (.mdl)'''

    bl_idname  = 'kb.mdlimport'
    bl_label   = 'Import Odyssey MDL'
    bl_options = {'UNDO'}

    filename_ext = '.mdl'
    filter_glob = bpy.props.StringProperty(
            default = '*.mdl;*.mdl.ascii',
            options = {'HIDDEN'},
            )

    importGeometry = bpy.props.BoolProperty(
            name = 'Import Geometry',
            description = 'Disable if only animations are needed',
            default = True)

    importWalkmesh = bpy.props.BoolProperty(
            name = 'Import Walkmesh',
            description = 'Attempt to load placeable and door walkmeshes',
            default = True)

    importSmoothGroups = bpy.props.BoolProperty(
            name = 'Import smooth groups',
            description = 'Import smooth groups as sharp edges',
            default = True)

    importAnim = bpy.props.BoolProperty(
            name = 'Import animations',
            description = 'Import animations',
            default = True)

    materialMode = bpy.props.EnumProperty(
            name = 'Materials',
            items = (('NON', 'None', 'Don\'t create materials or import textures'),
                     ('SIN', 'Single', 'Create only one material per texture, shared between objects'),
                     ('MUL', 'Multiple', 'Create a seperate material for each object')),
            default = 'SIN')

    textureSearch = bpy.props.BoolProperty(
            name='Image search',
            description='Search for images in subdirectories' \
                        ' (Warning, may be slow)',
            default=False,
            )

    # Hidden option, only used for batch minimap creation
    minimapMode = bpy.props.BoolProperty(
            name = 'Minimap Mode',
            description = 'Ignore lights and walkmeshes',
            default = False,
            options = {'HIDDEN'},
            )

    minimapSkipFade = bpy.props.BoolProperty(
            name = 'Minimap Mode: Import Fading Objects',
            description = 'Ignore fading objects',
            default = False,
            options = {'HIDDEN'},
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',
                                            'check_existing',
                                            ))
        return nvb_io.loadMdl(self, context, **keywords)


class NVB_OP_Export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    '''Export Odyssey Engine model (.mdl)'''

    bl_idname = 'kb.mdlexport'
    bl_label  = 'Export Odyssey MDL'

    filename_ext = '.mdl'
    filter_glob = bpy.props.StringProperty(
            default = '*.mdl;*.mdl.ascii',
            options = {'HIDDEN'},
            )

    exports = bpy.props.EnumProperty(
            name = 'Export',
            options = {'ENUM_FLAG'},
            items = (('ANIMATION', 'Animations', 'Export animations'),
                     ('WALKMESH', 'Walkmesh', 'Attempt to create walkmesh file (.pwk, .dwk or .wok depending on classification)'),
                     ),
            default = {'ANIMATION', 'WALKMESH'},
            )

    exportSmoothGroups = bpy.props.BoolProperty(
            name='Export Smooth groups',
            description='Generate smooth groups from sharp edges' \
                        '(When disabled every face belongs to the same group)',
            default=True,
            )

    exportTxi = bpy.props.BoolProperty(
            name='Export TXI files',
            description='Create TXI files containing the texture properties' \
                        '(When disabled, TXI files can be exported manually)',
            default=True,
            )

    applyModifiers = bpy.props.BoolProperty(
            name='Apply Modifiers',
            description='Apply Modifiers before exporting',
            default=True,
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',
                                            'check_existing',
                                            ))
        return nvb_io.saveMdl(self, context, **keywords)


class LoadWokMaterials(bpy.types.Operator):
    '''
    Load all materials for aabb walkmeshes for the selected object. Current
    material slots will be deleted.
    '''
    bl_idname = "nvb.load_wok_mats"
    bl_label  = "Load walkmesh materials"

    def execute(self, context):
        '''
        - Deletes all current materials
        - adds walkmesh materials
        '''
        selected_object = context.object
        if (selected_object) and (selected_object.type == 'MESH'):
            object_mesh = selected_object.data

            # Remove all current material slots
            for i in range(len(selected_object.material_slots)):
                bpy.ops.object.material_slot_remove()

            # Create materials
            for matDef in nvb_def.wok_materials:
                matName = matDef[0]

                # Walkmesh materials should be shared across multiple
                # walkmeshes, as they always identical
                if matName in bpy.data.materials.keys():
                    mat = bpy.data.materials[matName]
                else:
                    mat = bpy.data.materials.new(matName)

                    mat.diffuse_color      = matDef[1]
                    mat.diffuse_intensity  = 1.0
                    mat.specular_color     = (0.0,0.0,0.0)
                    mat.specular_intensity = matDef[2]

                object_mesh.materials.append(mat)
        else:
            self.report({'INFO'}, 'A mesh must be selected')
            return {'CANCELLED'}

        return {'FINISHED'}


class NVBOBJECT_OT_RenderMinimap(bpy.types.Operator):
    bl_idname = "nvb.render_minimap"
    bl_label  = "Render Minimap"

    def execute(self, context):
        '''
        - Creates an camera and a lamp
        - Renders Minimap
        '''
        obj   = context.object
        scene = bpy.context.scene
        if obj and (obj.type == 'EMPTY'):
            if (obj.nvb.dummytype == nvb_def.Dummytype.MDLROOT):
                nvb_utils.setupMinimapRender(obj, scene)
                bpy.ops.render.render(use_viewport = True)
                #bpy.ops.render.view_show()

                self.report({'INFO'}, 'Ready to render')
            else:
                self.report({'INFO'}, 'A MDLROOT must be selected')
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, 'An Empty must be selected')
            return {'CANCELLED'}

        return {'FINISHED'}


class NVBOBJECT_OT_SkingroupAdd(bpy.types.Operator):
    bl_idname = "nvb.skingroup_add"
    bl_label  = "Add new Skingroup"

    def execute(self, context):
        obj        = context.object
        skingrName = obj.nvb.skingroup_obj
        # Check if there is already a vertex group with this name
        if skingrName:
            if (skingrName not in obj.vertex_groups.keys()):
                # Create the vertex group
                vertGroup = obj.vertex_groups.new(skingrName)
                obj.nvb.skingroup_obj = ''

                self.report({'INFO'}, 'Created vertex group ' + skingrName)
                return{'FINISHED'}
            else:
                self.report({'INFO'}, 'Duplicate Name')
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, 'Empty Name')
            return {'CANCELLED'}


class NVBOBJECT_OT_AnimsceneRename(bpy.types.Operator):
    bl_idname = "nvb.animscene_rename"
    bl_label  = "Rename animation scene"

    @classmethod
    def poll(self, context):
        obj = context.object
        return (obj.type == 'EMPTY') and (obj.nvb.dummytype == nvb_def.Dummytype.MDLROOT) and obj.nvb.isanimation

    def execute(self, context):
        obj         = context.object
        newAnimName = obj.nvb.newanimname
        oldAnimName = obj.nvb.animname
        sourceScene = context.scene
        # Check if there is already a scene with this animation name
        if (newAnimName  != ''):
            if (newAnimName not in bpy.data.scenes):
                if nvb_utils.copyAnimSceneCheck(obj, newAnimName, oldAnimName):
                    sourceScene.name = newAnimName

                    animRootDummy = nvb_utils.renameAnimScene(obj, newAnimName, oldAnimName)
                    animRootDummy.nvb.animname    = newAnimName
                    animRootDummy.nvb.newanimname = ''

                    sourceScene.update()
                else:
                    self.report({'INFO'}, 'Duplicate Object')
                    return {'CANCELLED'}
            else:
                self.report({'INFO'}, 'Scene already present')
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, 'Empty Name')
            return {'CANCELLED'}

        self.report({'INFO'}, 'Renamed animation ' + oldAnimName + ' to ' + newAnimName)
        return{'FINISHED'}


class NVBOBJECT_OT_AnimsceneAdd(bpy.types.Operator):
    bl_idname = "nvb.animscene_add"
    bl_label  = "Add animation scene"

    @classmethod
    def poll(self, context):
        obj = context.object
        return (obj.type == 'EMPTY') and (obj.nvb.dummytype == nvb_def.Dummytype.MDLROOT)

    def execute(self, context):
        obj         = context.object
        newAnimName = obj.nvb.newanimname
        oldAnimName = obj.nvb.animname
        sourceScene = context.scene
        # Check if there is already a scene with this animation name
        if (newAnimName  != ''):
            if (newAnimName not in bpy.data.scenes):
                if nvb_utils.copyAnimSceneCheck(obj, newAnimName, oldAnimName):
                    # Create the scene
                    newScene = bpy.data.scenes.new(newAnimName)
                    # Set fps
                    newScene.render.fps   = nvb_def.fps
                    newScene.frame_start = sourceScene.frame_start
                    newScene.frame_end   = sourceScene.frame_end

                    animRootDummy = nvb_utils.copyAnimScene(newScene, obj, newAnimName, oldAnimName)
                    animRootDummy.nvb.isanimation = True
                    animRootDummy.nvb.animname    = newAnimName
                    animRootDummy.nvb.newanimname = ''

                    newScene.update()
                else:
                    self.report({'INFO'}, 'Duplicate Objects')
                    return {'CANCELLED'}
            else:
                self.report({'INFO'}, 'Scene already present')
                return {'CANCELLED'}
        else:
            self.report({'INFO'}, 'Empty Name')
            return {'CANCELLED'}

        self.report({'INFO'}, 'New animation ' + newAnimName)
        return{'FINISHED'}
