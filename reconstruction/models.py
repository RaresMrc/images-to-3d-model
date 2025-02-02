from django.db import models
import uuid
import os


class ReconstructionJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UPLOADED', 'Files Uploaded'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    result_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Job {self.id} - {self.status}"


class InputImage(models.Model):
    job = models.ForeignKey(ReconstructionJob, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='input_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def get_upload_path(self):
        return os.path.join('input_images', str(self.job.id), self.image.name)