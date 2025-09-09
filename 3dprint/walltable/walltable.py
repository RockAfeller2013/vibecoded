import FreeCAD
import Part
import SheetMetal

# Create a new document
doc = FreeCAD.newDocument()

# Define dimensions
table_length = 1200  # mm
table_width = 600    # mm
table_thickness = 20 # mm

# Create the tabletop
tabletop = Part.makeBox(table_length, table_width, table_thickness)
tabletop_obj = doc.addObject("Part::Feature", "Tabletop")
tabletop_obj.Shape = tabletop

# Create the wall bracket
bracket_length = 100  # mm
bracket_width = 600   # mm
bracket_thickness = 20 # mm

bracket = Part.makeBox(bracket_length, bracket_width, bracket_thickness)
bracket_obj = doc.addObject("Part::Feature", "Bracket")
bracket_obj.Shape = bracket
bracket_obj.Placement.Base = FreeCAD.Base.Vector(0, table_width, table_thickness)

# Create the folding mechanism (hinge)
hinge_radius = 10  # mm
hinge_thickness = 5 # mm

hinge = Part.makeCylinder(hinge_radius, hinge_thickness)
hinge_obj = doc.addObject("Part::Feature", "Hinge")
hinge_obj.Shape = hinge
hinge_obj.Placement.Base = FreeCAD.Base.Vector(bracket_length, table_width / 2, table_thickness)

# Fold the bracket to form the table
folded_bracket = bracket_obj.Shape.copy()
folded_bracket.Placement = FreeCAD.Placement(FreeCAD.Base.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Base.Vector(0, 1, 0), 90))
folded_bracket_obj = doc.addObject("Part::Feature", "FoldedBracket")
folded_bracket_obj.Shape = folded_bracket

# Recompute the document to update the view
doc.recompute()
