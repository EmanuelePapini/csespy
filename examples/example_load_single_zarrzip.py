import os

import csespy_dev as csespy

# Absolute path to one .zarr.zip file
zarr_file = (
    "/storage/gpfs_data/limadou/data/cses_data/CSES01/EFD_ELF/2020/01/CSES_01_EFD_2_L02_A1_110770_20200131_225632_20200131_233110_000.zarr.zip"
)

# Use unstructured_path=True so csespy searches directly in this folder
data_dir = os.path.dirname(zarr_file)
file_name = os.path.basename(zarr_file)

css = csespy.CSES(path=data_dir, unstructured_path=True)

css.select_data_to_load(search_string=file_name, append=False)
css.load_CSES(datakey="EFD_ELF", fix_data=False)

df = css.data["EFD_ELF"]
print("Loaded keys:", list(css.data.keys()))
print("EFD_ELF shape:", df.shape)
print(df.head())
