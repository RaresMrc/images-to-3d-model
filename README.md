# images-to-3d-model

A Django web application that generates 3D models from uploaded images using COLMAP. Users can upload multiple images of an object, and the application processes them to create three different types of 3D outputs:
- Sparse Point Cloud
- Dense Point Cloud
- Textured Mesh

## Features
- Drag-and-drop image upload interface
- Real-time progress tracking
- Support for multiple image formats (JPG, PNG)
- Automatic 3D reconstruction using COLMAP
- Download options for different 3D model formats

## Prerequisites
- Python 3.x
- Django
- Redis (for Celery task queue)
- COLMAP
- CUDA-capable GPU (recommended for better performance)

## Installation
1. Clone the repository
```bash
git clone https://github.com/RaresMrc/images-to-3d-model.git
cd images-to-3d-model
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run migrations
```bash
python3 manage.py migrate
```

4. Start Redis server
```bash
redis-server
```

5. Start Celery worker
```bash
celery -A image_to_model worker -l info
```

6. Run the development server
```bash
python3 manage.py runserver
```

## Usage

Navigate to http://localhost:8000
Upload 20-40 images of your object
Wait for the processing to complete
Download the generated 3D models

## Project Structure

/reconstruction - Main Django app containing the reconstruction logic
/templates - HTML templates
/media - Storage for uploaded images and generated models

## Technologies Used

Django
Celery
Redis
COLMAP
JavaScript (for frontend)
Tailwind CSS

## Important Setup Note
The Django settings.py file is not included in this repository for security reasons. To run this project, you can follow these steps:

1. Create a new settings.py file based on Django's default configuration
2. Configure the following settings:
   - SECRET_KEY
   - DEBUG
   - ALLOWED_HOSTS
   - MEDIA_URL and MEDIA_ROOT for handling uploaded images
   - Celery configuration for processing tasks
   - Redis settings for the task queue
