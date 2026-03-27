"""
Model artifact caching — store/load trained models keyed by filter hash.
"""

import os
import hashlib
import pickle
import time

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "models")
os.makedirs(CACHE_DIR, exist_ok=True)

TTL_SECONDS = 24 * 3600  # 24 hours


def _hash_key(model_type, params_dict):
    raw = f"{model_type}:{sorted(params_dict.items())}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def save_model(model_type, params_dict, model_obj):
    key = _hash_key(model_type, params_dict)
    path = os.path.join(CACHE_DIR, f"{model_type}_{key}.pkl")
    with open(path, "wb") as f:
        pickle.dump({"model": model_obj, "timestamp": time.time(), "params": params_dict}, f)
    return path


def load_model(model_type, params_dict):
    key = _hash_key(model_type, params_dict)
    path = os.path.join(CACHE_DIR, f"{model_type}_{key}.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = pickle.load(f)
    if time.time() - data["timestamp"] > TTL_SECONDS:
        os.remove(path)
        return None
    return data["model"]


def list_cached():
    items = []
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".pkl"):
            path = os.path.join(CACHE_DIR, fname)
            size_kb = os.path.getsize(path) / 1024
            items.append({"file": fname, "size_kb": round(size_kb, 1), "path": path})
    return items


def clear_cache():
    count = 0
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".pkl"):
            os.remove(os.path.join(CACHE_DIR, fname))
            count += 1
    return count
