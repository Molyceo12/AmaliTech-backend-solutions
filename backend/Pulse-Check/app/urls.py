from django.urls import path
from .views import MonitorListView, MonitorCreateView, HeartbeatView, PauseView, MonitorStatusView

urlpatterns = [
    path('get-monitors', MonitorListView.as_view(), name='monitor-list'),
    path('register_monitor', MonitorCreateView.as_view(), name='monitor-create'),
    path('monitors/<str:pk>/status', MonitorStatusView.as_view(), name='monitor-status'),
    path('monitors/<str:pk>/heartbeat', HeartbeatView.as_view(), name='monitor-heartbeat'),
    path('monitors/<str:pk>/pause', PauseView.as_view(), name='monitor-pause'),
]
