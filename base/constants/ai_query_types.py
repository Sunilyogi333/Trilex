from django.db import models


class QueryType(models.TextChoices):
    LOOKUP = "lookup", "Lookup"
    INTERPRETATION = "interpretation", "Interpretation"
    CASE_BASED = "case_based", "Case Based"
    PREDICTIVE = "predictive", "Predictive"
    GENERAL = "general", "General"
    NOT_LEGAL = "not_legal", "Not Legal"
    RECOMMENDATION = "recommendation", "Recommendation"
