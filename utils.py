import bpy
#import bmesh
import mathutils
from bpy_extras import view3d_utils
from . import geometry
        
axis_snap_angle = 0.1
ray_max=1.84467e+19

def get_workplane(context, event, origin = mathutils.Vector((0.0, 0.0, 0.0))):
    m_origin, m_dir = mouse_ray(context,event)

    xa = min(m_dir.angle(geometry.x_axis, None),m_dir.angle(-geometry.x_axis, None))
    ya = min(m_dir.angle(geometry.y_axis, None),m_dir.angle(-geometry.y_axis, None))
    za = min(m_dir.angle(geometry.z_axis, None),m_dir.angle(-geometry.z_axis, None))

    #print("{},{},{}".format(xa,ya,za))

    dir = geometry.z_axis

    if xa < za and xa <= ya:
        dir = geometry.x_axis
    elif ya < za and ya < xa:
        dir = geometry.y_axis

    return geometry.Plane(origin,dir)
        
def mouse_ray(context, event):
    coords = event.mouse_region_x, event.mouse_region_y
    origin = view3d_utils.region_2d_to_origin_3d(context.region,context.space_data.region_3d, coords)
    dir = view3d_utils.region_2d_to_vector_3d(context.region,context.space_data.region_3d,coords)
    return origin, dir    

def mouse_to_vert(context, event, plane):
    m_origin, m_dir = mouse_ray(context,event)
    v = mathutils.geometry.intersect_line_plane(m_origin, m_origin + ray_max * m_dir, plane.origin, plane.normal)
    return v   

def check_axis_snap(dir, axis, workplane):
    if axis.cross(workplane.normal).length==0:
        return False
    if dir.length == 0:
        return False
    if dir.angle(axis)<axis_snap_angle or dir.angle(-axis)<axis_snap_angle:
        return True
    return False    

def snap_on_axis(v0,v1,axis):
    if axis.x!=0:
        v1.y=v0.y
        v1.z=v0.z
    if axis.y!=0:
        v1.x=v0.x
        v1.z=v0.z
    if axis.z!=0:
        v1.x=v0.x
        v1.y=v0.y
        
    return v1