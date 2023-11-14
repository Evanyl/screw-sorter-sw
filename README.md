# `screw-sorter-sw/sim/`

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
### Using scraper
1. Run `python sim/scripts/scraper.py --help` to see all options

### Using simulation
Example command to run to generate sim images
`blender side_profile_2.blend --background --python ./scripts/run_sim.py`

# `screw-sorter-sw/ui/`
Codebase for a fastener imaging station.

## How to run the UI
Go to this directory
```
cd sw
```
Run the UI python script
```
./data_collection_backend.py
```


## How to refresh the rclone token
We use rclone to copy our imaging tests to google drive.
It uses a token to upload to drive that expires pretty often (like daily?)

From command line, run
```
rclone config
```
Type `e` to select the `edit existing remote` option

Choose the `gdrive` option

We don't want to edit anything, so just keep pressing "enter" to select all the default options.

At some point, this option appears in terminal:
```
Already have a token - refresh?
y) Yes (default)
n) No
```
Press "enter" to select the default. Press "enter" again to use the autoconfig.

A google account webpage will appear. Choose the screwsorter459@gmail.com account.
Disregard the warning and hit continue till you get "Success!"

Return to the terminal, it should show "Got code". Press enter again until you return to the main menu, then you can type `q` to exit.

You can verify the token works by typing
```
rclone lsd gdrive:2306\ Screw\ Sorter
```

It should list the top-level directories in our screw sorter folder.

# `screw-sorter-sw/fw/`

## Re-Flashing Mirco

To reflash the micro without blowing the LEDs:

1. Put the dome-light PWM signal (`PA1`) on `3.3V` pin,
2. Put the LED back-light on PWM signal (`PA0`) on `GND` pin,
3. Move the jumpers on the BP so that hitting the reset button kicks off the bootloader
4. Flash new firmware with PlatformIO IDE,
5. Move the jumpers and PWM lines back to their previous locations.
