from django.urls import path
from . import views

urlpatterns = [
    # ─── Pages HTML ───
    path('', views.page_accueil, name='accueil'),
    path('admin-tables/', views.page_admin_tables, name='admin_tables'),
    path('tables/<int:id>/detail/', views.page_detail_table, name='detail_table_page'),

    # ─── API REST ───
    path('api/tables/', views.liste_tables, name='liste_tables'),
    path('api/tables/disponibles/', views.tables_disponibles, name='tables_disponibles'),
    path('api/tables/<int:id>/', views.detail_modifier_supprimer, name='detail_table'),
]