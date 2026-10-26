from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('<int:year>.html', views.calendar_page, name='calendar_page'),
]
