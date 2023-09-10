import trimesh
import os
import stat
import time

metric_screws = {
#                 size drive cap pitch length
# hex socket
    "92290A013": "M2_hex_socket_0.4_6",
    "92290A015": "M2_hex_socket_0.4_8",
    "92290A017": "M2_hex_socket_0.4_10",
    "92290A019": "M2_hex_socket_0.4_12",
    "92290A056": "M2.5_hex_socket_0.45_6",
    "92290A058": "M2.5_hex_socket_0.45_8",
    "92290A060": "M2.5_hex_socket_0.45_10",
    "92290A062": "M2.5_hex_socket_0.45_12",
    "91292A111": "M3_hex_socket_0.5_6",
    "91292A112": "M3_hex_socket_0.5_8",
    "91292A113": "M3_hex_socket_0.5_10",
    "91292A114": "M3_hex_socket_0.5_12",
 # hex rounded:
    "92095A453": "M2_hex_rounded_0.4_6",
    "92095A454": "M2_hex_rounded_0.4_8",
    "92095A104": "M2_hex_rounded_0.4_10",
    "92095A455": "M2_hex_rounded_0.4_12",
    "92095A458": "M2.5_hex_rounded_0.45_6",
    "92095A459": "M2.5_hex_rounded_0.45_8",
    "92095A460": "M2.5_hex_rounded_0.45_10",
    "92095A461": "M2.5_hex_rounded_0.45_12",
    "92095A179": "M3_hex_rounded_0.5_6",
    "92095A181": "M3_hex_rounded_0.5_8",
    "92095A182": "M3_hex_rounded_0.5_10",
    "92095A183": "M3_hex_rounded_0.5_12",
# hex flat:
    "92125A052": "M2_hex_flat_0.4_6",
    "92125A054": "M2_hex_flat_0.4_8",
    "92125A056": "M2_hex_flat_0.4_10",
    "92125A058": "M2_hex_flat_0.4_12",
    "92125A084": "M2.5_hex_flat_0.45_6",
    "92125A086": "M2.5_hex_flat_0.45_8",
    "92125A088": "M2.5_hex_flat_0.45_10",
    "92125A090": "M2.5_hex_flat_0.45_12",
    "92125A126": "M3_hex_flat_0.5_6",
    "92125A128": "M3_hex_flat_0.5_8",
    "92125A130": "M3_hex_flat_0.5_10",
    "92125A132": "M3_hex_flat_0.5_12",
# phlips rounded
    "92000A013": "M2_philips_rounded_0.4_6",
    "92000A015": "M2_philips_rounded_0.4_8",
    "92000A017": "M2_philips_rounded_0.4_10",
    "92000A019": "M2_philips_rounded_0.4_12",
    "92000A104": "M2.5_philips_rounded_0.45_6",
    "92000A105": "M2.5_philips_rounded_0.45_8",
    "92000A106": "M2.5_philips_rounded_0.45_10",
    "92000A107": "M2.5_philips_rounded_0.45_12",
    "92000A116": "M3_philips_rounded_0.5_6",
    "92000A118": "M3_philips_rounded_0.5_8",
    "92000A120": "M3_philips_rounded_0.5_10",
    "92000A122": "M3_philips_rounded_0.5_12",
# philips flat
    "92010A003": "M2_philips_flat_0.4_6",
    "92010A004": "M2_philips_flat_0.4_8",
    "92010A005": "M2_philips_flat_0.4_10",
    "92010A006": "M2_philips_flat_0.4_12",
    "92010A016": "M2.5_philips_flat_0.45_6",
    "92010A018": "M2.5_philips_flat_0.45_8",
    "92010A020": "M2.5_philips_flat_0.45_10",
    "92010A022": "M2.5_philips_flat_0.45_12",
    "92010A116": "M3_philips_flat_0.5_6",
    "92010A118": "M3_philips_flat_0.5_8",
    "92010A120": "M3_philips_flat_0.5_10",
    "92010A122": "M3_philips_flat_0.5_12",
}

