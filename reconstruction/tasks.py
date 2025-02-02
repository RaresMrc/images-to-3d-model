import os
import cv2
import numpy as np
import subprocess
from celery import shared_task
from django.conf import settings
from .models import ReconstructionJob, InputImage
from django.db import transaction
import json
import shutil
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def process_images(job_id):
    """
    Main task that orchestrates the entire reconstruction pipeline.
    """
    try:
        job = ReconstructionJob.objects.get(id=job_id)

        # Set up directories
        work_dir = os.path.join(settings.MEDIA_ROOT, f'reconstruction_{job_id}')
        colmap_dir = os.path.join(work_dir, 'colmap')
        database_path = os.path.join(colmap_dir, 'database.db')
        image_dir = os.path.join(colmap_dir, 'images')
        sparse_dir = os.path.join(colmap_dir, 'sparse')
        dense_dir = os.path.join(colmap_dir, 'dense')

        os.makedirs(colmap_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)

        images = InputImage.objects.filter(job=job)
        for img_obj in images:
            src_path = os.path.join(settings.MEDIA_ROOT, str(img_obj.image))
            dst_path = os.path.join(image_dir, os.path.basename(img_obj.image.name))
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)

        run_colmap_pipeline(
            colmap_dir=colmap_dir,
            database_path=database_path,
            image_dir=image_dir,
            sparse_dir=sparse_dir,
            dense_dir=dense_dir
        )

        return {
            'status': 'success',
            'job_id': job_id,
            'message': '3D reconstruction completed successfully'
        }

    except Exception as e:
        return {
            'status': 'error',
            'job_id': job_id,
            'message': str(e)
        }


def run_colmap_pipeline(colmap_dir, database_path, image_dir, sparse_dir, dense_dir):
    try:
        # Create all directories if they don't exist
        for dir_path in [sparse_dir, dense_dir]:
            os.makedirs(dir_path, exist_ok=True)

        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['CUDA_VISIBLE_DEVICES'] = '0'

        logger.info("Starting feature extraction with GPU acceleration...")
        # Feature extraction using GPU
        subprocess.run([
            'colmap', 'feature_extractor',
            '--database_path', database_path,
            '--image_path', image_dir,
            '--ImageReader.single_camera', '1',
            '--SiftExtraction.use_gpu', '1',  # Enable GPU
            '--SiftExtraction.gpu_index', '0',  # Use first GPU
            '--SiftExtraction.max_num_features', '16384',  # Can use more features with GPU
            '--SiftExtraction.first_octave', '0'
        ], check=True, env=env)

        logger.info("Starting feature matching with GPU acceleration...")
        subprocess.run([
            'colmap', 'exhaustive_matcher',
            '--database_path', database_path,
            '--SiftMatching.use_gpu', '1',
            '--SiftMatching.gpu_index', '0',
            '--SiftMatching.guided_matching', '1'
        ], check=True, env=env)

        logger.info("Starting sparse reconstruction...")
        subprocess.run([
            'colmap', 'mapper',
            '--database_path', database_path,
            '--image_path', image_dir,
            '--output_path', sparse_dir,
            '--Mapper.num_threads', '8',
            '--Mapper.init_min_tri_angle', '4',
            '--Mapper.multiple_models', '0',
            '--Mapper.extract_colors', '1'
        ], check=True, env=env)

        logger.info("Converting sparse model to PLY format...")
        sparse_model_dir = os.path.join(sparse_dir, '0')
        if not os.path.exists(sparse_model_dir):
            raise Exception("Sparse reconstruction failed to produce output")

        subprocess.run([
            'colmap', 'model_converter',
            '--input_path', sparse_model_dir,
            '--output_path', os.path.join(sparse_dir, 'sparse.ply'),
            '--output_type', 'PLY'
        ], check=True, env=env)

        logger.info("Starting dense reconstruction...")
        subprocess.run([
            'colmap', 'image_undistorter',
            '--image_path', image_dir,
            '--input_path', sparse_model_dir,
            '--output_path', dense_dir,
            '--max_image_size', '3200'  # Can use larger images with GPU
        ], check=True, env=env)

        logger.info("Running patch match stereo with GPU acceleration...")
        subprocess.run([
            'colmap', 'patch_match_stereo',
            '--workspace_path', dense_dir,
            '--PatchMatchStereo.max_image_size', '2000',
            '--PatchMatchStereo.window_radius', '7',
            '--PatchMatchStereo.window_step', '2',
            '--PatchMatchStereo.num_samples', '20',
            '--PatchMatchStereo.num_iterations', '8'
        ], check=True, env=env)

        logger.info("Performing stereo fusion...")
        subprocess.run([
            'colmap', 'stereo_fusion',
            '--workspace_path', dense_dir,
            '--output_path', os.path.join(dense_dir, 'fused.ply'),
            '--input_type', 'geometric'
        ], check=True, env=env)

        logger.info("Generating mesh from point cloud...")
        subprocess.run([
            'colmap', 'poisson_mesher',
            '--input_path', os.path.join(dense_dir, 'fused.ply'),
            '--output_path', os.path.join(dense_dir, 'meshed.ply')
        ], check=True, env=env)

        return True

    except subprocess.CalledProcessError as e:
        error_msg = f"COLMAP pipeline failed at step: {e.cmd}\n"
        if hasattr(e, 'output'):
            error_msg += f"Error output: {e.output}"
        logger.info(error_msg)
        raise Exception(error_msg)