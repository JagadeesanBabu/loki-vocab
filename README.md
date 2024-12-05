# loki-vocab
This is to improve loki vocabulary

## Performance Optimizations

### Database Optimization
- Optimized database queries in `database/models.py` to reduce latency.
- Added indexes to `WordCount` model for `updated_at` and `updated_by` columns.

### Caching
- Implemented caching for frequently accessed data in `services/vocab_service.py` using Flask-Caching.
- Cached the result of `get_summary` method to reduce repeated calculations.

### Asynchronous Tasks
- Used asynchronous tasks for API calls in `services/openai_service.py`.
- Implemented Celery for asynchronous task management.

### Flask App Configuration
- Optimized Flask app configuration in `app.py` for better performance.

## Setup Instructions

### Setting up Flask-Caching
1. Install Flask-Caching:
   ```bash
   pip install Flask-Caching
   ```
2. Configure Flask-Caching in your `app.py`:
   ```python
   from flask_caching import Cache

   app = Flask(__name__)
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

### Setting up Celery
1. Install Celery:
   ```bash
   pip install celery
   ```
2. Configure Celery in your `app.py`:
   ```python
   from celery import Celery

   app = Flask(__name__)
   celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
   celery.conf.update(app.config)
   ```

3. Define your Celery tasks in `services/openai_service.py`:
   ```python
   from celery import Celery

   celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

   @celery.task
   def fetch_definition(word):
       # Your code here

   @celery.task
   def fetch_incorrect_options(word, correct_definition, num_options=3):
       # Your code here
   ```