# imperial_screws = [
# #                  size drive cap pitch length
# # hex socket
#     ("92196A459" ,"1_hex_socket_64_1/4"),
#     ("92196A062" ,"1_hex_socket_64_5/16"),
#     ("92196A064" ,"1_hex_socket_64_3/8"),
#     ("92196A424" ,"1_hex_socket_64_1/2"),
#     ("92196A077" ,"2_hex_socket_56_1/4"),
#     ("92196A078" ,"2_hex_socket_56_5/16"),
#     ("92196A079" ,"2_hex_socket_56_3/8"),
#     ("92196A081" ,"2_hex_socket_56_1/2"),
#     ("92196A092" ,"3_hex_socket_48_1/4"),
#     ("92196A094" ,"3_hex_socket_48_5/16"),
#     ("92196A101" ,"3_hex_socket_48_3/8"),
#     ("92196A102" ,"3_hex_socket_48_1/2"),
#     ("92196A106" ,"4_hex_socket_40_1/4"),
#     ("92196A107" ,"4_hex_socket_40_5/16"),
#     ("92196A108" ,"4_hex_socket_40_3/8"),
#     ("92196A110" ,"4_hex_socket_40_1/2"),
# # hex rounded
#     ("92949A316", "1_hex_socket_64_1/4"),
#     ("92949A889", "1_hex_socket_64_3/8"),
#     ("92949A890", "1_hex_socket_64_1/2"),
#     ("92949A077", "2_hex_socket_56_1/4"),
#     ("92949A078", "2_hex_socket_56_5/16"),
#     ("92949A079", "2_hex_socket_56_3/8"),
#     ("92949A081", "2_hex_socket_56_1/2"),
#     ("92949A325", "3_hex_socket_48_1/4"),
#     ("92949A899", "3_hex_socket_48_5/16"),
#     ("92949A326", "3_hex_socket_48_3/8"),
#     ("92949A900", "3_hex_socket_48_1/2"),
#     ("92949A106", "4_hex_socket_40_1/4"),
#     ("92949A107", "4_hex_socket_40_5/16"),
#     ("92949A108", "4_hex_socket_40_3/8"),
#     ("92949A110", "4_hex_socket_40_1/2"),
# # hex flat
#     ("92210A361", "1_hex_socket_64_1/4"),
#     ("92210A364", "1_hex_socket_64_3/8"),
#     ("92210A077", "2_hex_socket_56_1/4"),
#     ("92210A078", "2_hex_socket_56_5/16"),
#     ("92210A079", "2_hex_socket_56_3/8"),
#     ("92210A081", "2_hex_socket_56_1/2"),
#     ("92210A021", "3_hex_socket_48_1/4"),
#     ("92210A407", "3_hex_socket_48_5/16"),
#     ("92210A022", "3_hex_socket_48_3/8"),
#     ("92210A370", "3_hex_socket_48_1/2"),
#     ("92210A105", "4_hex_socket_40_1/4"),
#     ("92210A107", "4_hex_socket_40_5/16"),
#     ("92210A108", "4_hex_socket_40_3/8"),
#     ("92210A110", "4_hex_socket_40_1/2"),
# # philips rounded
#     ("91772A166", "1_philips_rounded_64_1/4"),
#     ("91772A502", "1_philips_rounded_64_5/16"),
#     ("91772A168", "1_philips_rounded_64_3/8"),
#     ("91772A170", "1_philips_rounded_64_1/2"),
#     ("91400A054", "2_philips_rounded_56_1/4"),
#     ("91400A056", "2_philips_rounded_56_5/16"),
#     ("91400A058", "2_philips_rounded_56_3/8"),
#     ("91400A062", "2_philips_rounded_56_1/2"),
#     ("91772A092", "3_philips_rounded_48_1/4"),
#     ("91772A093", "3_philips_rounded_48_5/16"),
#     ("91772A094", "3_philips_rounded_48_3/8"),
#     ("91772A096", "3_philips_rounded_48_1/2"),
#     ("91772A106", "4_philips_rounded_40_1/4"),
#     ("91772A107", "4_philips_rounded_40_5/16"),
#     ("91772A108", "4_philips_rounded_40_3/8"),
#     ("91772A110", "4_philips_rounded_40_1/2"),
# #philips flat
#     ("91771A066", "1_philips_flat_64_1/4"),
#     ("91771A068", "1_philips_flat_64_3/8"),
#     ("91771A070", "1_philips_flat_64_1/2"),
#     ("91771A104", "2_philips_flat_56_1/4"),
#     ("91771A078", "2_philips_flat_56_5/16"),
#     ("91771A105", "2_philips_flat_56_3/8"),
#     ("91771A081", "2_philips_flat_56_1/2"),
#     ("91771A092", "3_philips_flat_48_1/4"),
#     ("91771A093", "3_philips_flat_48_5/16"),
#     ("91771A094", "3_philips_flat_48_3/8"),
#     ("91771A096", "3_philips_flat_48_1/2"),
#     ("91771A106", "4_philips_flat_40_1/4"),
#     ("91771A107", "4_philips_flat_40_5/16"),
#     ("91771A108", "4_philips_flat_40_3/8"),
#     ("91771A110", "4_philips_flat_40_1/2"),
# ]


