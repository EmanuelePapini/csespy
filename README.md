# csespy

This repository contains a collection of python routines to read and process data from the CSES-01 spacecraft. This routines are designed to gather, process and store (optionally) payload observations in a given set of semiorbits, and to perform some basic analysis on the data.

It is intended for the internal use of the CSES-Limadou collaboration. Payload supported up to now are:
* EFD ULF/VLF/ELF (Electric Field Detector)
* SCM (Search Coil Magnetometer)
* HPM (High Precision Magnetometer)
* LAP (Langmuir Probe)
* PAP (Plasma Analyser Package)
* **HEPD (High Energy Particle Detector) *--> Support recentrly added***
* **HEPP-L, HEPP-H, HEPP-X (High Energy Package) *--> Support recentrly added***

Dependencies: matplotlib, skimage, mpl_toolkits, collections, scipy, copy, warnings, termcolor, numpy, h5py, flammkuchen, datetime

 NOTES: Ported from an experimental package firstly made on 30/03/2021 by Emanuele Papini


### Install ###

Simply download the repository in the desired folder to start using it.
If you have a PYTHONPATH already set, you can put the csespy folder directly there so that you can import the package from everywhere.

Authors: Emanuele Papini (EP) and Francesco Maria Follega (FMF)

### Files list ###

Files in this repos are named accordingly to their purpose.
* <ins>CSES_main.py</ins> : Contains the main class that is used as an interface for loading and processing of CSES data.
* <ins>CSES_core.py</ins> : Core routines/functions used to read the data.
* <ins>CSES_aux.py</ins> : Contains all auxiliary function for reading/manipulating data (e.g. filename parsing, naming convention, date conversion, reference frame conversion,...).
* <ins>CSES_raw.py</ins> : Routines to load the .h5 files "as it is" in their original format (RAW) without any manipulation (for advanced use and/or debugging).
* <ins>CSES_init.py</ins> : contains few simple instructions to initialize the environment. This requires (in its actual state) editing depending on the machine and/or where data are stored.

In addition, the folder blombly contains a collection of routines directly taken from EP personal python library (named blombly) that are used in csespy.

### Usage ###

The main class allow the user to load data from the cses missions without the need of specifying any filename in principle.
It only requires the location of the folder containing all the .h5 files (named following the convention explained in the CSES-01 data manual) from the instruments. This folder either need to be organized in subfolders following a strict scheme, or simply need to contain the .h5 files of interest (see the __init__ method in the **CSES** class in CSES_main.py)

#### Example ####
Assuming csespy is in the PYTHONPATH, and that data of interest are stored in `/CSES_data/` and that they are not structured in subfolders, the following commands load the EFD ELF waveforms for the orbit 104311 (orbit 10431, night side)
```
import csespy

#initialize class and tell it what orbit it will load 
css=csespy.CSES(path='/CSES_data/',orbitn='104311',unstructured_path=True) 

#load EFD ELF data
css.load_CSES(instrument='EFD',frequency='ELF') #equivalent to css.load_EFD() but different functions

#plot the data
css.plot_EFD(frequency='ELF')
```
This plot should appear

![EFD ELF orbit 10431(1)](./docs/Figure_EFD_104311.png "EFD ELF orbit 10431(1)")


### Contacts ###

Emanuele Papini - INAF, Istituto di Astrofisica e Planetologia Spaziali (emanuele.papini@inaf.it).

Francesco Maria Follega - TIFPA, Università di Trento (francesco.follega@unitn.it).
