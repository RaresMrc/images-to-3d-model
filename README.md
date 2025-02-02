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
