# screw-sorter-sw

## Setup
To run blender simulation, need to install blender

### Initial Environment Setup:
1. Install conda
2. Run `conda env create --file environment.yml`
3. Activate environment using `conda activate screw-sorter`

### Updating Environment Setup:
1. Activate environment using `conda activate screw-sorter`
2. Update environment using `conda env update --file environment.yml --prune`

## Usage
Example command to run to generate sim images
`blender side_profile_2.blend --background --python ./scripts/run_sim.py`
