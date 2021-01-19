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
    if len(self.verts)<0:
        return

    font_id = 0
    blf.position(font_id, self.mouse_pos[0]+text_offset[0], self.mouse_pos[1]+text_offset[1], 0)
    blf.size(font_id, 15, 72)
    blf.draw(font_id, str(round(self.dist,4)))

def draw_marker(self,context):
    if self.marker_vert:
        v = snap.vertex_to_screen(context, self.marker_vert)
        blf.position(0, v[0], v[1], 0)
        blf.size(0, 15, 72)
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
                v0 = self.verts[-1].co
            
                dir = (self.next_vert-v0).normalized()

                if sv==None:
                    if utils.check_axis_snap(dir,geometry.x_axis,self.workplane):
                        self.line_color=(1, 0, 0, 1) 
                        self.next_vert = utils.snap_on_axis(v0,self.next_vert,geometry.x_axis)   
                    elif utils.check_axis_snap(dir,geometry.y_axis,self.workplane):
                        self.line_color=(0, 1, 0, 1)
                        self.next_vert = utils.snap_on_axis(v0,self.next_vert,geometry.y_axis) 
                    elif utils.check_axis_snap(dir,geometry.z_axis,self.workplane):
                        self.line_color=(0, 0, 1, 1)
                        self.next_vert = utils.snap_on_axis(v0,self.next_vert,geometry.z_axis)     

                if self.dist_str=="0":
                    self.dist = (self.next_vert-v0).length 
  
                self.batch = batch_for_shader(shader, 'LINES', {"pos": [v0[:],self.next_vert[:]]})
                context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                self.add_vertex(context,event)

        elif event.type == 'RET':
            if event.value == 'RELEASE':
                if self.dist_str!="0":
                    self.add_vertex(context,event)
                else:
                    self.clean(context)
                    return {'FINISHED'}
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

            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
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
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print("cancel")
        self.clean(context)
    
    def start_mesh(self, context):
        mesh = context.object.data
        self.bm = bmesh.from_edit_mesh(mesh)            

    def add_vertex(self, context, event):
        #v1 = utils.mouse_to_vert(context,event,self.workplane)
        if self.next_vert == None:
            return

        v1 = self.next_vert
        
        if len(self.verts)>0:
            v0 = self.verts[-1].co
            dir = (v1-v0).normalized()
            
            #if utils.check_axis_snap(dir,geometry.x_axis):
            #    v1 = utils.snap_on_axis(v0,v1,geometry.x_axis) 
            #elif utils.check_axis_snap(dir,geometry.y_axis):
            #    v1 = utils.snap_on_axis(v0,v1,geometry.y_axis) 
                
            if self.dist!=0: 
                dir = (v1-v0).normalized()
                v1 = v0 + self.dist * dir
        
        vert = self.bm.verts.new(v1)
        self.verts.append(vert)
        
        if len(self.verts)>1:
            self.bm.edges.new((self.verts[-2],self.verts[-1]))
        
        bmesh.update_edit_mesh(context.object.data)
        
        self.dist = 0
        self.dist_str = "0"
        self.next_vert = None

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