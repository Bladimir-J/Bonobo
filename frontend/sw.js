// Service worker de Bonobo.
// Lo necesita el movil para ofrecer "Instalar app". No guarda nada en cache:
// la app siempre carga la version mas reciente de la web y de la API.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {
    // sin respondWith: el navegador hace la peticion normal
});
