import bpy
#import bmesh
import mathutils
from bpy_extras import view3d_utils
        
axis_snap_angle = 0.1
ray_max=1.84467e+19

        
def mouse_ray(context, event):
    coords = event.mouse_region_x, event.mouse_region_y
    origin = view3d_utils.region_2d_to_origin_3d(context.region,context.space_data.region_3d, coords)
    dir = view3d_utils.region_2d_to_vector_3d(context.region,context.space_data.region_3d,coords)
    return origin, dir    

def mouse_to_vert(context, event, plane):
    m_origin, m_dir = mouse_ray(context,event)
    v = mathutils.geometry.intersect_line_plane(m_origin, m_origin + ray_max * m_dir, plane.origin, plane.normal)
    return v   

def check_axis_snap(dir, axis):
    if dir.length == 0:
        return False
    if dir.angle(axis)<axis_snap_angle or dir.angle(-axis)<axis_snap_angle:
        return True
    return False    

def snap_on_axis(v0,v1,axis):
    v = v1
    if axis.x!=0:
        v.y=v0.y
    if axis.y!=0:
        v.x=v0.x
        
    return v