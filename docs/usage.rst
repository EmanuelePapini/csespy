Usage
=====
Common Workflows
================

Loading data
------------

The primary entry point is the `CSES` class. Create an instance
pointing to a folder containing CSES HDF5 files (the folder may be
structured or unstructured):

.. code-block:: python

	from csespy import CSES

	cs = CSES(path='/path/to/CSES_data', orbitn='104311', unstructured_path=True)
	cs.load_CSES('EFD_ELF')

Selecting files
---------------

Use `select_data_to_load()` to configure which orbits or timespan to
load. The `find_files_to_load()` and `find_available_files()` helpers
help inspect which files match your selection.

Plotting
--------

Many payloads include a `plot_payload()` helper for quick visual
inspection. The example in `getting-started` shows a minimal plotting
workflow.

Post-processing and fixing data
-------------------------------

Utilities in `CSES_fixdata.py` and `CSES_aux.py` provide small helpers
to clean and convert fields. Consult the API reference for the
available functions and their signatures.

Command-line and scripts
------------------------

The `examples/` directory contains small scripts that can be used as
templates for batch processing. For large-scale processing consider
writing a small wrapper that iterates over orbit numbers and stores
results to HDF5 or Zarr.

Further reading
---------------

- API reference: :doc:`api`
- Examples: the `examples/` folder in the repository