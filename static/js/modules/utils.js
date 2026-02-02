const ASTROSURGE_API_BASE = (window.ASTROSURGE_API_BASE || 'http://localhost:8000/api').replace(/\/$/, '');

function buildApiUrl(path = '') {
    if (!path) return ASTROSURGE_API_BASE;
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${ASTROSURGE_API_BASE}${normalizedPath}`;
}

function apiFetch(path, options = {}) {
    return fetch(buildApiUrl(path), options);
}
