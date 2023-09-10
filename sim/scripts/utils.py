import trimesh

from pathlib import Path

def convert_step_to_stl(step_file_path: Path, output_file_path: Path):
    assert step_file_path.exists(), f"{step_file_path} does not exist"
    mesh = trimesh.Trimesh(
        **trimesh.interfaces.gmsh.load_gmsh(
            file_name = str(step_file_path),
            gmsh_args = [
                ("Mesh.Algorithm", 6),
                ("Mesh.CharacteristicLengthFromCurvature", 50),
                ("General.NumThreads", 4),
                ("Mesh.MinimumCirclePoints", 32)
            ]
        ))

    mesh.export(str(output_file_path))
    assert output_file_path.exists(), f"{output_file_path} was not successfully created, silent error somewhere"
