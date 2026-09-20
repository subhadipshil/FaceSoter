"""
Dialogs package for FaceSoter UI.
"""

from facesoter.ui.dialogs.model_setup_dialog import ModelSetupDialog
from facesoter.ui.dialogs.face_picker_dialog import FacePickerDialog
from facesoter.ui.dialogs.review_dialog import ReviewDialog
from facesoter.ui.dialogs.failed_files_dialog import FailedFilesDialog

__all__ = [
    "ModelSetupDialog",
    "FacePickerDialog",
    "ReviewDialog",
    "FailedFilesDialog",
]
