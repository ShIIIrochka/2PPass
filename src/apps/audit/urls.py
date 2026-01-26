from django.urls import path

from apps.audit.views import (
    audit_logs_view,
    audit_log_detail_view,
    audit_logs_export_view,
)

app_name = 'audit'

urlpatterns = [
    path('', audit_logs_view, name='audit-logs'),
    path('export/', audit_logs_export_view, name='audit-logs-export'),
    path('<int:log_id>/', audit_log_detail_view, name='audit-log-detail'),
]
