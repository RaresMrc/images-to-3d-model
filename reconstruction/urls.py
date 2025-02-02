from django.urls import path
from .views import ReconstructionView

from django.urls import path
from .views import ReconstructionView, DownloadView, JobStatusView

urlpatterns = [
    path('', ReconstructionView.as_view(), name='reconstruction'),
    path('download/<uuid:job_id>/<str:file_type>/', DownloadView.as_view(), name='download'),
    path('job-status/<uuid:job_id>/', JobStatusView.as_view(), name='job-status'),
]