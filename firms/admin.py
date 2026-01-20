from django.contrib import admin
from firms.models import Firm, FirmVerification

# Register your models here.

admin.site.register(Firm)
admin.site.register(FirmVerification)