import bpy
import bmesh
import mathutils
import gpu
from gpu_extras.batch import batch_for_shader
import blf

from . import geometry, utils, snap

shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
text_offset = [10,20]

def draw_line(self,context):
    shader.bind()
    shader.uniform_float("color", self.line_color)
    self.batch.draw(shader)
    
def draw_text(self,context):
    if len(self.verts)<0 or self.dist==0:
        return

    font_id = 0
    blf.position(font_id, self.mouse_pos[0]+text_offset[0], self.mouse_pos[1]+text_offset[1], 0)
    blf.size(font_id, 15, 72)
    blf.draw(font_id, str(round(self.dist,4)))

def draw_marker(self,context):
    if self.marker_vert:
        blf.position(0,  self.mouse_pos[0]-text_offset[0], self.mouse_pos[1]+text_offset[1], 0)
        blf.size(0, 15, 96)
        blf.draw(0, "V")
        

class MESH_OT_draw_polyline(bpy.types.Operator):
    """Polyline"""
    bl_idname = "mga.polyline"
    bl_label = "Draw Polyline"

    def modal(self, context, event):       
        if event.type == 'MOUSEMOVE':
            self.mouse_pos = [event.mouse_region_x, event.mouse_region_y]
            self.workplane = utils.get_workplane(context,event,self.workplane.origin)
            self.snapper.check_update(context)

            self.next_vert = utils.mouse_to_vert(context,event,self.workplane)

            self.line_color=(1, 1, 0, 1)

            sv = self.snapper.get_snapped_vertex(self.mouse_pos)
            if sv:
                self.next_vert = sv 
                self.line_color=(1, 0, 1, 1) 
                self.marker_vert = self.next_vert
                self.workplane.origin = self.next_vert
            else:
                self.marker_vert = None

            if len(self.verts)>0:
                v0 = context.object.matrix_world @ self.verts[-1].co
                self.workplane.origin = v0

                temp_axis = self.snap_axis
                if self.ortho and temp_axis==None:
                    d = self.next_vert - v0

                    max_dot = None
                    if d.length!=0:
                        for axis in [geometry.x_axis,geometry.y_axis,geometry.z_axis]:
                            if axis.cross(self.workplane.normal).length == 0:
                                continue
                            dot = abs(d.dot(axis))
                            if max_dot==None or dot>max_dot:
                                max_dot=dot
                                temp_axis = axis

                if temp_axis!=None:
                    self.line_color=(temp_axis[0],temp_axis[1],temp_axis[2],1)
                    self.next_vert = snap.snap_on_axis(v0,self.next_vert,temp_axis)

                if self.dist_str=="0":
                    self.dist = (self.next_vert-v0).length 
  
                self.batch = batch_for_shader(shader, 'LINES', {"pos": [v0[:], self.next_vert[:]]})
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                self.add_vertex(context,event)

        elif event.type == 'RET' or event.type == 'SPACE':
            if event.value == 'RELEASE':
                if self.dist_str!="0":
                    self.add_vertex(context,event)
                else:
                    self.clean(context)
                    return {'FINISHED'}
            return {'RUNNING_MODAL'}
        elif event.type == 'ESC':  # finish
                self.clean(context)
                return {'FINISHED'}
        elif event.type == 'BACK_SPACE':
            if event.value == 'RELEASE':
                if len(self.dist_str)>1:
                    self.dist_str = self.dist_str[:-1]
                else:
                    self.dist_str="0"
                
                self.dist = float(self.dist_str)
                context.area.tag_redraw()
        elif event.type == 'TAB':
            return {'RUNNING_MODAL'}
        elif event.ascii:
            char = event.ascii
            if char.isdigit() or char=='.':
                if self.dist_str=="0":
                    s = char
                else:
                    s = self.dist_str + char
                d = float(s)
                self.dist_str = s
                self.dist = d

            elif char=='c':
                if self.close_line(context):
                    self.clean(context)
                    return {'FINISHED'}
            elif char=='x':
                if self.snap_axis == geometry.x_axis:
                    self.snap_axis = None
                else:
                    self.snap_axis = geometry.x_axis
            elif char=='y':
                if self.snap_axis == geometry.y_axis:
                    self.snap_axis = None
                else:
                    self.snap_axis = geometry.y_axis
            elif char=='z':
                if self.snap_axis == geometry.z_axis:
                    self.snap_axis = None
                else:
                    self.snap_axis = geometry.z_axis
            elif char=='o':
                self.ortho = not self.ortho

            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        #self.matrix_world = context.object.matrix_world
        self.workplane = geometry.Plane(mathutils.Vector((0.0, 0.0, 0.0)),mathutils.Vector((0.0,0.0,1.0)))
        self.verts = []
        self.next_vert = None
        self.start_mesh(context)
        self.dist=0
        self.dist_str="0"
        self.line_color=(1, 1, 0, 1)
        self.batch = batch_for_shader(shader, 'LINES', {"pos": []})
        args = (self,context)
        self.handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_line, args, 'WINDOW', 'POST_VIEW')        
        self.handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_text, args, 'WINDOW', 'POST_PIXEL')
        self.mouse_pos = [0,0]

        self.snapper = snap.Snapper()
        self.snapper.update_verts_2d(context)
        self.marker_handle = bpy.types.SpaceView3D.draw_handler_add(draw_marker, args, 'WINDOW', 'POST_PIXEL') 
        self.marker_vert = None

        self.snap_axis = None
        self.ortho = True
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print("cancel")
        self.clean(context)
    
    def start_mesh(self, context):
        mesh = context.object.data
        self.bm = bmesh.from_edit_mesh(mesh) 
        self.workplane = geometry.Plane(mathutils.Vector((0.0, 0.0, 0.0)),mathutils.Vector((0.0,0.0,1.0)))           

    def add_vertex(self, context, event):
        #v1 = utils.mouse_to_vert(context,event,self.workplane)
        if self.next_vert == None:
            return

        v1 = context.object.matrix_world.inverted() @ self.next_vert
        
        if len(self.verts)>0:
            v0 = self.verts[-1].co
            dir = (v1-v0).normalized()
                
            if self.dist!=0: 
                dir = (v1-v0).normalized()
                v1 = v0 + self.dist * dir
        
        vert = self.bm.verts.new(v1)
        self.verts.append(vert)
        
        if len(self.verts)>1:
            self.bm.edges.new((self.verts[-2],self.verts[-1]))
    
        bmesh.update_edit_mesh(context.object.data)
        context.object.update_from_editmode()
        self.snapper.update_verts_2d(context)

        self.dist = 0
        self.dist_str = "0"
        self.next_vert = None
        self.snap_axis = None

    def close_line(self, context):
        if len(self.verts)<3:
            return False

        self.bm.edges.new((self.verts[-1],self.verts[0]))
        
        bmesh.update_edit_mesh(context.object.data)

        return True
        
    def clean(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_3d, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.handle_2d, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.marker_handle, 'WINDOW')
        context.area.tag_redraw()

        if len(self.verts)==1:
            self.bm.verts.remove(self.verts[0])
            bmesh.update_edit_mesh(context.object.data)

def menu_func(self, context):
    self.layout.operator(MESH_OT_draw_polyline.bl_idname)