# reconstruction/views.py
import shutil

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from .models import ReconstructionJob, InputImage
import os
from django.conf import settings
from .tasks import process_images, run_colmap_pipeline
from django.http import FileResponse, Http404
from django.conf import settings
import os


class ReconstructionView(View):
    template_name = 'reconstruction/upload.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            job = ReconstructionJob.objects.create()

            files = request.FILES.getlist('images')

            # Create working directories
            work_dir = os.path.join(settings.MEDIA_ROOT, f'reconstruction_{job.id}')
            colmap_dir = os.path.join(work_dir, 'colmap')
            database_path = os.path.join(colmap_dir, 'database.db')
            image_dir = os.path.join(colmap_dir, 'images')
            sparse_dir = os.path.join(colmap_dir, 'sparse')
            dense_dir = os.path.join(colmap_dir, 'dense')

            for dir_path in [colmap_dir, image_dir, sparse_dir, dense_dir]:
                os.makedirs(dir_path, exist_ok=True)

            # Save images and copy them to the working directory
            for file in files:
                img_obj = InputImage.objects.create(job=job, image=file)

                source_path = os.path.join(settings.MEDIA_ROOT, str(img_obj.image))
                dest_path = os.path.join(image_dir, os.path.basename(file.name))
                shutil.copy2(source_path, dest_path)

            run_colmap_pipeline(
                colmap_dir=colmap_dir,
                database_path=database_path,
                image_dir=image_dir,
                sparse_dir=sparse_dir,
                dense_dir=dense_dir
            )

            return JsonResponse({
                'job_id': str(job.id),
                'status': 'SUCCESS',
                'message': 'Successfully processed images'
            })

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            return JsonResponse({
                'error': 'Processing failed',
                'message': str(e)
            }, status=500)


class DownloadView(View):
    def get(self, request, job_id, file_type):
        """
        Handles file downloads for reconstruction results.
        file_type can be 'sparse', 'dense', or 'mesh' to specify which model to download.
        """
        file_mapping = {
            'sparse': 'sparse/sparse.ply',
            'dense': 'dense/fused.ply',
            'mesh': 'dense/meshed.ply'
        }

        if file_type not in file_mapping:
            raise Http404("Invalid file type requested")

        base_path = os.path.join(settings.MEDIA_ROOT, f'reconstruction_{job_id}/colmap/')
        file_path = os.path.join(base_path, file_mapping[file_type])

        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404("Reconstruction file not found")

        # Open and return the file
        try:
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/octet-stream'
            )
            filename = os.path.basename(file_path)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            raise Http404(f"Error accessing file: {str(e)}")


class JobStatusView(View):
    def get(self, request, job_id):
        try:
            job = ReconstructionJob.objects.get(id=job_id)

            dense_path = os.path.join(settings.MEDIA_ROOT,
                                      f'reconstruction_{job_id}/colmap/dense/fused.ply')

            if os.path.exists(dense_path):
                return JsonResponse({
                    'status': 'completed',
                    'message': 'Reconstruction completed successfully'
                })
            else:
                return JsonResponse({
                    'status': 'processing',
                    'message': 'Reconstruction in progress'
                })

        except ReconstructionJob.DoesNotExist:
            return JsonResponse({
                'status': 'failed',
                'message': 'Job not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'failed',
                'message': str(e)
            }, status=500)
