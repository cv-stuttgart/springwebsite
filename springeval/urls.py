from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'springeval'
urlpatterns = [
    path('', TemplateView.as_view(template_name="springeval/index.html"), name="index"),
    path('stereo', views.stereo, name='stereo'),
    path('opticalflow', views.opticalflow, name='opticalflow'),
    path('sceneflow', views.sceneflow, name='sceneflow'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/edit', views.EditView.as_view(), name='edit'),
    path('user', views.userindex, name='user'),
    path('submit', views.submit, name="submit"),
    path('accounts/signup', views.signup, name="signup"),
    path('activate/<slug:uidb64>/<slug:token>/', views.activate, name='activate'),
    path('faq', TemplateView.as_view(template_name="springeval/faq.html"), name="faq"),
    path('download', TemplateView.as_view(template_name="springeval/download.html"), name="download"),
]