metric_screws_list = [
#                  size drive cap pitch length
# hex socket
    ("92290A013", "M2_hex_socket_0.4_6"),
    ("92290A015", "M2_hex_socket_0.4_8"),
    ("92290A017", "M2_hex_socket_0.4_10"),
    ("92290A019", "M2_hex_socket_0.4_12"),
    ("92290A056", "M2.5_hex_socket_0.45_6"),
    ("92290A058", "M2.5_hex_socket_0.45_8"),
    ("92290A060", "M2.5_hex_socket_0.45_10"),
    ("92290A062", "M2.5_hex_socket_0.45_12"),
    ("91292A111", "M3_hex_socket_0.5_6"),
    ("91292A112", "M3_hex_socket_0.5_8"),
    ("91292A113", "M3_hex_socket_0.5_10"),
    ("91292A114", "M3_hex_socket_0.5_12"),
# hex rounded
    ("92095A453", "M2_hex_rounded_0.4_6"),
    ("92095A454", "M2_hex_rounded_0.4_8"),
    ("92095A104", "M2_hex_rounded_0.4_10"),
    ("92095A455", "M2_hex_rounded_0.4_12"),
    ("92095A458", "M2.5_hex_rounded_0.45_6"),
    ("92095A459", "M2.5_hex_rounded_0.45_8"),
    ("92095A460", "M2.5_hex_rounded_0.45_10"),
    ("92095A461", "M2.5_hex_rounded_0.45_12"),
    ("92095A179", "M3_hex_rounded_0.5_6"),
    ("92095A181", "M3_hex_rounded_0.5_8"),
    ("92095A182", "M3_hex_rounded_0.5_10"),
    ("92095A183", "M3_hex_rounded_0.5_12"),
# hex flat
    ("92125A052", "M2_hex_flat_0.4_6"),
    ("92125A054", "M2_hex_flat_0.4_8"),
    ("92125A056", "M2_hex_flat_0.4_10"),
    ("92125A058", "M2_hex_flat_0.4_12"),
    ("92125A084", "M2.5_hex_flat_0.45_6"),
    ("92125A086", "M2.5_hex_flat_0.45_8"),
    ("92125A088", "M2.5_hex_flat_0.45_10"),
    ("92125A090", "M2.5_hex_flat_0.45_12"),
    ("92125A126", "M3_hex_flat_0.5_6"),
    ("92125A128", "M3_hex_flat_0.5_8"),
    ("92125A130", "M3_hex_flat_0.5_10"),
    ("92125A132", "M3_hex_flat_0.5_12"),
# philips rounded
    ("92000A013", "M2_philips_rounded_0.4_6"),
    ("92000A015", "M2_philips_rounded_0.4_8"),
    ("92000A017", "M2_philips_rounded_0.4_10"),
    ("92000A019", "M2_philips_rounded_0.4_12"),
    ("92000A104", "M2.5_philips_rounded_0.45_6"),
    ("92000A105", "M2.5_philips_rounded_0.45_8"),
    ("92000A106", "M2.5_philips_rounded_0.45_10"),
    ("92000A107", "M2.5_philips_rounded_0.45_12"),
    ("92000A116", "M3_philips_rounded_0.5_6"),
    ("92000A118", "M3_philips_rounded_0.5_8"),
    ("92000A120", "M3_philips_rounded_0.5_10"),
    ("92000A122", "M3_philips_rounded_0.5_12"),
# philips flat
    ("92010A003", "M2_philips_flat_0.4_6"),
    ("92010A004", "M2_philips_flat_0.4_8"),
    ("92010A005", "M2_philips_flat_0.4_10"),
    ("92010A006", "M2_philips_flat_0.4_12"),
    ("92010A016", "M2.5_philips_flat_0.45_6"),
    ("92010A018", "M2.5_philips_flat_0.45_8"),
    ("92010A020", "M2.5_philips_flat_0.45_10"),
    ("92010A022", "M2.5_philips_flat_0.45_12"),
    ("92010A116", "M3_philips_flat_0.5_6"),
    ("92010A118", "M3_philips_flat_0.5_8"),
    ("92010A120", "M3_philips_flat_0.5_10"),
    ("92010A122", "M3_philips_flat_0.5_12"),
]

