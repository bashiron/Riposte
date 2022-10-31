from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tweet/<int:twid>/', views.tweet, name='tweet'),
    path('load-more/', views.expand_chat, name="more"),
    path('open-chat/', views.new_chat, name="open"),
    path('collapse/', views.collapse_chat, name="close")
]
