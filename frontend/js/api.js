// Capa central para hablar con el backend.
// En localhost vamos al backend local, fuera al de produccion
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://bonobo-backend-bladimir.onrender.com';

// Escapa texto del usuario antes de meterlo con innerHTML (anti-XSS)
function escapeHTML(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}


function _headers(esJSON = true) {
    const token = localStorage.getItem('bonobo_token');
    const h = {};
    if (esJSON) h['Content-Type'] = 'application/json; charset=UTF-8'
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
}

async function _req(method, endpoint, body = null) {
    const opts = { method, headers: _headers() };
    if (body !== null) opts.body = JSON.stringify(body);

    let res;
    try {
        res = await fetch(`${API_BASE}${endpoint}`, opts);
    } catch (err) {
        // sin red o servidor caido
        throw new Error('No hay conexión con el servidor');
    }

    if (res.status === 204) return null;

    let data;
    try {
        data = await res.json();
    } catch (e) {
        data = { detail: 'Error ' + res.status };
    }

    if (res.status === 401 && localStorage.getItem('bonobo_token')) {
        // token caducado -> fuera sesion
        localStorage.removeItem('bonobo_token');
        localStorage.removeItem('bonobo_user');
        const inPages = window.location.pathname.includes('/pages/');
        window.location.href = inPages ? 'login.html' : 'pages/login.html';
        return null;
    }

    if (!res.ok) throw new Error(data.detail || ('Error ' + res.status));
    return data;
}

const api = {

    auth: {
        registro: (body) => _req('POST', '/api/auth/registro', body),

        // login va con form-urlencoded porque OAuth2 de FastAPI lo pide asi
        login: async (email, password) => {
            const form = new URLSearchParams();
            form.append('username', email);
            form.append('password', password);

            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                body: form
            });

            const data = await res.json().catch(() => ({ detail: 'Error al conectar' }));
            if (!res.ok) throw new Error(data.detail || 'Credenciales incorrectas');
            return data;
        }
    },

    peliculas: {
        buscar: (q, skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),
        cartelera: (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/cartelera?skip=${skip}&limit=${limit}`),
        estrenos: (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/estrenos?skip=${skip}&limit=${limit}`),
        detalle: (tmdbId) => _req('GET', `/api/peliculas/${tmdbId}`),
        persona: (personId) => _req('GET', `/api/peliculas/persona/${personId}`),
    },

    acciones: {
        marcarVista: (tmdbId) => _req('POST', `/api/peliculas/${tmdbId}/vista`),
        desmarcarVista: (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/vista`),

        puntuar: (tmdbId, puntuacion) => _req('PUT', `/api/peliculas/${tmdbId}/puntuacion`, { puntuacion }),
        eliminarPuntuacion: (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/puntuacion`),

        darMeGusta: (tmdbId) => _req('POST', `/api/peliculas/${tmdbId}/me-gusta`),
        quitarMeGusta: (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/me-gusta`),

        añadirWatchlist: (tmdbId) => _req('POST', `/api/peliculas/${tmdbId}/watchlist`),
        quitarWatchlist: (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/watchlist`),

        crearDiario: (tmdbId, body) => _req('POST', `/api/peliculas/${tmdbId}/diario`, body),
        editarDiario: (idEntrada, body) => _req('PUT', `/api/diario/${idEntrada}`, body),
        borrarDiario: (idEntrada) => _req('DELETE', `/api/diario/${idEntrada}`),
    },

    usuarios: {
        mePerfil: () => _req('GET', '/api/usuarios/me'),
        editarPerfil: (body) => _req('PUT', '/api/usuarios/me', body),
        configurarFavoritas: (tmdbIds) => _req('PUT', '/api/usuarios/me/favoritas', tmdbIds),

        cambiarPassword: (password_actual, password_nueva) =>
            _req('PUT', '/api/usuarios/me/password', { password_actual, password_nueva }),

        buscar: (q, skip = 0, limit = 20) =>
            _req('GET', `/api/usuarios/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),

        perfil: (id) => _req('GET', `/api/usuarios/${id}`),
        vistas: (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/vistas?skip=${skip}&limit=${limit}`),
        diario: (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/diario?skip=${skip}&limit=${limit}`),
        diarioPelicula: (id, tmdbId) => _req('GET', `/api/usuarios/${id}/diario/pelicula/${tmdbId}`),
        watchlist: (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/watchlist?skip=${skip}&limit=${limit}`),
        favoritas: (id) => _req('GET', `/api/usuarios/${id}/favoritas`),
        listas: (id) => _req('GET', `/api/usuarios/${id}/listas`),

        feed: (skip = 0, limit = 20) => _req('GET', `/api/usuarios/me/feed?skip=${skip}&limit=${limit}`),
        rankingAmigos: () => _req('GET', '/api/usuarios/me/ranking-amigos'),
    },

    social: {
        seguir: (id) => _req('POST', `/api/usuarios/${id}/seguir`),
        dejarDeSeguir: (id) => _req('DELETE', `/api/usuarios/${id}/seguir`),
        seguidores: (id, skip = 0, limit = 50) =>
            _req('GET', `/api/usuarios/${id}/seguidores?skip=${skip}&limit=${limit}`),
        seguidos: (id, skip = 0, limit = 50) =>
            _req('GET', `/api/usuarios/${id}/seguidos?skip=${skip}&limit=${limit}`),
    },

    resenas: {
        amigos: (tmdbId) => _req('GET', `/api/peliculas/${tmdbId}/resenas/amigos`),
        comunidad: (tmdbId, skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/${tmdbId}/resenas?skip=${skip}&limit=${limit}`),
        darLike: (idEntrada) => _req('POST', `/api/diario/${idEntrada}/like`),
        quitarLike: (idEntrada) => _req('DELETE', `/api/diario/${idEntrada}/like`),
        comentarios: (idEntrada) => _req('GET', `/api/diario/${idEntrada}/comentarios`),
        crearComentario: (idEntrada, texto) =>
            _req('POST', `/api/diario/${idEntrada}/comentarios`, { texto }),
        borrarComentario: (idComentario) => _req('DELETE', `/api/comentarios/${idComentario}`),
    },

    listas: {
        crear: (body) => _req('POST', '/api/listas', body),
        detalle: (id) => _req('GET', `/api/listas/${id}`),
        editar: (id, body) => _req('PUT', `/api/listas/${id}`, body),
        borrar: (id) => _req('DELETE', `/api/listas/${id}`),
        añadirPelicula: (idLista, tmdbId) => _req('POST', `/api/listas/${idLista}/peliculas/${tmdbId}`),
        quitarPelicula: (idLista, tmdbId) => _req('DELETE', `/api/listas/${idLista}/peliculas/${tmdbId}`),
        listasConPelicula: (tmdbId) => _req('GET', `/api/listas/mis-listas-con-pelicula/${tmdbId}`),

        colaborando: () => _req('GET', '/api/listas/colaborando'),
        colaboradores: (idLista) => _req('GET', `/api/listas/${idLista}/colaboradores`),
        añadirColaborador: (idLista, idUsuario) => _req('POST', `/api/listas/${idLista}/colaboradores/${idUsuario}`),
        quitarColaborador: (idLista, idUsuario) => _req('DELETE', `/api/listas/${idLista}/colaboradores/${idUsuario}`),
    },

    logros: {
        todos: () => _req('GET', '/api/logros/todos'),
        misLogros: () => _req('GET', '/api/logros/mis-logros'),
        reclamar: (idUsuarioLogro) => _req('POST', `/api/logros/${idUsuarioLogro}/reclamar`),
    },
};
