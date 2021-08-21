window.onload = function () {
    if (typeof WidevineCrypto !== 'undefined') {
        $('#status').css('color', 'green').text('widevine-l3-guesser is installed.');
    } else {
        $('#status').css('color', 'red').text('widevine-l3-guesser is NOT installed. The API will not work.');
    }
};

(async function () {
    function base64ToBuffer(data) {
        return Uint8Array.from(atob(data), x => x.charCodeAt(0));
    }

    let sessions = {};

    let keySystemAccess = await navigator.requestMediaKeySystemAccess('com.widevine.alpha', [{
        'initDataTypes': ['cenc'],
        'audioCapabilities': [{
            'contentType': 'audio/mp4;codecs="mp4a.40.2"',
        }],
        'videoCapabilities': [{
            'contentType': 'video/mp4;codecs="avc1.42E01E"',
        }],
    }]);

    let socket = io();

    console.log('Socket initialized');

    socket.on('GetChallenge', async function(req, cb) {
        console.log('GetChallenge called with params: %o', req);

        let mediaKeys = await keySystemAccess.createMediaKeys();
        await mediaKeys.setServerCertificate(
            DeviceCertificate.read(new Pbf(base64ToBuffer(req.params.cert))).serial_number
        );

        let session = mediaKeys.createSession('temporary');
        session.generateRequest('cenc', base64ToBuffer(req.params.init));

        session.addEventListener('message', async function (event) {
            if (event.messageType == 'license-request') {
                socket.emit('SetChallenge', {
                    session_id: req.params.session_id,
                    challenge: event.message,
                });
                sessions[req.params.session_id] = event.message;
                await session.close();
            }
        })
    });

    socket.on('GetKeys', async function (req, cb) {
        console.log('GetKeys called with params: %o', req);

        let data = {
            licenseRequest: sessions[req.params.session_id],
            licenseResponse: base64ToBuffer(req.params.cdmkeyresponse),
            keys: new Map(),
        };

        await WidevineCrypto.decryptContentKey(null, data);

        let keys = [];
        for (let [kid, key] of data.keys) {
            keys.push({
                kid: kid,
                key: key,
            });
        }

        console.log('Keys: %o', keys);

        socket.emit('SetKeys', {
            session_id: req.params.session_id,
            keys: keys,
        });
    });
})();
