from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from base.constants.ai_query_types import QueryType

User = settings.AUTH_USER_MODEL


class AIQueryHistory(AbstractBaseModel):
    """
    Immutable log of AI-assisted legal queries.
    AI suggests, backend decides.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_queries"
    )

    # User input
    query = models.TextField()

    # AI classification
    query_type = models.CharField(
        max_length=30,
        choices=QueryType.choices
    )

    # AI-generated explanation / guidance
    answer = models.TextField(
        blank=True,
        null=True
    )

    # Case category suggested by AI (nullable)
    case_category = models.ForeignKey(
        "cases.CaseCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_queries"
    )

    # Backend-selected recommendations
    recommended_lawyers = models.ManyToManyField(
        "lawyers.Lawyer",
        blank=True,
        related_name="ai_recommendations"
    )

    recommended_firms = models.ManyToManyField(
        "firms.Firm",
        blank=True,
        related_name="ai_recommendations"
    )

    # Optional: store raw AI payload for audits
    raw_ai_response = models.JSONField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"AIQueryHistory(user={self.user}, type={self.query_type})"
