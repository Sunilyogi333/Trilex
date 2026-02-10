from django.db import models

class CaseOwnerType(models.TextChoices):
    LAWYER = "lawyer", "Lawyer"
    FIRM = "firm", "Firm"

class CourtType(models.TextChoices):
    DISTRICT = "district", "District Court"
    HIGH = "high", "High Court"
    SUPREME = "supreme", "Supreme Court"

class CaseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REGISTERED = "registered", "Registered"
    ONGOING = "ongoing", "Ongoing"
    COMPLETED = "completed", "Completed"

class CaseLawyerRole(models.TextChoices):
    LEAD = "lead", "Lead Lawyer"
    ASSISTANT = "assistant", "Assistant Lawyer"

class CaseDocumentUploader(models.TextChoices):
    LAWYER = "lawyer", "Lawyer"
    FIRM = "firm", "Firm"
    CLIENT = "client", "Client"

class CaseDocumentFileType(models.TextChoices):
    IMAGE = "image", "Image"
    PDF = "pdf", "PDF"
    OTHER = "other", "Other"

class CaseDateType(models.TextChoices):
    TARIK = "tarik", "Tarik Date"
    PESI = "pesi", "Pesi Date"
    OTHER = "other", "Other"
