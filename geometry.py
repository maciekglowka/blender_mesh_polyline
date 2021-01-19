import mathutils

x_axis = mathutils.Vector((1,0,0))
y_axis = mathutils.Vector((0,1,0))
z_axis = mathutils.Vector((0,0,1))

class Plane:
    def __init__(self, origin, normal):
        self.origin = origin
        self.normal = normal