import bpy

class Polyline_PT_main_panel(bpy.types.Panel):
    bl_idname = "Polyline_PT_main_panel"
    bl_label = "Main Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Polyline"
    bl_context = "mesh_edit"

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="Mesh Polyline")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('mga.polyline')

        row = layout.row()
        row.label(text='x,y,z - toggle axis snap')
        row = layout.row()
        row.label(text='o - toggle ortho mode')
        row = layout.row()
        row.label(text='c - close polyline')
        row = layout.row()
        row.label(text='space, enter - accept length / finish')