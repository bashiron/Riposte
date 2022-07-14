from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('thread/<int:id>/', views.thread, name='thread')
]
