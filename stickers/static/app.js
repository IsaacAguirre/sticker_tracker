const groupSelect = document.getElementById("group-select");
const countrySelect = document.getElementById("country-select");
const loadReportButton = document.getElementById("load-report");
const stickerInput = document.getElementById("sticker-input");
const saveStickersButton = document.getElementById("save-stickers");
const reportOutput = document.getElementById("report-output");
const saveStatus = document.getElementById("save-status");

let groupMap = {};

async function apiFetch(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error(data.detail || data || response.statusText);
  }
  return data;
}

function formatReport(data) {
  const dupEntries = Object.entries(data.duplicates || {});
  const dupText = dupEntries.length > 0 ? dupEntries.map(([id, count]) => `${id} (x${count})`).join(", ") : "none";
  const displayName = data.country_name || data.country;

  return [
    `Country: ${displayName}`,
    `Completion: ${data.completion_percentage}%`,
    `Found: ${data.counts.found}`,
    `Missing: ${data.counts.missing}`,
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
    reportOutput.textContent = formatReport(data);
    showMessage("Report loaded.", "success");
  } catch (error) {
    reportOutput.textContent = `Error: ${error.message}`;
    showMessage("Could not load report.", "error");
  }
}

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
    reportOutput.textContent = formatReport(data);
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
