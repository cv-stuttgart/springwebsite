# Subsampling and ground truth files
This repository contains
- the code to compile the subsampling executables that are used by benchmark users to create submission files.
- the code to generate the ground truth files as needed by the benchmark website for evaluation

## Subsampling
### Build
- clone [HighFive](https://github.com/BlueBrain/HighFive) (tested with commit 5d88d87155a14cd694ee342c8f77e61815d2810a)
- create build folder: `mkdir build && cd build`
- execute cmake: `cmake ..`
- execute make: `make -j <numprocesses>`

The code was tested with gcc 11.3.0, cmake 3.22.1 on Ubuntu 22.

### Usage
The build result are six executables; disp1_subsampling, disp2_subsampling, flow_subsampling, disp1_robust_subsampling, disp2_robust_subsampling and flow_robust_subsampling, which are used to generate the corresponding submission files, e.g. via `./disp1_subsampling <path to disp1 results>`.

Please note that the true subsampling random numbers are withheld and have to be added in the *.cpp files in order to create correct submission executables.

## Ground truth eval files generation
Additionally, this repository contains the code to generate subsampled ground truth files (eval files) that are used by the benchmark website evaluation code:
- Install the required python libraries numpy and h5py.
- Set the environment variable SPRING_TESTPATH to the test split directory of the spring dataset that contains the ground truth files
- Run `python create_evalfiles.py`
- The resulting eval_*.hdf5 files are needed by the benchmark evaluation code.
