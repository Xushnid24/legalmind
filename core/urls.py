from django.urls import path
from .views import (
    case_list, case_detail, case_create, case_delete,
    analyze_case_view, search_cases_view, generate_document_view
)

urlpatterns = [
    path('', case_list, name='case_list'),
    path('case/<int:pk>/', case_detail, name='case_detail'),
    path('cases/create/', case_create, name='case_create'),  # <- исправил здесь
    path('case/delete/<int:pk>/', case_delete, name='case_delete'),

    path('analyze_case/', analyze_case_view, name='analyze_case'),
    path('search_cases/', search_cases_view, name='search_cases'),
    path('generate_document/', generate_document_view, name='generate_document'),
]
