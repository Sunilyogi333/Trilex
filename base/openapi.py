from drf_spectacular.utils import OpenApiParameter


PAGE_PARAMETER = OpenApiParameter(
    name="page",
    type=int,
    location=OpenApiParameter.QUERY,
    description="Page number",
)

PAGE_SIZE_PARAMETER = OpenApiParameter(
    name="page_size",
    type=int,
    location=OpenApiParameter.QUERY,
    description="Number of items per page",
)
