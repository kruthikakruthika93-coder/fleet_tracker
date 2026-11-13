(function () {
    const card = document.getElementById('share-card');
    if (!card) return;

    const updateUrl = card.dataset.updateUrl;
    const stopUrl = card.dataset.stopUrl;
    const csrf = card.dataset.csrf;
    const startBtn = document.getElementById('share-start');
    const stopBtn = document.getElementById('share-stop');
    const statusEl = document.getElementById('share-status');
    const detailEl = document.getElementById('share-detail');

    const INTERVAL_MS = 15000;
    const FLAG = 'locationSharing';
    let timer = null;

    function setUi(sharing, label, detail) {
        statusEl.textContent = label;
        statusEl.className = 'badge text-bg-' + (sharing ? 'success' : 'secondary');
        startBtn.classList.toggle('d-none', sharing);
        stopBtn.classList.toggle('d-none', !sharing);
        detailEl.textContent = detail || '';
    }

    function post(url, payload) {
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify(payload || {})
        });
    }

    function onPosition(position) {
        if (!timer) return;
        post(updateUrl, {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
        }).then(function (response) {
            if (!timer) return;
            if (response.ok) {
                setUi(true, 'Sharing', 'Last sent at ' + new Date().toLocaleTimeString());
            } else {
                setUi(true, 'Sharing', 'The server rejected the last update. Retrying...');
            }
        }).catch(function () {
            if (timer) setUi(true, 'Sharing', 'No connection. Retrying...');
        });
    }

    function halt() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
        try { sessionStorage.removeItem(FLAG); } catch (e) {}
        return post(stopUrl).catch(function () {});
    }

    function onError(error) {
        if (!timer) return;
        if (error.code === 1) {
            halt();
            setUi(false, 'Not sharing', 'Location permission was denied. Allow location for this site in your browser, then try again.');
        } else {
            setUi(true, 'Sharing', 'Could not read your location. Retrying...');
        }
    }

    function sendPosition() {
        navigator.geolocation.getCurrentPosition(onPosition, onError, {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        });
    }

    function startSharing() {
        if (!('geolocation' in navigator)) {
            setUi(false, 'Not sharing', 'This browser does not support location sharing.');
            return;
        }
        if (timer) return;
        try { sessionStorage.setItem(FLAG, '1'); } catch (e) {}
        setUi(true, 'Starting', 'Waiting for location permission...');
        timer = setInterval(sendPosition, INTERVAL_MS);
        sendPosition();
    }

    function stopSharing() {
        halt().then(function () {
            setUi(false, 'Not sharing', 'Location sharing stopped.');
        });
    }

    startBtn.addEventListener('click', startSharing);
    stopBtn.addEventListener('click', stopSharing);

    try {
        if (sessionStorage.getItem(FLAG) === '1') startSharing();
    } catch (e) {}
})();