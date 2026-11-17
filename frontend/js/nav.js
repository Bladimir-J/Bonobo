// Navbar comun a todas las paginas. Se inyecta en el placeholder.
// El parametro base es '' desde index.html y '../' desde pages/.

function renderNav(base = '') {
    const usuario = auth.getUsuario();
    const logueado = auth.estaLogueado();

    // todo lo que viene del user lo escapamos antes de meterlo en HTML
    const usernameSafe = escapeHTML(usuario?.username || 'Perfil');
    const avatarSafe = escapeHTML(usuario?.avatar_url || '');

    const authHTML = logueado ? `
        <div class="nav-user-info">
            <a href="${base}pages/perfil.html" class="nav-username">
                ${usuario?.avatar_url
                    ? `<img src="${avatarSafe}" alt="" class="nav-avatar">`
                    : `<div class="nav-avatar nav-avatar--placeholder"></div>`
                }
                <span class="nav-username-text">${usernameSafe}</span>
            </a>
            <button class="nav-btn nav-btn--ghost nav-btn--logout" id="btnLogout">Salir</button>
        </div>
    ` : `
        <div class="nav-auth">
            <a href="${base}pages/login.html" class="nav-btn nav-btn--ghost">Entrar</a>
            <a href="${base}pages/registro.html" class="nav-btn nav-btn--primary nav-btn--registro">Registrarse</a>
        </div>
    `;

    // links para el menu movil
    const mobileLinksHTML = logueado ? `
        <a href="${base}pages/diario.html"      class="nav-mobile-link">Diario</a>
        <a href="${base}pages/watchlist.html"   class="nav-mobile-link">Watchlist</a>
        <a href="${base}pages/listas.html"      class="nav-mobile-link">Listas</a>
        <a href="${base}pages/logros.html"      class="nav-mobile-link">Logros</a>
        <a href="${base}pages/actividad.html"   class="nav-mobile-link">Actividad</a>
        <button class="nav-mobile-link nav-mobile-link--salir" id="btnLogoutMobile">Salir</button>
    ` : `
        <a href="${base}pages/registro.html" class="nav-mobile-link">Registrarse</a>
    `;

    const navHTML = `
        <nav class="navbar">
            <div class="nav-inner">
                <a href="${base}index.html" class="nav-logo" aria-label="Bonobo, inicio">B<span class="nav-logo__o">o</span>N<span class="nav-logo__o">o</span>B<span class="nav-logo__o">o</span></a>

                <div class="nav-search-wrap">
                    <svg class="nav-search-icon" viewBox="0 0 20 20" fill="none">
                        <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input
                        type="text"
                        id="navSearch"
                        class="nav-search"
                        placeholder="Buscar película o @usuario…"
                        autocomplete="off"
                    />
                    <div id="navDropdown" class="nav-dropdown" style="display:none"></div>
                </div>

                ${logueado ? `
                <div class="nav-links">
                    <a href="${base}pages/diario.html"      class="nav-link">Diario</a>
                    <a href="${base}pages/watchlist.html"   class="nav-link">Watchlist</a>
                    <a href="${base}pages/listas.html"      class="nav-link">Listas</a>
                    <a href="${base}pages/logros.html"      class="nav-link">Logros</a>
                    <a href="${base}pages/actividad.html"   class="nav-link">Actividad</a>
                </div>
                ` : ''}

                ${authHTML}

                <button class="nav-hamburger" id="navHamburger" aria-label="Menu">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="6" x2="21" y2="6"/>
                        <line x1="3" y1="12" x2="21" y2="12"/>
                        <line x1="3" y1="18" x2="21" y2="18"/>
                    </svg>
                </button>
            </div>

            <div class="nav-mobile-menu" id="navMobileMenu">
                <input type="text" class="nav-mobile-search" id="navSearchMobile"
                       placeholder="Buscar película o @usuario…" autocomplete="off" />
                <div class="nav-mobile-links">
                    ${mobileLinksHTML}
                </div>
            </div>
        </nav>
    `;

    const placeholder = document.getElementById('nav-placeholder');
    if (placeholder) placeholder.innerHTML = navHTML;

    const searchInput = document.getElementById('navSearch');
    const dropdown = document.getElementById('navDropdown');

    if (searchInput && dropdown) {
        let navTimer = null;

        const cerrarDropdown = () => {
            dropdown.style.display = 'none';
            dropdown.innerHTML = '';
        };

        // sugerencias mientras escribe (debounce 300ms)
        searchInput.addEventListener('input', () => {
            clearTimeout(navTimer);
            const q = searchInput.value.trim();
            if (!q) { cerrarDropdown(); return; }

            navTimer = setTimeout(async () => {
                try {
                    let items = [];
                    if (q.startsWith('@')) {
                        const usuarios = await api.usuarios.buscar(q.slice(1), 0, 6);
                        items = usuarios.map(u => ({
                            img: u.avatar_url || '',
                            titulo: u.username,
                            sub: u.bio ? u.bio.slice(0, 40) : '',
                            href: `${base}pages/usuario.html?id=${u.id}`,
                            esAvatar: true,
                        }));
                    } else {
                        const data = await api.peliculas.buscar(q, 0, 6);
                        items = (data.results || []).map(p => ({
                            img: p.poster_url || '',
                            titulo: p.titulo,
                            sub: p.anio_estreno ? String(p.anio_estreno) : '',
                            href: `${base}pages/pelicula.html?id=${p.tmdb_id}`,
                        }));
                    }

                    if (!items.length) { cerrarDropdown(); return; }

                    // OJO: titulo y sub vienen del usuario (bios), hay que escaparlos
                    // el href lo construyo yo asi que no hace falta
                    dropdown.innerHTML = items.map(it => {
                        const tituloSafe = escapeHTML(it.titulo);
                        const subSafe = escapeHTML(it.sub);
                        const imgSafe = escapeHTML(it.img);
                        return `
                        <div class="nav-dropdown-item" onclick="location.href='${it.href}'">
                            ${it.img
                                ? `<img src="${imgSafe}" alt="" ${it.esAvatar ? 'style="height:28px;border-radius:50%"' : ''}>`
                                : `<div style="width:28px;height:42px;background:var(--surface3);border-radius:2px;flex-shrink:0"></div>`
                            }
                            <div class="nav-dropdown-item__info">
                                <div class="nav-dropdown-item__title">${tituloSafe}</div>
                                ${it.sub ? `<div class="nav-dropdown-item__sub">${subSafe}</div>` : ''}
                            </div>
                        </div>
                    `;
                    }).join('');
                    dropdown.style.display = 'block';
                } catch (err) {
                    console.warn('[nav] error en sugerencias', err);
                    cerrarDropdown();
                }
            }, 300);
        });

        // Enter -> pagina de resultados completa
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') { cerrarDropdown(); return; }
            if (e.key !== 'Enter') return;
            const q = searchInput.value.trim();
            if (!q) return;
            cerrarDropdown();
            if (q.startsWith('@')) {
                window.location.href = `${base}pages/buscar.html?q=${encodeURIComponent(q.slice(1).trim())}`;
            } else {
                sessionStorage.setItem('nav_search', q);
                window.location.href = `${base}index.html`;
            }
        });

        // clic fuera -> cerramos
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                cerrarDropdown();
            }
        });
    }

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            auth.logout();
            window.location.href = `${base}index.html`;
        });
    }

    const btnLogoutMobile = document.getElementById('btnLogoutMobile');
    if (btnLogoutMobile) {
        btnLogoutMobile.addEventListener('click', () => {
            auth.logout();
            window.location.href = `${base}index.html`;
        });
    }

    // hamburger: abre/cierra el menu movil
    const hamburger = document.getElementById('navHamburger');
    const mobileMenu = document.getElementById('navMobileMenu');
    if (hamburger && mobileMenu) {
        hamburger.addEventListener('click', (e) => {
            e.stopPropagation();
            mobileMenu.classList.toggle('nav-mobile-menu--open');
        });
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !hamburger.contains(e.target)) {
                mobileMenu.classList.remove('nav-mobile-menu--open');
            }
        });
    }

    // busqueda desde el menu movil (solo redirige, sin sugerencias)
    const searchMobile = document.getElementById('navSearchMobile');
    if (searchMobile) {
        searchMobile.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter') return;
            const q = searchMobile.value.trim();
            if (!q) return;
            if (mobileMenu) mobileMenu.classList.remove('nav-mobile-menu--open');
            if (q.startsWith('@')) {
                window.location.href = `${base}pages/buscar.html?q=${encodeURIComponent(q.slice(1).trim())}`;
            } else {
                sessionStorage.setItem('nav_search', q);
                window.location.href = `${base}index.html`;
            }
        });
    }

    // marca el link activo segun la URL
    const path = window.location.pathname;
    document.querySelectorAll('.nav-link, .nav-mobile-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && path.includes(href.split('/').pop())) {
            link.classList.add('nav-link--active');
        }
    });
}


// App instalable (PWA): registramos el service worker una vez por pagina.
// Esta en la raiz de la web (sw.js), asi controla todas las paginas.
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        const raiz = location.pathname.includes('/pages/') ? '../' : './';
        navigator.serviceWorker.register(raiz + 'sw.js').catch((err) => {
            console.warn('[pwa] no se pudo registrar el service worker', err);
        });
    });
}