imperial_screws = [
#                  size drive cap pitch length
# hex socket
    ("92196A459" ,"1_hex_socket_64_1/4"),
    ("92196A062" ,"1_hex_socket_64_5/16"),
    ("92196A064" ,"1_hex_socket_64_3/8"),
    ("92196A424" ,"1_hex_socket_64_1/2"),
    ("92196A077" ,"2_hex_socket_56_1/4"),
    ("92196A078" ,"2_hex_socket_56_5/16"),
    ("92196A079" ,"2_hex_socket_56_3/8"),
    ("92196A081" ,"2_hex_socket_56_1/2"),
    ("92196A092" ,"3_hex_socket_48_1/4"),
    ("92196A094" ,"3_hex_socket_48_5/16"),
    ("92196A101" ,"3_hex_socket_48_3/8"),
    ("92196A102" ,"3_hex_socket_48_1/2"),
    ("92196A106" ,"4_hex_socket_40_1/4"),
    ("92196A107" ,"4_hex_socket_40_5/16"),
    ("92196A108" ,"4_hex_socket_40_3/8"),
    ("92196A110" ,"4_hex_socket_40_1/2"),
# hex rounded
    ("92949A316", "1_hex_socket_64_1/4"),
    ("92949A889", "1_hex_socket_64_3/8"),
    ("92949A890", "1_hex_socket_64_1/2"),
    ("92949A077", "2_hex_socket_56_1/4"),
    ("92949A078", "2_hex_socket_56_5/16"),
    ("92949A079", "2_hex_socket_56_3/8"),
    ("92949A081", "2_hex_socket_56_1/2"),
    ("92949A325", "3_hex_socket_48_1/4"),
    ("92949A899", "3_hex_socket_48_5/16"),
    ("92949A326", "3_hex_socket_48_3/8"),
    ("92949A900", "3_hex_socket_48_1/2"),
    ("92949A106", "4_hex_socket_40_1/4"),
    ("92949A107", "4_hex_socket_40_5/16"),
    ("92949A108", "4_hex_socket_40_3/8"),
    ("92949A110", "4_hex_socket_40_1/2"),
# hex flat
    ("92210A361", "1_hex_socket_64_1/4"),
    ("92210A364", "1_hex_socket_64_3/8"),
    ("92210A077", "2_hex_socket_56_1/4"),
    ("92210A078", "2_hex_socket_56_5/16"),
    ("92210A079", "2_hex_socket_56_3/8"),
    ("92210A081", "2_hex_socket_56_1/2"),
    ("92210A021", "3_hex_socket_48_1/4"),
    ("92210A407", "3_hex_socket_48_5/16"),
    ("92210A022", "3_hex_socket_48_3/8"),
    ("92210A370", "3_hex_socket_48_1/2"),
    ("92210A105", "4_hex_socket_40_1/4"),
    ("92210A107", "4_hex_socket_40_5/16"),
    ("92210A108", "4_hex_socket_40_3/8"),
    ("92210A110", "4_hex_socket_40_1/2"),
# philips rounded
    ("91772A166", "1_philips_rounded_64_1/4"),
    ("91772A502", "1_philips_rounded_64_5/16"),
    ("91772A168", "1_philips_rounded_64_3/8"),
    ("91772A170", "1_philips_rounded_64_1/2"),
    ("91400A054", "2_philips_rounded_56_1/4"),
    ("91400A056", "2_philips_rounded_56_5/16"),
    ("91400A058", "2_philips_rounded_56_3/8"),
    ("91400A062", "2_philips_rounded_56_1/2"),
    ("91772A092", "3_philips_rounded_48_1/4"),
    ("91772A093", "3_philips_rounded_48_5/16"),
    ("91772A094", "3_philips_rounded_48_3/8"),
    ("91772A096", "3_philips_rounded_48_1/2"),
    ("91772A106", "4_philips_rounded_40_1/4"),
    ("91772A107", "4_philips_rounded_40_5/16"),
    ("91772A108", "4_philips_rounded_40_3/8"),
    ("91772A110", "4_philips_rounded_40_1/2"),
#philips flat
    ("91771A066", "1_philips_flat_64_1/4"),
    ("91771A068", "1_philips_flat_64_3/8"),
    ("91771A070", "1_philips_flat_64_1/2"),
    ("91771A104", "2_philips_flat_56_1/4"),
    ("91771A078", "2_philips_flat_56_5/16"),
    ("91771A105", "2_philips_flat_56_3/8"),
    ("91771A081", "2_philips_flat_56_1/2"),
    ("91771A092", "3_philips_flat_48_1/4"),
    ("91771A093", "3_philips_flat_48_5/16"),
    ("91771A094", "3_philips_flat_48_3/8"),
    ("91771A096", "3_philips_flat_48_1/2"),
    ("91771A106", "4_philips_flat_40_1/4"),
    ("91771A107", "4_philips_flat_40_5/16"),
    ("91771A108", "4_philips_flat_40_3/8"),
    ("91771A110", "4_philips_flat_40_1/2"),
]

