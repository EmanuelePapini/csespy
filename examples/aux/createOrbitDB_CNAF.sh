#!/bin/bash
source /storage/gpfs_data/limadou/dagiorda/env.sh


python ./createOrbitDB_CNAF.py

cp CSES01_orbitdb.h5 /storage/gpfs_data/limadou/dagiorda/csespy_dev/examples/aux/CSES01_orbitdb_HTcondor.h5 

exit 0
