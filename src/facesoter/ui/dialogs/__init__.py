"""
Dialogs package for FaceSoter UI.
"""

from facesoter.ui.dialogs.model_setup_dialog import ModelSetupDialog
from facesoter.ui.dialogs.face_picker_dialog import FacePickerDialog
from facesoter.ui.dialogs.review_dialog import ReviewDialog
from facesoter.ui.dialogs.failed_files_dialog import FailedFilesDialog
from facesoter.ui.dialogs.feature_poster_dialog import FeaturePosterDialog
from facesoter.ui.dialogs.single_group_review_dialog import SingleGroupReviewDialog

__all__ = [
    "ModelSetupDialog",
    "FacePickerDialog",
    "ReviewDialog",
    "FailedFilesDialog",
    "FeaturePosterDialog",
    "SingleGroupReviewDialog",
]
