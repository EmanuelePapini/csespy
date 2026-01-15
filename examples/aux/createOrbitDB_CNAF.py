#!/usr/bin/env python3
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ----------------------------
# Filename parsing
# ----------------------------
_ORBIT_RE = re.compile(r"_(\d{6})_20\d{2}")
_TIME_RE  = re.compile(r"_(\d{8})_(\d{6})_(\d{8})_(\d{6})_")

def parse_orbitn(path: str) -> str:
    base = os.path.basename(path)
    m = _ORBIT_RE.search(base)
    if not m:
        raise ValueError(f"Cannot parse orbit number from: {base}")
    return m.group(1)  # already zero-padded string

def parse_start_end(path: str):
    base = os.path.basename(path)
    m = _TIME_RE.search(base)
    if not m:
        raise ValueError(f"Cannot parse start/end time from: {base}")
    t0 = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    t1 = datetime.strptime(m.group(3) + m.group(4), "%Y%m%d%H%M%S")
    return t0, t1


# ----------------------------
# Zarr / HDF5 openers
# ----------------------------
def open_any(path: str):
    """
    Returns (kind, handle, closer)
    kind: "zarrzip" or "h5"
    handle: zarr group or h5py file
    closer: callable
    """
    pl = path.lower()
    if pl.endswith(".zarr.zip") or pl.endswith(".zip"):
        import zarr
        from zarr.storage import ZipStore  # IMPORTANT (fix for your error)
        store = ZipStore(path, mode="r")
        root = zarr.open_group(store, mode="r")

        def _close():
            try:
                store.close()
            except Exception:
                pass

        return "zarrzip", root, _close

    if pl.endswith(".h5") or pl.endswith(".hdf5"):
        import h5py
        f = h5py.File(path, "r")

        def _close():
            try:
                f.close()
            except Exception:
                pass

        return "h5", f, _close

    raise ValueError(f"Unsupported file type: {path}")


# ----------------------------
# Tree walking utilities
# ----------------------------
def _iter_group_items(node):
    """Return an iterator of (key, value) for a zarr group across v2/v3 APIs."""
    if hasattr(node, "items"):
        try:
            return node.items()
        except Exception:
            pass

    try:
        return ((k, node[k]) for k in node)
    except Exception:
        pass

    if hasattr(node, "group_keys") and hasattr(node, "array_keys"):
        try:
            keys = list(node.group_keys()) + list(node.array_keys())
            return ((k, node[k]) for k in keys)
        except Exception:
            pass

    if hasattr(node, "members"):
        try:
            members = node.members()
            if isinstance(members, dict):
                return members.items()
            return ((m.name.split("/")[-1], m) for m in members)
        except Exception:
            pass

    return iter(())


def _is_zarr_array(obj):
    return hasattr(obj, "shape") and hasattr(obj, "dtype")


def iter_zarr_arrays(root):
    stack = [("", root)]
    while stack:
        prefix, node = stack.pop()
        for k, v in _iter_group_items(node):
            p = f"{prefix}/{k}" if prefix else k
            if _is_zarr_array(v):
                yield p, v
            else:
                stack.append((p, v))

def find_zarr_array(root, name_upper: str):
    """
    Find first array whose path ends with /NAME or contains NAME.
    """
    name_upper = name_upper.upper()
    for p, arr in iter_zarr_arrays(root):
        pu = p.upper()
        if pu.endswith(name_upper) or (name_upper in pu):
            return p, arr
    return None, None

def iter_h5_datasets(h5obj):
    import h5py
    out = []

    def visitor(name, o):
        if isinstance(o, h5py.Dataset):
            out.append((name, o))
    h5obj.visititems(visitor)
    return out

def find_h5_dataset(h5obj, name_upper: str):
    name_upper = name_upper.upper()
    for p, ds in iter_h5_datasets(h5obj):
        pu = p.upper()
        if pu.endswith(name_upper) or (name_upper in pu):
            return p, ds
    return None, None


# ----------------------------
# Time index heuristics
# ----------------------------
def _to_1d(x):
    x = np.asarray(x)
    if x.ndim == 2 and x.shape[1] == 1:
        x = x[:, 0]
    return x.reshape(-1)

