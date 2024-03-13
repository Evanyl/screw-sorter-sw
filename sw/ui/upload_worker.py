from PyQt5 import QtCore, QtGui, QtWidgets

class UploadWorker(QtCore.QObject):
    """Class designed for use in a thread to upload imaging runs from the station to the cloud."""
    finished = QtCore.pyqtSignal()

    def __init__(self, local_directory: str, remote_directory: str):
        """local_top_directory: folder containing all past sessions
            remote_top_directory: cloud folder containing all uploaded sessions"""
        super(UploadWorker, self).__init__()
        self.local_directory = local_directory
        self.remote_directory = remote_directory

        # check that these directories exist
        if not os.path.exists(local_directory):
            raise Exception(f"Could not create upload thread, {local_directory} not found")

    def run(self):
        print(f"Uploading to Drive. Remote drive path: {self.remote_directory}")
        print(f"On-device path: {self.local_directory}")
        try:
            # .copy() compares local_directory to remote_directory, only changing files that are different.
            # rclone.copy() uploads all top-level folders in self.local_directory as top-level folders in self.remote_directory.
            #rclone.copy(self.local_directory, self.remote_directory)
            print("should be rclonin!")
        except UnicodeDecodeError as uni_e:
            print(str(uni_e))
            print("Error. Wait a few seconds and click 'Upload to Google Drive' again.")
            print("If upload continues to fail after multiple retries, try typing this into your command line:")
            print(f"rclone copy {self.local_directory} {self.remote_directory}")
            return
            # Kenneth commentary: I think it's something to do with the image data not getting flushed to the file, so the copy() function finds files that are empty.
            # I find that it always works after I retry a few times, so it's not a high-prio bug.
        except Exception as e:
            print(str(e))
            return
        print(f"Entire upload complete")
        self.finished.emit()


