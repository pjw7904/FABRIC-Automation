#!/bin/bash

# Install dependencies first.
./mtp_scripts/init_deps.sh

# Then install the MTP implementation.
./mtp_scripts/compile_mtp.sh

echo "MTP initalization complete. Please check to make sure all operations succeeded."
