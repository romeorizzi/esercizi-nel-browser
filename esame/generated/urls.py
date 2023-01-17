from django.urls import path
from . import views
from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    path('',views.esame, name='home'),
    path('knapsack',views.knapsack, name='knapsack'),
    path('lcs',views.lcs, name='lcs'),
    path('mst',views.mst, name='mst'),
    url('grafo_template',views.grafo_template, name='grafo_template'),
    path('retrieve_saved_solutions/<str:ex>',views.retrieve_saved_solutions, name='retrieve_saved_solutions'),
    path('save_solutions/<str:ex>',views.save_solutions,name='save_solutions'),
    path('simple_upload/<str:ex>/<str:task>',views.simple_upload,name='simple_upload'),
]