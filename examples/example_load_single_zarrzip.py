import os

import csespy_dev as csespy

# Absolute path to one .zarr.zip file
zarr_file = (
    "/storage/gpfs_data/limadou/data/cses_data/CSES01/EFD_ELF/2019/01/"
    "CSES_01_SCM_2_L02_A2_053980_20190123_081535_20190123_082228_000.zarr.zip"
)

# Use unstructured_path=True so csespy searches directly in this folder
data_dir = os.path.dirname(zarr_file)
file_name = os.path.basename(zarr_file)

css = csespy.CSES(path=data_dir, unstructured_path=True)

# Select exactly this file by filename substring
css.select_data_to_load(search_string=file_name, append=False)

# SCM instrument number 2 corresponds to ELF -> datakey is SCM_ELF
css.load_CSES(datakey="SCM_ELF", fix_data=False)

if "SCM_ELF" not in css.data:
    raise RuntimeError("SCM_ELF was not loaded. Check path/datakey/search_string.")

df = css.data["SCM_ELF"]
print("Loaded keys:", list(css.data.keys()))
print("SCM_ELF shape:", df.shape)
print(df.head())
