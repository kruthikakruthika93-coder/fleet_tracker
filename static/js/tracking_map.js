(function () {
    const mapEl = document.getElementById('map');
    if (!mapEl || typeof L === 'undefined') return;

    const url = mapEl.dataset.url;
    const rowsEl = document.getElementById('loc-rows');

    const map = L.map('map').setView([20.5937, 78.9629], 5);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        referrerPolicy: 'strict-origin-when-cross-origin',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    const COLORS = { ACTIVE: '#10b981', OUTDATED: '#f59e0b', OFFLINE: '#94a3b8' };
    const LABELS = { ACTIVE: 'Active', OUTDATED: 'Outdated', OFFLINE: 'Offline' };
    const BADGES = { ACTIVE: 'success', OUTDATED: 'warning', OFFLINE: 'secondary' };

    const markers = {};
    let fitted = false;

    function popupFor(d) {
        const box = document.createElement('div');
        const title = document.createElement('strong');
        title.textContent = d.driver;
        box.appendChild(title);
        const lines = [
            ['Vehicle', d.vehicle],
            ['Latitude', d.latitude.toFixed(6)],
            ['Longitude', d.longitude.toFixed(6)],
            ['Updated', d.updated_at],
            ['Status', LABELS[d.status]]
        ];
        if (d.accuracy !== null) lines.splice(3, 0, ['Accuracy', Math.round(d.accuracy) + ' m']);
        lines.forEach(function (pair) {
            const line = document.createElement('div');
            line.textContent = pair[0] + ': ' + pair[1];
            box.appendChild(line);
        });
        return box;
    }

    function cell(text) {
        const td = document.createElement('td');
        td.textContent = text;
        return td;
    }

    function render(drivers) {
        const seen = {};
        const points = [];

        drivers.forEach(function (d) {
            seen[d.username] = true;
            const latlng = [d.latitude, d.longitude];
            points.push(latlng);
            const style = {
                radius: 11, color: '#ffffff', weight: 2,
                fillColor: COLORS[d.status], fillOpacity: 1
            };
            if (markers[d.username]) {
                markers[d.username].setLatLng(latlng).setStyle(style).setPopupContent(popupFor(d));
            } else {
                markers[d.username] = L.circleMarker(latlng, style).addTo(map).bindPopup(popupFor(d));
            }
        });

        Object.keys(markers).forEach(function (username) {
            if (!seen[username]) {
                map.removeLayer(markers[username]);
                delete markers[username];
            }
        });

        if (!fitted && points.length) {
            map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 14 });
            fitted = true;
        }

        rowsEl.replaceChildren();
        if (!drivers.length) {
            const tr = document.createElement('tr');
            const td = cell('No driver is sharing a location yet.');
            td.colSpan = 6;
            td.className = 'text-center text-muted py-4';
            tr.appendChild(td);
            rowsEl.appendChild(tr);
            return;
        }

        drivers.forEach(function (d) {
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.appendChild(cell(d.driver));
            tr.appendChild(cell(d.vehicle));
            tr.appendChild(cell(d.latitude.toFixed(6)));
            tr.appendChild(cell(d.longitude.toFixed(6)));
            tr.appendChild(cell(d.updated_at));
            const statusTd = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = 'badge text-bg-' + BADGES[d.status];
            badge.textContent = LABELS[d.status];
            statusTd.appendChild(badge);
            tr.appendChild(statusTd);
            tr.addEventListener('click', function () {
                map.setView([d.latitude, d.longitude], 15);
                if (markers[d.username]) markers[d.username].openPopup();
            });
            rowsEl.appendChild(tr);
        });
    }

    function load() {
        fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
            .then(function (response) {
                if (!response.ok) throw new Error('Request failed');
                return response.json();
            })
            .then(function (data) { render(data.drivers); })
            .catch(function () {
                rowsEl.replaceChildren();
                const tr = document.createElement('tr');
                const td = cell('Could not load locations. Retrying...');
                td.colSpan = 6;
                td.className = 'text-center text-danger py-4';
                tr.appendChild(td);
                rowsEl.appendChild(tr);
            });
    }

    load();
    setInterval(load, 10000);
})();