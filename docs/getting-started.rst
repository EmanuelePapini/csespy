Getting started
===============
Install
-------

Installation
~~~~~~~~~~~~

csespy is a lightweight collection of Python tools to read and process
data from the CSES-01 spacecraft. You can install it in-place for
development or add the `csespy` folder to your `PYTHONPATH`.

Recommended (editable install):

.. code-block:: bash

	python -m pip install -e .

If you prefer not to install, ensure the repository root is on your
`PYTHONPATH` so you can `import csespy` from anywhere.

Dependencies
~~~~~~~~~~~~

csespy requires a few common scientific Python packages. Typical
dependencies include `numpy`, `h5py`, `matplotlib`, `scipy`, and
`flamkuchen`/`flammkuchen` where used. See `docs/requirements.txt` for
an approximate list used to build the documentation.

Quickstart
----------

Minimal example (assumes `csespy` is importable and your data are in
`/CSES_data/`):

.. code-block:: python

	import csespy
	import pylab as plt

	css = csespy.CSES(path='/CSES_data/', orbitn='104311', unstructured_path=True)
	css.load_CSES('EFD_ELF')

	fig, ax = plt.subplots()
	css.plot_payload('EFD_ELF', fig=fig, ax=ax)
	plt.show()

Examples
--------

See the `examples` folder in the repository for small runnable
examples (for instance `examples/example.py` and
`examples/example_db.py`). These demonstrate common workflows and how
to create or query orbit databases.

Author and Contacts
-------------------

Authors: Emanuele Papini and Francesco Maria Follega. For questions
refer to the project README or contact the listed authors in the
repository.