const content = document.getElementById('report-content');
const status = document.getElementById('status-message');
const btnDups = document.getElementById('btn-duplicates');
const btnPars = document.getElementById('btn-parallels');

async function apiFetch(path) {
    const response = await fetch(path);
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || response.statusText);
    }
    return response.json();
}

function showStatus(msg, type='success') {
    status.textContent = msg;
    status.className = `status ${type}`;
}

async function loadDuplicates() {
    btnDups.classList.add('active');
    btnPars.classList.remove('active');
    content.innerHTML = '<p>Generating duplicates report...</p>';
    
    try {
        const data = await apiFetch('/reports/duplicates');
        if (data.length === 0) {
            content.innerHTML = '<p>No duplicate stickers found in any inventory.</p>';
            return;
        }

        let html = '';
        data.forEach(group => {
            html += `<div class="group-header"><h2>${group.group}</h2></div>`;
            group.entries.forEach(entry => {
                const dups = Object.entries(entry.duplicates)
                    .map(([id, count]) => `<span class="sticker-item">${id} <strong>(x${count})</strong></span>`)
                    .join('');
                html += `
                    <div class="country-entry">
                        <strong>${entry.name}</strong>
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

async function loadParallels() {
    btnPars.classList.add('active');
    btnDups.classList.remove('active');
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
                let pList = '';
                Object.entries(entry.parallels).forEach(([sid, types]) => {
                    const typeTags = Object.entries(types)
                        .map(([t, c]) => `<span class="parallel-tag" style="background: ${t}">${t}: ${c}</span>`)
                        .join('');
                    pList += `<div class="sticker-item" style="margin-bottom:6px; display:block;"><strong>${sid}:</strong> ${typeTags}</div>`;
                });
                html += `
                    <div class="country-entry">
                        <strong>${entry.name}</strong>
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

btnDups.addEventListener('click', loadDuplicates);
btnPars.addEventListener('click', loadParallels);

// Initialize
loadDuplicates();