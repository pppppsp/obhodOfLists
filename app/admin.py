from django.contrib import admin
from app.models import *

admin.site.register(DepartmentModel)
admin.site.register(StatusModel)
admin.site.register(RoleModel)
admin.site.register(NameChildPostModel)
admin.site.register(typWorkAround)


@admin.register(PostChildModel)
class PostChildModelAdmin(admin.ModelAdmin):
    list_display=[ 'user', 'childpost']

@admin.register(WorkaroundSheetModel)
class WorkaroundSheetModelAdmin(admin.ModelAdmin):
    list_display=['nameofpoint','decription','depart','date_of_create','date_of_update']

@admin.register(WorkaroundModel)
class WorkaroundModelAdmin(admin.ModelAdmin):
    list_display = ['user','status','date_of_create','date_of_update']

@admin.register(SignatureModel)
class SignatureModelAdmin(admin.ModelAdmin):
    list_display = ['wam', 'wasm','user','comment']

@admin.register(CustomUser)
class CustomUserModel(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name', 'patronymic', 'birthday_date', 'role', 'depart', 'date_end', 'signature']
# Register your models here.
