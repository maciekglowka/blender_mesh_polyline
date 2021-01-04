import bpy
import mathutils
from bpy_extras import view3d_utils

SNAP_TRESHOLD = 25

def vertex_to_screen(context, v):
    return view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, v)

class Snapper:
    def __init__(self):
        self.verts_3d = None
        self.kdtree = None
        self.view_matrix = None

    def update_verts_2d(self, context):
        objects = context.view_layer.objects
        verts = []
        self.verts_3d = []

        for o in objects:
            mat = o.matrix_world
            if o.type!='MESH' or not o.visible_get():
                continue
            for v in o.data.vertices:
                mv = mat @ v.co
                verts.append(vertex_to_screen(context,mv))
                self.verts_3d.append(mv)

        self.kdtree = mathutils.kdtree.KDTree(len(verts))
        for idx, v in enumerate(verts):
            self.kdtree.insert((v[0],v[1],0),idx)

        self.kdtree.balance()

    def check_update(self, context):
        mat = context.space_data.region_3d.view_matrix
        if mat != self.view_matrix:
            self.view_matrix = mat.copy()
            self.update_verts_2d(context)

    def get_snapped_vertex(self, mouse):
        v,idx,dist = self.kdtree.find((mouse[0],mouse[1],0))
        if v and dist<=SNAP_TRESHOLD:
            return self.verts_3d[idx]
        return None