# based on path to file, get path to STEP file directories
dir_path = os.path.dirname(os.path.realpath(__file__))
path_to_imperial_STEP = "".join((dir_path, "/../cads/imperial_STEP"))
path_to_metric_STEP = "".join((dir_path, "/../cads/metric_STEP"))
start_dir = os.getcwd()

os.chdir(path_to_metric_STEP)
files = os.listdir()

for f in files:
    try:
        # mesh = trimesh.Trimesh(
        #     **trimesh.interfaces.gmsh.load_gmsh(
        #         file_name = f,
        #         gmsh_args = [
        #             ("Mesh.Algorithm", 1),
        #             ("Mesh.CharacteristicLengthFromCurvature", 50),
        #             ("General.NumThreads", 10),
        #             ("Mesh.MinimumCirclePoints", 32)
        #         ]
        #     )
        # )
        name = metric_screws[f.split("_")[0]]
        try:
            os.mkdir(os.getcwd() + "/../metric_named_STEP", mode=0o777)
        except(FileExistsError):
            pass

        with open(f, "r") as original, open("".join([os.getcwd(), "/../metric_named_STEP/", name,".STEP"]), "w") as rename:
            for l in original:
                rename.write(l)

        # mesh.export("".join([os.getcwd(), "/../metric_STL/", name,".STL"]))

    except(Exception):
        pass

# change back to original directory
os.chdir(start_dir)
