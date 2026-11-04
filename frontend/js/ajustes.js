// ajustes.js — pagina de ajustes (perfil + cambio de contraseña)

function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}


// FOTO DE PERFIL
// Se puede elegir de dos formas: subiendo una imagen del dispositivo o
// pegando una URL. La imagen subida se recorta en cuadrado y se reduce a
// 256x256 en el propio navegador (canvas), y se guarda como texto (data URL).
// Asi no hace falta ningun servicio extra para guardar archivos.
const AVATAR_LADO = 256;
const AVATAR_MAX_MB = 10;
let avatarSubido = null;   // data URL de la foto subida (o null si no hay)

function pintarPreviewAvatar(src) {
    const preview = document.getElementById('avatarPreview');
    if (src) {
        preview.style.backgroundImage = `url("${src.replace(/"/g, '%22')}")`;
        preview.textContent = '';
    } else {
        const usuario = auth.getUsuario();
        preview.style.backgroundImage = '';
        preview.textContent = (usuario?.username?.[0] || '?').toUpperCase();
    }
}

// lee el archivo, lo recorta al centro en cuadrado y lo reduce
function imagenADataURL(archivo) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(archivo);
        const img = new Image();
        img.onload = () => {
            const lado = Math.min(img.naturalWidth, img.naturalHeight);
            const sx = (img.naturalWidth - lado) / 2;
            const sy = (img.naturalHeight - lado) / 2;

            const canvas = document.createElement('canvas');
            canvas.width = AVATAR_LADO;
            canvas.height = AVATAR_LADO;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#16161e';   // fondo por si el PNG tiene transparencia
            ctx.fillRect(0, 0, AVATAR_LADO, AVATAR_LADO);
            ctx.drawImage(img, sx, sy, lado, lado, 0, 0, AVATAR_LADO, AVATAR_LADO);

            URL.revokeObjectURL(url);
            resolve(canvas.toDataURL('image/jpeg', 0.85));
        };
        img.onerror = () => {
            URL.revokeObjectURL(url);
            reject(new Error('No se ha podido leer la imagen'));
        };
        img.src = url;
    });
}

async function alElegirArchivo(e) {
    const archivo = e.target.files[0];
    e.target.value = '';   // para poder elegir el mismo archivo otra vez
    if (!archivo) return;

    const errorEl = document.getElementById('errorPerfil');
    errorEl.className = 'form-error';

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(archivo.type)) {
        errorEl.textContent = 'La imagen debe ser JPG, PNG o WEBP.';
        errorEl.className = 'form-error form-error--visible';
        return;
    }
    if (archivo.size > AVATAR_MAX_MB * 1024 * 1024) {
        errorEl.textContent = `La imagen no puede pesar más de ${AVATAR_MAX_MB} MB.`;
        errorEl.className = 'form-error form-error--visible';
        return;
    }

    try {
        avatarSubido = await imagenADataURL(archivo);
        document.getElementById('inputAvatar').value = '';
        pintarPreviewAvatar(avatarSubido);
        document.getElementById('avatarAyuda').textContent = 'Foto lista. Pulsa "Guardar perfil" para guardarla.';
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.className = 'form-error form-error--visible';
    }
}

function alEscribirUrl(e) {
    // si escribe una URL, manda la URL (y olvidamos la foto subida)
    avatarSubido = null;
    pintarPreviewAvatar(e.target.value.trim() || null);
}

function quitarAvatar() {
    avatarSubido = null;
    document.getElementById('inputAvatar').value = '';
    pintarPreviewAvatar(null);
    document.getElementById('avatarAyuda').textContent = 'Pulsa "Guardar perfil" para quitar la foto.';
}


// cambia solo la foto de la barra de arriba (sin volver a pintar toda la barra)
function actualizarAvatarNav(src) {
    const enlace = document.querySelector('.nav-username');
    const actual = enlace?.querySelector('.nav-avatar');
    if (!actual) return;
    let nuevo;
    if (src) {
        nuevo = document.createElement('img');
        nuevo.className = 'nav-avatar';
        nuevo.alt = '';
        nuevo.src = src;
    } else {
        nuevo = document.createElement('div');
        nuevo.className = 'nav-avatar nav-avatar--placeholder';
    }
    actual.replaceWith(nuevo);
}


async function guardarPerfil() {
    // "" (vacio) = quitar la foto; el backend lo guarda tal cual
    const avatar_url = avatarSubido || document.getElementById('inputAvatar').value.trim();
    const bio = document.getElementById('inputBio').value.trim() || null;
    const errorEl = document.getElementById('errorPerfil');

    try {
        await api.usuarios.editarPerfil({ bio, avatar_url });

        // sincronizamos lo guardado en localStorage
        const usuarioGuardado = auth.getUsuario();
        auth.guardarUsuario({ ...usuarioGuardado, bio, avatar_url });
        actualizarAvatarNav(avatar_url);   // que el avatar de arriba cambie al momento

        errorEl.className = 'form-error';
        document.getElementById('avatarAyuda').textContent = 'JPG, PNG o WEBP. Se recorta en cuadrado.';
        mostrarToast('Perfil actualizado ✓');
    } catch (err) {
        console.warn('[ajustes] error guardando perfil', err);
        errorEl.textContent = err.message || 'Error al guardar.';
        errorEl.className = 'form-error form-error--visible';
    }
}


async function guardarPassword() {
    const actual = document.getElementById('inputPasswordActual').value;
    const nueva = document.getElementById('inputPasswordNueva').value;
    const repetir = document.getElementById('inputPasswordRepetir').value;
    const errorEl = document.getElementById('errorPassword');

    if (nueva.length < 8) {
        errorEl.textContent = 'La nueva contraseña debe tener al menos 8 caracteres.';
        errorEl.className = 'form-error form-error--visible';
        return;
    }
    if (nueva !== repetir) {
        errorEl.textContent = 'Las contraseñas no coinciden.';
        errorEl.className = 'form-error form-error--visible';
        return;
    }

    try {
        await api.usuarios.cambiarPassword(actual, nueva);
        document.getElementById('inputPasswordActual').value = '';
        document.getElementById('inputPasswordNueva').value = '';
        document.getElementById('inputPasswordRepetir').value = '';
        errorEl.className = 'form-error';
        mostrarToast('Contraseña actualizada ✓');
    } catch (err) {
        console.warn('[ajustes] error cambiando password', err);
        errorEl.textContent = err.message || 'Error al cambiar la contraseña.';
        errorEl.className = 'form-error form-error--visible';
    }
}


document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');
    actualizarBadgesLogros();

    const inputArchivo = document.getElementById('inputAvatarArchivo');
    document.getElementById('btnSubirAvatar').addEventListener('click', () => inputArchivo.click());
    inputArchivo.addEventListener('change', alElegirArchivo);
    document.getElementById('inputAvatar').addEventListener('input', alEscribirUrl);
    document.getElementById('btnQuitarAvatar').addEventListener('click', quitarAvatar);

    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const usuario = await api.usuarios.mePerfil();
        // si la foto actual es una subida (data URL) no la metemos en la caja
        // de la URL: la guardamos aparte para no perderla al guardar
        if (usuario.avatar_url?.startsWith('data:')) {
            avatarSubido = usuario.avatar_url;
        } else {
            document.getElementById('inputAvatar').value = usuario.avatar_url || '';
        }
        pintarPreviewAvatar(usuario.avatar_url || null);
        document.getElementById('inputBio').value = usuario.bio || '';
    } catch (err) {
        console.warn('[ajustes] error cargando datos', err);
        mostrarToast('Error al cargar los datos', 'error');
    }
});
