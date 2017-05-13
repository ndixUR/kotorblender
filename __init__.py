# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Neverblender",
    "author": "Attila Gyoerkoes",
    "version": (1, 29),
    "blender": (2, 7, 0),
    "location": "File > Import-Export, Object Properties",
    "description": "Import, export and edit Odyssey MDL format",
    "warning": "",
    "wiki_url": ""
                "",
    "tracker_url": "",
    "category": "Import-Export"}


if 'bpy' in locals():
    import importlib
    importlib.reload(nvb_def)
    importlib.reload(nvb_utils)
    importlib.reload(nvb_io)
    importlib.reload(nvb_mdl)
    importlib.reload(nvb_node)
    importlib.reload(nvb_anim)
    importlib.reload(nvb_animnode)

    importlib.reload(nvb_props)
    importlib.reload(nvb_ops)
    importlib.reload(nvb_ui)
else:
    from .nvb import nvb_def
    from .nvb import nvb_utils
    from .nvb import nvb_io
    from .nvb import nvb_mdl
    from .nvb import nvb_node
    from .nvb import nvb_anim
    from .nvb import nvb_animnode

    from .nvb import nvb_props
    from .nvb import nvb_ops
    from .nvb import nvb_ui

import bpy
#import bpy_extras


def menu_func_export(self, context):
    self.layout.operator(nvb_ops.NVB_OP_Export.bl_idname, text="Odyssey (KotOR) (.mdl)")


def menu_func_import(self, context):
    self.layout.operator(nvb_ops.NVB_OP_Import.bl_idname, text="Odyssey (KotOR) (.mdl)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Object.nvb = bpy.props.PointerProperty(type=nvb_props.NVB_PG_OBJECT)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

    del bpy.types.Object.nvb

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
