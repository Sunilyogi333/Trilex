from django.db import models


class NotificationType(models.TextChoices):
    # Booking
    BOOKING_CREATED = "booking_created", "Booking Created"
    BOOKING_ACCEPTED = "booking_accepted", "Booking Accepted"
    BOOKING_REJECTED = "booking_rejected", "Booking Rejected"

    # Firm Invitation
    FIRM_INVITATION_RECEIVED = "firm_invitation_received", "Firm Invitation Received"
    FIRM_INVITATION_ACCEPTED = "firm_invitation_accepted", "Firm Invitation Accepted"
    FIRM_INVITATION_REJECTED = "firm_invitation_rejected", "Firm Invitation Rejected"
