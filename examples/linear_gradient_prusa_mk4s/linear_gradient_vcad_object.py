import pyvcad as pv
import pyvcad_rendering as viz

materials = pv.default_materials
bar = pv.RectPrism(pv.Vec3(0,0,0), pv.Vec3(100,50,10), materials.id("gray"))
vcad_object = pv.FGrade(["x/100 + 0.5", "-x/100 + 0.5"], [materials.id("red"), materials.id("blue")], False) # A functional gradient that is 100% blue at x=-50 and 100% at x=50
vcad_object.set_child(bar)
viz.Render(vcad_object, materials) # Render the object first