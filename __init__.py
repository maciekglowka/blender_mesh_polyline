bl_info = {
    'name': 'Mesh Draw',
    'description': 'CAD-like tool for drawing mesh edges',
    'author': 'maciek glowka',
    'version': (0,0,1),
    'blender': (2, 90, 0),
    'location': 'View3D',
    'category': 'Mesh'
}

if "bpy" in locals():
    if 'polyline' in locals():
        import importlib

        try:
            modules = (geometry,utils,snap,polyline,panel)
            for m in modules:
                importlib.reload(m)

        except Exception as E:
            print('reload failed with error:')
            print(E)

import bpy
from . import polyline, panel

def register():
    bpy.utils.register_class(polyline.MESH_OT_draw_polyline)
    bpy.types.VIEW3D_MT_edit_mesh.append(polyline.menu_func)
    bpy.utils.register_class(panel.Polyline_PT_main_panel)


def unregister():
    bpy.utils.unregister_class(polyline.MESH_OT_draw_polyline)
    bpy.utils.unregister_class(panel.Polyline_PT_main_panel)