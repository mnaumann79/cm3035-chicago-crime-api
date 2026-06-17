from django.contrib import admin
from .models import OffenseCategory, District, Incident


@admin.register(OffenseCategory)
class OffenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'code')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('district_num', 'name', 'area_type', 'population')
    list_filter = ('area_type',)
    search_fields = ('name',)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'date', 'primary_type', 'district', 'arrest', 'domestic')
    list_filter = ('arrest', 'domestic', 'primary_type', 'district')
    search_fields = ('case_number', 'block')
    date_hierarchy = 'date'
