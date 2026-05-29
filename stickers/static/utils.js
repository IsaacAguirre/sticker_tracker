/**
 * Shared utilities for the Sticker Tracker
 */

const FLAG_MAPPING = {
    MEX: 'mx', KOR: 'kr', RSA: 'za', CZE: 'cz', CAN: 'ca', BIH: 'ba', QAT: 'qa', SUI: 'ch', BRA: 'br', MAR: 'ma', 
    HAI: 'ht', SCO: 'gb-sct', USA: 'us', PAR: 'py', AUS: 'au', TUR: 'tr', GER: 'de', CUW: 'cw', CIV: 'ci', 
    ECU: 'ec', NED: 'nl', JPN: 'jp', SWE: 'se', TUN: 'tn', BEL: 'be', EGY: 'eg', IRN: 'ir', NZL: 'nz', 
    ESP: 'es', CPV: 'cv', KSA: 'sa', URU: 'uy', FRA: 'fr', SEN: 'sn', IRQ: 'iq', NOR: 'no', ARG: 'ar', 
    ALG: 'dz', AUT: 'at', JOR: 'jo', POR: 'pt', COD: 'cd', UZB: 'uz', COL: 'co', ENG: 'gb-eng', CRO: 'hr', 
    GHA: 'gh', PAN: 'pa'
};

window.getFlagUrl = function(code) {
    const iso = FLAG_MAPPING[code.toUpperCase()];
    return iso ? `https://flagcdn.com/w40/${iso}.png` : null;
};

window.apiFetch = async function(path, options = {}) {
    const response = await fetch(path, options);
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) throw new Error(data.detail || data || response.statusText);
    return data;
};