const groupSelect = document.getElementById("group-select");
const countrySelect = document.getElementById("country-select");
const loadReportButton = document.getElementById("load-report");
const stickerInput = document.getElementById("sticker-input");
const saveStickersButton = document.getElementById("save-stickers");
const reportOutput = document.getElementById("report-output");
const saveStatus = document.getElementById("save-status");

let groupMap = {};
let expandedParallelId = null;

function formatReport(data) {
  const dupEntries = Object.entries(data.duplicates || {});
  const dupText = dupEntries.length > 0 ? dupEntries.map(([id, count]) => `${id} (x${count})`).join(", ") : "none";
  const totalDups = data.counts.total_duplicates || 0;
  const displayName = data.country_name || data.country;

  return [
    `Country: ${displayName}`,
    `Completion: ${data.completion_percentage}%`,
    `Unique Found: ${data.counts.found} / ${data.counts.total}`,
    `Missing: ${data.counts.missing}`,
    `Total Duplicates (Extras): ${totalDups}`,
    "",
    `Missing: ${data.missing.join(", ") || "none"}`,
    `Duplicates: ${dupText}`,
  ].join("\n");
}

function showMessage(message, type = "success") {
  saveStatus.textContent = message;
  saveStatus.className = `status ${type}`;
}

async function loadGroups() {
  try {
    const data = await apiFetch("/groups");
    groupMap = data.groups || {};
    const groupOptions = Object.keys(groupMap)
      .map((groupKey) => `<option value="${groupKey}">${groupKey}</option>`)
      .join("");
    groupSelect.innerHTML = groupOptions;
    if (groupSelect.options.length > 0) {
      countrySelect.innerHTML = groupMap[groupSelect.value]
        .map((code) => `<option value="${code}">${code}</option>`)
        .join("");
    }
  } catch (error) {
    reportOutput.textContent = `Error loading groups: ${error.message}`;
    showMessage("Could not load groups.", "error");
  }
}

function updateCountryOptions() {
  const selectedGroup = groupSelect.value;
  const countries = groupMap[selectedGroup] || [];
  countrySelect.innerHTML = countries
    .map((code) => `<option value="${code}">${code}</option>`)
    .join("");
}

async function loadReport() {
  const countryCode = countrySelect.value;
  if (!countryCode) {
    return;
  }

  try {
    const data = await apiFetch(`/inventory/${countryCode}`);
    renderStickerGrid(data);
    showMessage("Report loaded.", "success");
  } catch (error) {
    reportOutput.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    showMessage("Could not load report.", "error");
  }
}