def make_time_index(time_arr, t_start, t_end, n_fallback):
    """
    Build a pandas DatetimeIndex in UTC.

    If time_arr exists:
      - datetime64 -> use it
      - numeric:
          >1e14 => ns epoch
          ~1e9..2e10 => seconds epoch
          ~1e12..2e13 => ms epoch
          otherwise => seconds since orbit start
    Else:
      fallback: linear spacing between filename t_start/t_end
    """
    ts_start = pd.Timestamp(t_start, tz="UTC")
    ts_end = pd.Timestamp(t_end, tz="UTC")

    if time_arr is None:
        secs = np.linspace(t_start.timestamp(), t_end.timestamp(), n_fallback, dtype=float)
        return pd.to_datetime(secs, unit="s", utc=True)

    t = np.asarray(time_arr)
    if np.issubdtype(t.dtype, np.datetime64):
        idx = pd.to_datetime(t)
        if idx.tz is None:
            idx = idx.tz_localize("UTC", ambiguous="infer", nonexistent="shift_forward")
        # sanity check: fallback to filename-based if outside expected range
        if idx.min() < ts_start - pd.Timedelta(days=1) or idx.max() > ts_end + pd.Timedelta(days=1):
            secs = np.linspace(t_start.timestamp(), t_end.timestamp(), n_fallback, dtype=float)
            return pd.to_datetime(secs, unit="s", utc=True)
        return idx

    t = _to_1d(t.astype("float64"))
    t0 = np.nanmin(t)
    tmax = np.nanmax(t)

    if tmax > 1e14:  # ns epoch
        idx = pd.to_datetime(t.astype("int64"), unit="ns", utc=True)
    elif 1e12 <= t0 <= 2e13:  # ms epoch
        idx = pd.to_datetime(t, unit="ms", utc=True)
    elif 1e9 <= t0 <= 2e10:  # seconds epoch
        idx = pd.to_datetime(t, unit="s", utc=True)
    else:
        # seconds since orbit start
        idx = pd.to_datetime([t_start + timedelta(seconds=float(s)) for s in t]).tz_localize("UTC")

    if idx.min() < ts_start - pd.Timedelta(days=1) or idx.max() > ts_end + pd.Timedelta(days=1):
        secs = np.linspace(t_start.timestamp(), t_end.timestamp(), n_fallback, dtype=float)
        return pd.to_datetime(secs, unit="s", utc=True)
    return idx


# ----------------------------
# Extract GEO from one file
# ----------------------------
def extract_geo_track(path: str, spacecraft="CSES01", step=1):
    """
    Returns DataFrame with index=Time and columns: lat, lon, alt, orbitn, spacecraft
    """
    t_start, t_end = parse_start_end(path)
    orbitn = parse_orbitn(path)

    kind, h, closer = open_any(path)
    try:
        if kind == "zarrzip":
            lat_p, lat_a = find_zarr_array(h, "GEO_LAT")
            lon_p, lon_a = find_zarr_array(h, "GEO_LON")

            # altitude can be named differently
            alt_p, alt_a = find_zarr_array(h, "ALTITUDE")
            if alt_a is None:
                alt_p, alt_a = find_zarr_array(h, "GEO_ALT")

            # time can be UTC_TIME or similar
            time_p, time_a = find_zarr_array(h, "UTC_TIME")
            if time_a is None:
                time_p, time_a = find_zarr_array(h, "TIME")
            if time_a is None:
                time_p, time_a = find_zarr_array(h, "VERSETIME")

            if lat_a is None or lon_a is None:
                raise RuntimeError(f"Missing GEO_LAT/GEO_LON (found lat={lat_p}, lon={lon_p})")

            lat = _to_1d(lat_a[:]).astype(float)
            lon = _to_1d(lon_a[:]).astype(float)

            if alt_a is not None:
                alt = _to_1d(alt_a[:]).astype(float)
            else:
                alt = np.full_like(lat, np.nan, dtype=float)

            n = min(len(lat), len(lon), len(alt))
            lat, lon, alt = lat[:n], lon[:n], alt[:n]

            time_arr = _to_1d(time_a[:])[:n] if time_a is not None else None
            idx = make_time_index(time_arr, t_start, t_end, n_fallback=n)

        else:  # h5
            lat_p, lat_d = find_h5_dataset(h, "GEO_LAT")
            lon_p, lon_d = find_h5_dataset(h, "GEO_LON")
            alt_p, alt_d = find_h5_dataset(h, "ALTITUDE")
            if alt_d is None:
                alt_p, alt_d = find_h5_dataset(h, "GEO_ALT")
            time_p, time_d = find_h5_dataset(h, "UTC_TIME")
            if time_d is None:
                time_p, time_d = find_h5_dataset(h, "TIME")
            if time_d is None:
                time_p, time_d = find_h5_dataset(h, "VERSETIME")

            if lat_d is None or lon_d is None:
                raise RuntimeError(f"Missing GEO_LAT/GEO_LON (found lat={lat_p}, lon={lon_p})")

            lat = _to_1d(lat_d[:]).astype(float)
            lon = _to_1d(lon_d[:]).astype(float)
            if alt_d is not None:
                alt = _to_1d(alt_d[:]).astype(float)
            else:
                alt = np.full_like(lat, np.nan, dtype=float)

            n = min(len(lat), len(lon), len(alt))
            lat, lon, alt = lat[:n], lon[:n], alt[:n]

            time_arr = _to_1d(time_d[:])[:n] if time_d is not None else None
            idx = make_time_index(time_arr, t_start, t_end, n_fallback=n)

        # decimate
        if step > 1:
            lat = lat[::step]
            lon = lon[::step]
            alt = alt[::step]
            idx = idx[::step]

        df = pd.DataFrame(
            {
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "orbitn": orbitn,
                "spacecraft": spacecraft,
            },
            index=pd.DatetimeIndex(idx, name="Time"),
        )
        return df

    finally:
        closer()


