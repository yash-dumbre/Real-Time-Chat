from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload_file, name='upload_file'),
    path('search/', views.search_messages, name='search_messages'),
    path('<str:room_name>/', views.room, name='room'),
    path('push/key/',       views.push_public_key, name='push_key'),
    path('push/subscribe/', views.push_subscribe,  name='push_subscribe'),
]