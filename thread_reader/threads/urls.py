from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tweet/<int:twid>/', views.tweet, name='tweet'),
    path('load-more/', views.expand_thread, name="more"),
    path('open-thread/', views.new_thread, name="open")
]
