import trimesh

mesh = trimesh.Trimesh(
    **trimesh.interfaces.gmsh.load_gmsh(
        file_name = "92949A050_18-8 Stainless Steel Button Head Hex Drive Screw.STEP", 
        gmsh_args = [
            ("Mesh.Algorithm", 1),
            ("Mesh.CharacteristicLengthFromCurvature", 50),
            ("General.NumThreads", 10),
            ("Mesh.MinimumCirclePoints", 32)
        ]
    ))

mesh.export("Screw.STL")
