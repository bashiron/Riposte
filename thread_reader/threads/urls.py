from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tweet/<int:id>/', views.tweet, name='tweet'),
    path('thread/<int:id>/', views.thread, name="thread")
]