function renderStickerGrid(data) {
  reportOutput.innerHTML = "";
  reportOutput.classList.add("html-report");
  const parallelTypes = data.parallel_types || [];
  
  const dupEntries = Object.entries(data.duplicates || {});
  const dupListText = dupEntries.length > 0 
    ? dupEntries.map(([id, count]) => `<strong>${id}</strong> (${count})`).join(", ") 
    : "none";

  const flagUrl = getFlagUrl(data.country);
  const flagHtml = flagUrl ? `<img src="${flagUrl}" class="flag-icon" alt="">` : '';

  const summary = document.createElement("div");
  summary.className = "report-summary";
  const summaryHtml = `
    ${flagHtml}<h2 style="margin: 0; font-size: 1.15rem; display: inline-block; vertical-align: middle; margin-right: 12px;">${data.country_name || data.country}</h2>
    <span style="font-size: 0.9rem; vertical-align: middle;">Completion: <strong>${data.completion_percentage}%</strong> (${data.counts.found}/${data.counts.total}) | Extras: <strong>${data.counts.total_duplicates}</strong></span>
    <p style="font-size: 0.85rem; color: #555; margin: 2px 0 0;">Detailed Extras: ${dupListText}</p>`.replace(/\n\s+/g, ' ');
  summary.innerHTML = summaryHtml;
  reportOutput.appendChild(summary);

  Object.entries(data.sections).forEach(([sectionName, stickers]) => {
    const sectionHeader = document.createElement("h3");
    sectionHeader.textContent = sectionName;
    reportOutput.appendChild(sectionHeader);

    const grid = document.createElement("div");
    grid.className = "sticker-grid";

    Object.entries(stickers).forEach(([id, count]) => {
      const stickerParallels = (data.parallels && data.parallels[id]) || {};
      const hasParallels = Object.values(stickerParallels).some(v => v > 0);

      const card = document.createElement("div");
      card.id = `sticker-${id}`;
      card.className = "sticker-card";
      if (count > 1) card.classList.add("extra");
      else if (count > 0) card.classList.add("owned");

      const isExpanded = expandedParallelId === id;
      card.innerHTML = `
        <div class="id-label">${id}</div>
        <div class="card-actions" style="margin-bottom: 2px;">
          <button onclick="updateCount('${id}', ${count - 1})" style="padding: 1px 6px;">-</button>
          <span>${count}</span>
          <button onclick="updateCount('${id}', ${count + 1})" style="padding: 1px 6px;">+</button>
        </div>
        ${parallelTypes.length > 0 ? `
          <div style="margin-top: 6px; border-top: 1px dashed #ccc; padding-top: 4px;">
            <button onclick="toggleParallels('${id}')" style="font-size: 0.75rem; padding: 2px 6px; background: none; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; color: ${hasParallels ? '#d32f2f' : '#777'}">
              ${hasParallels ? '★ Parallels' : 'Parallels'}
            </button>
          <div id="parallels-${id}" style="display: ${isExpanded ? 'block' : 'none'}; margin-top: 6px; font-size: 0.8rem; text-align: left;">
              ${parallelTypes.map(type => {
                const pCount = stickerParallels[type] || 0;
                return `
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="color: ${type}; font-weight: bold;">${type}:</span>
                    <div style="display: flex; gap: 4px; align-items: center;">
                      <button onclick="updateParallelCount('${id}', '${type}', ${pCount - 1})" style="padding: 0 5px; font-size: 0.85rem; line-height: 1;">-</button>
                      <span>${pCount}</span>
                      <button onclick="updateParallelCount('${id}', '${type}', ${pCount + 1})" style="padding: 0 5px; font-size: 0.85rem; line-height: 1;">+</button>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>` : ''}
      `;
      grid.appendChild(card);
    });
    reportOutput.appendChild(grid);
  });
}

window.toggleParallels = function(id) {
  const el = document.getElementById(`parallels-${id}`);
  if (el) {
    const isOpening = el.style.display === "none";
    el.style.display = isOpening ? "block" : "none";
    expandedParallelId = isOpening ? id : null;
  }
};

window.updateCount = async function(stickerId, newCount) {
  if (newCount < 0) return;
  const countryCode = countrySelect.value;
  try {
    const data = await apiFetch(`/inventory/${countryCode}/sticker`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sticker_id: stickerId, count: newCount }),
    });
    renderStickerGrid(data);
  } catch (error) {
    showMessage(error.message, "error");
  }
};

window.updateParallelCount = async function(stickerId, type, newCount) {
  if (newCount < 0) return;
  const countryCode = countrySelect.value;
  try {
    const data = await apiFetch(`/inventory/${countryCode}/parallel`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sticker_id: stickerId, parallel_type: type, count: newCount }),
    });
    renderStickerGrid(data);
  } catch (error) {
    showMessage(error.message, "error");
  }
};

async function saveStickers() {
  const countryCode = countrySelect.value;
  const stickersText = stickerInput.value.trim();
  if (!countryCode || !stickersText) {
    showMessage("Select a group and country, and enter sticker numbers.", "error");
    return;
  }

  try {
    const payload = { stickers: stickersText };
    const data = await apiFetch(`/inventory/${countryCode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderStickerGrid(data);
    showMessage("Stickers saved successfully.", "success");
    stickerInput.value = "";
  } catch (error) {
    showMessage(error.message, "error");
  }
}

loadGroups();
groupSelect.addEventListener("change", updateCountryOptions);
loadReportButton.addEventListener("click", loadReport);
saveStickersButton.addEventListener("click", saveStickers);
