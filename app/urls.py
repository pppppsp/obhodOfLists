from django.urls import path, include
from django.conf import settings
from .views import *
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import get_roles

urlpatterns = [ 
    # main
    path('', MainView.MainPage, name='index'),
    path('admin/create-user/', AdminView.admin_create_user, name='admin_create_user'),

    # posts
    path('admin/post-list/', AdminView.postsListFunc, name='admin_post_list'),
    path('admin/post-filter/', AdminView.search_and_filter, name='admin-filter'),
    path('admin/add-childpost/', AdminView.add_childpost, name='admin-add-childpost'),
    path('admin/add-childpost/delete/<int:id>/', AdminView.del_childpost, name='admin-del-childpost'),
    path('admin/add-childpost-user/delete/<int:id>/', AdminView.del_childpost_user, name='admin-del-childpost-user'),
    path('admin/assign-post/', AdminView.assign_post, name='admin-assign-post'),
    path('admin/edit-post/<int:post_id>/', AdminView.edit_post, name='admin-edit-post'),
    # obhod admin 
    path('admin/workaround/create/', AdminView.create_workaround, name='admin-create-workaround'),
    path('admin/workaround/<int:pk>/', AdminView.workaround_detail, name='admin-workaround-detail'),
    path('admin/workaround/accept/<int:sheet_id>/', AdminView.sign_sheet, name='admin-workaround-accept'),
    path('workaround/<int:workaround_id>/pdf/', AdminView.generate_workaround_pdf, name='generate_workaround_pdf'),
    path('workarounds/', AdminView.workaround_list, name='workaround-list'),
    path('delete/<int:pk>/', AdminView.delete_workaround, name='delete-workaround'),

    # depart
    path('admin/departments/', AdminView.department_list, name='admin-department-list'),
    path('admin/delete-department/<int:department_id>/', AdminView.delete_department, name='admin-delete-department'),
    path('admin/add-department/', AdminView.add_department, name='admin-add-department'),
    path('account/my_obhod/',ProfileUserView.myObhod, name='myobhod'),
    path('delete_workaround/<int:id>/', ProfileUserView.deleteWorkaround, name='delete_workaround'),

    # users 
    path('users/', AdminView.user_list, name='user-list'),
    path('users/edit-user/<int:user_id>/', AdminView.edit_user, name='admin-edit-user'),
    path('users/delete-user/<int:user_id>/', AdminView.delete_user, name='admin-delete-user'),

    path('list_user/', AdminView.list_users, name='list_user-admin'),
    path('list_user/delete/<int:id>/', ProfileUserView.user_delete, name='delete_user'),
    # profile
    path('account/profile/',ProfileUserView.profile, name='profile'),
    path('account/sign/',ProfileUserView.sign, name='sign'),
    path('account/sign/delete/',ProfileUserView.sign_delete, name='sign_delete'),
    path('account/my_post/', ProfileUserView.take_post, name='take_post'),

    path('get_roles/', get_roles, name='get_roles'),  # Новый маршрут для AJAX-запроса


    
    # auth link 
    path('account/login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('exit/', ProfileUserView.logout, name='logout'),
    path('account/', include('django.contrib.auth.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