# ----------------------------
# Folder scan + build DB
# ----------------------------
def scan_files(root_dir: str, include_h5=False):
    # Support glob patterns in root_dir (e.g. "/path/*/*/")
    if any(ch in root_dir for ch in "*?["):
        roots = [Path(p) for p in sorted(Path("/").glob(root_dir.lstrip("/")))]
    else:
        roots = [Path(root_dir)]

    zarr_files = []
    h5_files = []
    for root in roots:
        zarr_files.extend(root.rglob("*.zarr.zip"))
    if include_h5:
        for root in roots:
            h5_files.extend(root.rglob("*.h5"))
            h5_files.extend(root.rglob("*.hdf5"))
    files = [str(p) for p in zarr_files] + [str(p) for p in h5_files]
    files.sort()
    return files

def build_orbitdb_from_folder(
    root_dir: str,
    out_h5: str,
    step=1,
    include_h5=False,
    spacecraft="CSES01",
    key="orbitdb",
):
    files = scan_files(root_dir, include_h5=include_h5)
    print(f"[SCAN] Found {len(files)} files under: {root_dir}")

    tracks = []
    ok = bad = 0

    for i, fpath in enumerate(files, 1):
        try:
            df = extract_geo_track(fpath, spacecraft=spacecraft, step=step)
            tracks.append(df)
            ok += 1
        except Exception as e:
            bad += 1
            print(f"[WARN] {i}/{len(files)} skip geo: {os.path.basename(fpath)} -> {e}")

        if ok and ok % 100 == 0:
            print(f"[PROGRESS] ok={ok} bad={bad}")
            print(fpath)
            # break

    if not tracks:
        raise RuntimeError("No tracks extracted; nothing to save.")

    odb = pd.concat(tracks, axis=0).sort_index()
    odb["orbitn"] = odb["orbitn"].astype(str).str.zfill(6)

    # Save one pandas DataFrame to HDF5
    odb.to_hdf(out_h5, key=key, mode="w", format="table")
    print(f"[OK] Saved: {out_h5}")
    print(f"     rows={len(odb):,}  orbits={odb['orbitn'].nunique():,}  ok_files={ok} bad_files={bad}")
    return odb


if __name__ == "__main__":
    # Example for your storage tree
    ROOT_DIR = "/storage/gpfs_data/limadou/data/cses_data/CSES01/EFD_ULF/*/*/"
    OUT_H5   = "CSES01_orbitdb.h5"

    # step: 1 keeps all geo points; 5 or 10 makes the DB much smaller (often still fine for selection)
    STEP = 1

    build_orbitdb_from_folder(
        root_dir=ROOT_DIR,
        out_h5=OUT_H5,
        step=STEP,
        include_h5=False,   # set True if you also want to scan .h5 files
        spacecraft="CSES01",
        key="orbitdb",
    )
