"""
Repositories package for FaceSoter database entities.
"""

from facesoter.core.database.repositories.person_repo import PersonRepository, Person, ReferenceFace
from facesoter.core.database.repositories.image_repo import ImageRepository, ImageRecord, DetectedFaceRecord
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord, JobFileRecord, ClassificationRecord
from facesoter.core.database.repositories.settings_repo import SettingsRepository, RegisteredModel

__all__ = [
    "PersonRepository",
    "Person",
    "ReferenceFace",
    "ImageRepository",
    "ImageRecord",
    "DetectedFaceRecord",
    "JobRepository",
    "JobRecord",
    "JobFileRecord",
    "ClassificationRecord",
    "SettingsRepository",
    "RegisteredModel",
]
