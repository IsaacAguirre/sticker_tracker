const content = document.getElementById('report-content');
const status = document.getElementById('status-message');
const btnDups = document.getElementById('btn-duplicates');
const btnMissing = document.getElementById('btn-missing');
const btnPars = document.getElementById('btn-parallels');

let lastDuplicatesData = null;
let lastMissingData = null;

function showStatus(msg, type='success') {
    status.textContent = msg;
    status.className = `status ${type}`;
}

async function loadDuplicates() {
    btnDups.classList.add('active');
    btnMissing?.classList.remove('active');
    btnPars.classList.remove('active');
    content.innerHTML = '<p>Generating duplicates report...</p>';
    
    try {
        const data = await apiFetch('/reports/duplicates');
        lastDuplicatesData = data;
        if (data.length === 0) {
            content.innerHTML = '<p>No duplicate stickers found in any inventory.</p>';
            return;
        }

        let html = '<div class="report-actions" style="margin-bottom: 20px;"><button class="btn-secondary" onclick="exportDuplicates()">Export CSV</button></div>';
        data.forEach(group => {
            html += `<div class="group-header"><h2>${group.group}</h2></div>`;
            group.entries.forEach(entry => {
                const dups = Object.entries(entry.duplicates)
                    .map(([id, count]) => `<span class="sticker-item">${id} <strong>(x${count})</strong></span>`)
                    .join('');
                const flagUrl = getFlagUrl(entry.code);
                const flagHtml = flagUrl ? `<img src="${flagUrl}" class="flag-icon" alt="">` : '';
                html += `
                    <div class="country-entry">
                        <strong>${flagHtml}${entry.code}</strong>
                        <div class="sticker-list">${dups}</div>
                    </div>
                `;
            });
        });
        content.innerHTML = html;
        showStatus('Duplicates report updated.');
    } catch (e) {
        showStatus(e.message, 'error');
    }
}

async function loadMissing() {
    btnMissing?.classList.add('active');
    btnDups.classList.remove('active');
    btnPars.classList.remove('active');
    content.innerHTML = '<p>Generating missing stickers report...</p>';
    
    try {
        const data = await apiFetch('/reports/missing');
        lastMissingData = data;
        if (data.length === 0) {
            content.innerHTML = '<p>No missing stickers found in any inventory.</p>';
            return;
        }

        let html = '<div class="report-actions" style="margin-bottom: 20px;"><button class="btn-secondary" onclick="exportMissing()">Export CSV</button></div>';
        data.forEach(group => {
            html += `<div class="group-header"><h2>${group.group}</h2></div>`;
            group.entries.forEach(entry => {
                const missing = entry.missing
                    .map(id => `<span class="sticker-item">${id}</span>`)
                    .join('');
                const flagUrl = getFlagUrl(entry.code);
                const flagHtml = flagUrl ? `<img src="${flagUrl}" class="flag-icon" alt="">` : '';
                html += `
                    <div class="country-entry">
                        <strong>${flagHtml}${entry.code}</strong>
                        <div class="sticker-list">${missing}</div>
                    </div>
                `;
            });
        });
        content.innerHTML = html;
        showStatus('Missing stickers report updated.');
    } catch (e) {
        showStatus(e.message, 'error');
    }
}

async function loadParallels() {
    btnPars.classList.add('active');
    btnDups.classList.remove('active');
    btnMissing?.classList.remove('active');
    content.innerHTML = '<p>Generating parallels report...</p>';

    try {
        const data = await apiFetch('/reports/parallels');
        if (data.length === 0) {
            content.innerHTML = '<p>No parallel stickers found in any inventory.</p>';
            return;
        }

        let html = '';
        data.forEach(group => {
            html += `<div class="group-header"><h2>${group.group}</h2></div>`;
            group.entries.forEach(entry => {
                const flagUrl = getFlagUrl(entry.code);
                const flagHtml = flagUrl ? `<img src="${flagUrl}" class="flag-icon" alt="">` : '';
                let pList = '';
                Object.entries(entry.parallels).forEach(([sid, types]) => {
                    const typeTags = Object.entries(types)
                        .map(([t, c]) => `<span class="parallel-tag" style="background: ${t}">${t}: ${c}</span>`)
                        .join('');
                    pList += `<div class="sticker-item" style="margin-bottom:6px; display:block;"><strong>${sid}:</strong> ${typeTags}</div>`;
                });
                html += `
                    <div class="country-entry">
                        <strong>${flagHtml}${entry.code}</strong>
                        <div style="margin-top: 8px;">${pList}</div>
                    </div>
                `;
            });
        });
        content.innerHTML = html;
        showStatus('Parallels report updated.');
    } catch (e) {
        showStatus(e.message, 'error');
    }
}

function downloadCSV(filename, rows) {
    const csvContent = rows.map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")
    ).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

window.exportDuplicates = function() {
    if (!lastDuplicatesData) return;
    const rows = [["Group", "Country", "Stickers"]];
    lastDuplicatesData.forEach(group => {
        group.entries.forEach(entry => {
            const stickerList = Object.entries(entry.duplicates)
                .map(([id, count]) => `${id} (x${count})`)
                .join(", ");
            rows.push([group.group, entry.code, stickerList]);
        });
    });
    downloadCSV("duplicates_report.csv", rows);
};

window.exportMissing = function() {
    if (!lastMissingData) return;
    const rows = [["Group", "Country", "Stickers"]];
    lastMissingData.forEach(group => {
        group.entries.forEach(entry => {
            const stickerList = entry.missing.join(", ");
            rows.push([group.group, entry.code, stickerList]);
        });
    });
    downloadCSV("missing_report.csv", rows);
};

btnDups.addEventListener('click', loadDuplicates);
btnMissing?.addEventListener('click', loadMissing);
btnPars.addEventListener('click', loadParallels);