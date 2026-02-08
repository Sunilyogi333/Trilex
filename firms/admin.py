from django.contrib import admin
from firms.models import Firm, FirmVerification, FirmInvitation, FirmMember

# Register your models here.

admin.site.register(Firm)
admin.site.register(FirmVerification)
admin.site.register(FirmInvitation)
admin.site.register(FirmMember)