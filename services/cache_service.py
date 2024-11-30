from flask_caching import Cache

cache = Cache()

def init_cache(app):
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})

def cache_data(key, data, timeout=300):
    cache.set(key, data, timeout=timeout)

def get_cached_data(key):
    return cache.get(key)

def clear_cache(key):
    cache.delete(key)
