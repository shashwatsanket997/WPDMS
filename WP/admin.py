from django.contrib import admin

# Register your models here.
from .models import WaterPlant,WaterPlantLoc,WarrentyYear,Consumables,repair_parts,User

admin.site.register(WaterPlant)

admin.site.register(WaterPlantLoc)

admin.site.register(WarrentyYear)
admin.site.register(Consumables)
admin.site.register(repair_parts)
admin.site.register(User)
