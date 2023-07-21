#File: Ex022_Classic_OCC_Bottle.py
#To use this example file, you need to first follow the "Using CadQuery From Inside FreeCAD"
#instructions here: https://github.com/dcowden/cadquery#installing----using-cadquery-from-inside-freecad

#You run this example by typing the following in the FreeCAD python console, making sure to change
#the path to this example, and the name of the example appropriately.
#import sys
#sys.path.append('/home/user/Downloads/cadquery/examples/FreeCAD')
#import Ex022_Classic_OCC_Bottle

#If you need to reload the part after making a change, you can use the following lines within the FreeCAD console.
#reload(Ex022_Classic_OCC_Bottle)

#You'll need to delete the original shape that was created, and the new shape should be named sequentially
# (Shape001, etc).

#You can also tie these blocks of code to macros, buttons, and keybindings in FreeCAD for quicker access.
#You can get a more information on this example at
# http://parametricparts.com/docs/examples.html#an-extruded-prismatic-solid

import cadquery
import Part

#Set up the length, width, and thickness
(L,w,t) = (20.0, 6.0, 3.0)
s = cadquery.Workplane("XY")

#Draw half the profile of the bottle and extrude it
p = s.center(-L / 2.0, 0).vLine(w / 2.0) \
    .threePointArc((L / 2.0, w / 2.0 + t),(L, w / 2.0)).vLine(-w / 2.0) \
    .mirrorX().extrude(30.0, True)

#Make the neck
p.faces(">Z").workplane().circle(3.0).extrude(2.0, True)

#Make a shell
result = p.faces(">Z").shell(0.3)

#Boiler plate code to render our solid in FreeCAD's GUI
Part.show(result.toFreecad())
