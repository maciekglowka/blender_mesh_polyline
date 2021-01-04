import bpy
import mathutils
from bpy_extras import view3d_utils


def vertex_to_screen(context, v):
    return view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, v)

class Snapper:
    def __init__(self):
        #self.objects = []
        self.verts_2d = []

    def update_verts_2d(self, context):
        objects = context.view_layer.objects

        for o in objects:
            mat = o.matrix_world
            if o.type!='MESH' or not o.visible_get():
                continue
            for v in o.data.vertices:
                self.verts_2d.append(vertex_to_screen(context,mat @ v.co))