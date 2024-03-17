# Adapted from https://docs.platformio.org/en/latest/scripting/examples/override_package_files.html
print("apply_patches.py: Starting patching script")
from os.path import join, isfile

Import("env")
FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-arduinoststm32")
patchflag_path = join(FRAMEWORK_DIR, ".patching-done")

# patch file only if we didn't do it before
if not isfile(join(FRAMEWORK_DIR, ".patching-done")):
    print("apply_patches.py: Flag not seen, beginning patch")
    original_file = join(FRAMEWORK_DIR, "cores", "arduino", "HardwareSerial.h")
    patched_file = join("patches", "1-HardwareSerial-increase-buffer-size.patch")

    assert isfile(original_file) and isfile(patched_file)

    env.Execute("patch %s %s" % (original_file, patched_file))

    def _touch(path):
        with open(path, "w") as fp:
            fp.write("")

    env.Execute(lambda *args, **kwargs: _touch(patchflag_path))
else:
    print("apply_patches.py: Flag was seen, skipping patch")
