from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import csv
from datetime import datetime, timedelta

from apps.audit.models import AuditLog
from apps.users.constants import UserRole

User = get_user_model()


class AuditPageView(LoginRequiredMixin, TemplateView):
    template_name = 'audit/audit.html'
    
    def dispatch(self, request, *args, **kwargs):
        from apps.roles.utils.permissions import has_permission
        if request.user.role != UserRole.ADMIN and not has_permission(request.user, 'audit', 'view'):
            from django.shortcuts import redirect
            return redirect('vaults_web:vaults_page')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        context['is_admin'] = self.request.user.role == UserRole.ADMIN
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_logs_view(request):
    from apps.roles.utils.permissions import has_permission
    if request.user.role != UserRole.ADMIN and not has_permission(request.user, 'audit', 'view'):
        return Response(
            {'error': 'Доступ запрещён.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    
    user_filter = request.query_params.get('user_id')
    if user_filter:
        try:
            user_id = int(user_filter)
            logs = logs.filter(user_id=user_id)
        except (ValueError, TypeError):
            pass
    
    action_filter = request.query_params.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    resource_type_filter = request.query_params.get('resource_type')
    if resource_type_filter:
        logs = logs.filter(resource_type=resource_type_filter)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_obj = timezone.make_aware(date_from_obj)
            logs = logs.filter(timestamp__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    date_to = request.query_params.get('date_to')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = timezone.make_aware(date_to_obj) + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    limit = request.query_params.get('limit')
    if limit:
        try:
            limit = int(limit)
            logs = logs[:limit]
        except (ValueError, TypeError):
            pass
    
    log_list = []
    for log in logs:
        log_list.append({
            'id': log.id,
            'user': log.user.email,
            'user_id': log.user.id,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'timestamp': log.timestamp,
            'ip_address': str(log.ip_address) if log.ip_address else None,
            'user_agent': log.user_agent,
        })
    
    users = User.objects.filter(audit_logs__isnull=False).distinct().order_by('email')
    user_list = [{'id': u.id, 'email': u.email} for u in users]
    
    actions = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')
    resource_types = AuditLog.objects.values_list('resource_type', flat=True).distinct().order_by('resource_type')
    
    return Response({
        'logs': log_list,
        'users': user_list,
        'actions': list(actions),
        'resource_types': list(resource_types),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log_detail_view(request, log_id):
    from apps.roles.utils.permissions import has_permission
    if request.user.role != UserRole.ADMIN and not has_permission(request.user, 'audit', 'view'):
        return Response(
            {'error': 'Доступ запрещён.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        log = AuditLog.objects.select_related('user').get(id=log_id)
    except AuditLog.DoesNotExist:
        return Response(
            {'error': 'Запись журнала не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'id': log.id,
        'user': log.user.email,
        'user_id': log.user.id,
        'action': log.action,
        'resource_type': log.resource_type,
        'resource_id': log.resource_id,
        'details': log.details,
        'timestamp': log.timestamp,
        'ip_address': str(log.ip_address) if log.ip_address else None,
        'user_agent': log.user_agent,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_logs_export_view(request):
    from apps.roles.utils.permissions import has_permission
    if request.user.role != UserRole.ADMIN and not has_permission(request.user, 'audit', 'export'):
        return Response(
            {'error': 'Доступ запрещён.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    
    user_filter = request.query_params.get('user_id')
    if user_filter:
        try:
            user_id = int(user_filter)
            logs = logs.filter(user_id=user_id)
        except (ValueError, TypeError):
            pass
    
    action_filter = request.query_params.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    resource_type_filter = request.query_params.get('resource_type')
    if resource_type_filter:
        logs = logs.filter(resource_type=resource_type_filter)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_obj = timezone.make_aware(date_from_obj)
            logs = logs.filter(timestamp__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    date_to = request.query_params.get('date_to')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = timezone.make_aware(date_to_obj) + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    format_type = request.query_params.get('format', 'csv')
    
    if format_type == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        log_list = []
        for log in logs:
            log_list.append({
                'id': log.id,
                'user': log.user.email,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': str(log.ip_address) if log.ip_address else None,
                'user_agent': log.user_agent,
            })
        
        json.dump(log_list, response, ensure_ascii=False, indent=2, default=str)
        return response
    
    else:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Пользователь', 'Действие', 'Тип ресурса', 'ID ресурса', 'Дата и время', 'IP адрес', 'User Agent', 'Детали'])
        
        for log in logs:
            details_str = json.dumps(log.details, ensure_ascii=False) if log.details else ''
            writer.writerow([
                log.id,
                log.user.email,
                log.action,
                log.resource_type,
                log.resource_id,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                str(log.ip_address) if log.ip_address else '',
                log.user_agent,
                details_str,
            ])
        
        return response
