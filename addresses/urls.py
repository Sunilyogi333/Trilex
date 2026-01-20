# addresses/api/urls.py

from django.urls import path

from addresses.api.views import (
    ProvinceListView,
    DistrictListView,
    MunicipalityListView,
    WardListView,
)

urlpatterns = [
    # -------------------------
    # READ-ONLY ADDRESS MASTER DATA
    # -------------------------

    # Provinces
    path(
        "provinces/",
        ProvinceListView.as_view(),
        name="address-province-list",
    ),

    # Districts by province
    path(
        "districts/<int:province_id>/",
        DistrictListView.as_view(),
        name="address-district-list",
    ),

    # Municipalities by district
    path(
        "municipalities/<int:district_id>/",
        MunicipalityListView.as_view(),
        name="address-municipality-list",
    ),

    # Wards by municipality
    path(
        "wards/<int:municipality_id>/",
        WardListView.as_view(),
        name="address-ward-list",
    ),
]
