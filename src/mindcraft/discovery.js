import net from 'net';
import os from 'os';

function checkPort(ip, port, timeout = 300) {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(timeout);
        socket.once('connect', () => { socket.destroy(); resolve(true); });
        socket.once('timeout', () => { socket.destroy(); resolve(false); });
        socket.once('error', () => { resolve(false); });
        socket.connect(port, ip);
    });
}

// Scans the local /24 subnet for a host with an open port that responds
// like an LM Studio server (serves /v1/models). Requires the container to
// run with host networking so it can see the real LAN.
export async function findLMStudio(port = 1234) {
    const nets = os.networkInterfaces();
    let subnet = null;
    for (const iface of Object.values(nets).flat()) {
        if (iface.family === 'IPv4' && !iface.internal) {
            subnet = iface.address.split('.').slice(0, 3).join('.');
            break;
        }
    }
    if (!subnet) {
        console.error('[discovery] Could not determine local subnet');
        return null;
    }

    console.log(`[discovery] Scanning ${subnet}.0/24 for LM Studio on port ${port}...`);
    const candidates = Array.from({ length: 254 }, (_, i) => `${subnet}.${i + 1}`);
    const CONCURRENCY = 40;
    for (let i = 0; i < candidates.length; i += CONCURRENCY) {
        const batch = candidates.slice(i, i + CONCURRENCY);
        const results = await Promise.all(batch.map(ip => checkPort(ip, port)));
        for (let j = 0; j < batch.length; j++) {
            if (!results[j]) continue;
            const ip = batch[j];
            try {
                const res = await fetch(`http://${ip}:${port}/v1/models`, { signal: AbortSignal.timeout(500) });
                if (res.ok) {
                    console.log(`[discovery] Found LM Studio at ${ip}:${port}`);
                    return `http://${ip}:${port}/v1`;
                }
            } catch { /* not it, keep scanning */ }
        }
    }
    console.error('[discovery] No LM Studio instance found on the LAN');
    return null;
}
