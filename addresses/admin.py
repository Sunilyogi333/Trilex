from django.contrib import admin
from addresses.models import Address, Province, District, Municipality, Ward

# Register your models here.
admin.site.register(Address)
admin.site.register(Province)
admin.site.register(District)
admin.site.register(Municipality)
admin.site.register(Ward)