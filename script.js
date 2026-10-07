/* ==========================================================
   ResumeAI — shared script
   ----------------------------------------------------------
   This file ONLY handles the interface:
     - collecting input, validating files
     - sending data to the backend API
     - displaying whatever the backend returns
   No AI logic, no scoring, no sample data lives here.
   ========================================================== */

/* ----------------------------------------------------------
   1. CONFIG — set API_BASE when your backend is ready
   ---------------------------------------------------------- */
const CONFIG = {
  // Example: "http://localhost:8000". Leave empty until a backend exists.
  API_BASE: "",

  ENDPOINTS: {
    createScreening: () => "/api/screenings",                      // POST  JSON  -> { screeningId }
    uploadResumes:   (id) => `/api/screenings/${id}/resumes`,      // POST  multipart (field: "resumes")
    status:          (id) => `/api/screenings/${id}/status`,       // GET   -> see updateProcessingStatus()
    candidate:       (id, i) => `/api/screenings/${id}/candidates/${i}`, // GET -> see renderCandidate()
    summary:         (id) => `/api/screenings/${id}/summary`,      // GET   -> see renderSummary()
  },

  POLL_INTERVAL_MS: 2000,
  ALL_FORMATS: ["pdf", "doc", "docx", "jpg", "jpeg", "png"],
};

/* ----------------------------------------------------------
   2. SMALL HELPERS
   ---------------------------------------------------------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const ICONS = {
  logo: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
  plus: '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  settings: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="m21 16-5-5-8 9"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  check: '<path d="m5 12 5 5 9-10"/>',
  "arrow-left": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
  "chevron-right": '<path d="m9 6 6 6-6 6"/>',
  play: '<path d="M7 4v16l13-8z"/>',
  pin: '<path d="M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
  star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
  trend: '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.5-4M4 4v4h4M4 13a8 8 0 0 0 14.5 4M20 20v-4h-4"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
  sparkle: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
  warn: '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>',
};

function icon(name) {
  return `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;
}

// Replaces <i data-icon="name"></i> placeholders with SVG icons.
function hydrateIcons(root = document) {
  $$("i[data-icon]", root).forEach((el) => {
    el.innerHTML = icon(el.dataset.icon);
    el.removeAttribute("data-icon");
  });
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getExt(name) {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot + 1).toLowerCase();
}

function initials(name) {
  if (!name) return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((p) => p[0]).join("").toUpperCase();
}

function setText(sel, value, fallback = "—") {
  const el = $(sel);
  if (el) el.textContent = value === undefined || value === null || value === "" ? fallback : value;
}

function showToast(message) {
  let t = $("#toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "toast";
    t.className = "toast";
    document.body.appendChild(t);
  }
  t.textContent = message;
  t.classList.add("show");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => t.classList.remove("show"), 2600);
}

function showBanner(container, message, type = "error", list = []) {
  if (!container) return;
  container.className = `banner banner-${type}`;
  container.innerHTML = "";
  container.insertAdjacentHTML("afterbegin", icon(type === "error" ? "alert" : "info"));
  const body = document.createElement("div");
  const p = document.createElement("div");
  p.textContent = message;
  body.appendChild(p);
  if (list.length) {
    const ul = document.createElement("ul");
    list.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      ul.appendChild(li);
    });
    body.appendChild(ul);
  }
  container.appendChild(body);
  container.classList.remove("hidden");
}

function hideBanner(container) {
  if (container) container.classList.add("hidden");
}

/* ----------------------------------------------------------
   3. SETTINGS (stored in the browser only)
   ---------------------------------------------------------- */
const DEFAULT_SETTINGS = {
  name: "",
  email: "",
  minScore: 60,
  sensitivity: "balanced",
  aiExplanation: true,
  maxFileMB: 10,
  formats: ["pdf", "doc", "docx", "jpg", "jpeg", "png"],
  theme: "light",
  notifyComplete: true,
  notifyErrors: true,
};

function getSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem("resumeai.settings") || "{}");
    return { ...DEFAULT_SETTINGS, ...saved };
  } catch (e) {
    return { ...DEFAULT_SETTINGS };
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
}

/* ----------------------------------------------------------
   4. SHARED PAGE CHROME (sidebar + user chip)
   ---------------------------------------------------------- */
function renderSidebar() {
  const sidebar = $("#sidebar");
  if (!sidebar) return;
  const page = document.body.dataset.page;
  const links = [
    { href: "index.html", icon: "grid", label: "Dashboard", pages: ["dashboard"] },
    { href: "index.html#new", icon: "plus", label: "New Screening", pages: ["screening", "candidate"] },
    { href: "summary.html", icon: "clock", label: "Screening History", pages: ["summary"] },
  ];
  const item = (l) =>
    `<a class="nav-link ${l.pages.includes(page) ? "active" : ""}" href="${l.href}">${icon(l.icon)}<span>${l.label}</span></a>`;

  sidebar.innerHTML = `
    <a class="brand" href="index.html">${icon("logo")}<span>ResumeAI</span></a>
    <nav class="nav">${links.map(item).join("")}</nav>
    <nav class="nav nav-bottom">
      <a class="nav-link ${page === "settings" ? "active" : ""}" href="settings.html">${icon("settings")}<span>Settings</span></a>
    </nav>`;
}

function renderUserChip() {
  const s = getSettings();
  const name = s.name.trim() || "Recruiter";
  setText("#userName", name);
  setText("#userAvatar", initials(name));
}

/* ----------------------------------------------------------
   5. API LAYER
   ---------------------------------------------------------- */
class BackendNotConnectedError extends Error {
  constructor() {
    super("The backend is not connected yet. Set CONFIG.API_BASE in script.js once your API is running.");
    this.name = "BackendNotConnectedError";
  }
}

async function apiRequest(path, options = {}) {
  if (!CONFIG.API_BASE) throw new BackendNotConnectedError();
  const res = await fetch(CONFIG.API_BASE + path, options);
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).message || ""; } catch (e) { /* ignore */ }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function currentScreeningId() {
  return sessionStorage.getItem("resumeai.screeningId");
}

/* ----------------------------------------------------------
   6. DASHBOARD (index.html)
   ---------------------------------------------------------- */
const selectedFiles = []; // File objects the user picked

function initDashboard() {
  const jd = $("#jobDescription");
  const counter = $("#charCount");
  const clearBtn = $("#clearJd");
  const dropzone = $("#dropzone");
  const fileInput = $("#fileInput");
  const settings = getSettings();

  $("#formatHint").textContent =
    `${settings.formats.map((f) => f.toUpperCase()).join(", ")} · max ${settings.maxFileMB} MB each`;
  fileInput.setAttribute("accept", settings.formats.map((f) => "." + f).join(","));

  jd.addEventListener("input", () => { counter.textContent = jd.value.length.toLocaleString(); });
  clearBtn.addEventListener("click", () => {
    jd.value = "";
    counter.textContent = "0";
    jd.focus();
  });

  $("#browseBtn").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    addFiles(fileInput.files);
    fileInput.value = ""; // allow re-selecting the same file
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("dragover"); }));
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("dragover"); }));
  dropzone.addEventListener("drop", (e) => addFiles(e.dataTransfer.files));

  $("#startBtn").addEventListener("click", startScreening);
  renderFileList();
}

// Checks one file against the allowed formats / max size from Settings.
function validateFile(file, settings) {
  const ext = getExt(file.name);
  if (!settings.formats.includes(ext)) {
    return `"${file.name}" — .${ext || "?"} files are not allowed.`;
  }
  if (file.size > settings.maxFileMB * 1024 * 1024) {
    return `"${file.name}" — larger than ${settings.maxFileMB} MB (${formatSize(file.size)}).`;
  }
  if (file.size === 0) {
    return `"${file.name}" — the file is empty.`;
  }
  return null;
}

function addFiles(fileList) {
  const settings = getSettings();
  const errors = [];
  Array.from(fileList).forEach((file) => {
    const problem = validateFile(file, settings);
    if (problem) { errors.push(problem); return; }
    const duplicate = selectedFiles.some((f) => f.name === file.name && f.size === file.size && f.lastModified === file.lastModified);
    if (duplicate) { errors.push(`"${file.name}" — already added.`); return; }
    selectedFiles.push(file);
  });
  renderFileList();
  const banner = $("#formMessage");
  if (errors.length) showBanner(banner, "Some files were not added:", "error", errors);
  else hideBanner(banner);
}

function removeFile(index) {
  selectedFiles.splice(index, 1);
  renderFileList();
}

function renderFileList() {
  const list = $("#fileList");
  const count = $("#fileCount");
  if (!list) return;
  list.innerHTML = "";
  selectedFiles.forEach((file, i) => {
    const ext = getExt(file.name);
    const isImage = ["jpg", "jpeg", "png"].includes(ext);
    const li = document.createElement("li");
    li.className = "file-item";
    li.innerHTML = `
      <span class="file-icon">${icon(isImage ? "image" : "file")}</span>
      <div class="file-info">
        <div class="file-name"></div>
        <div class="file-meta"></div>
      </div>
      <button type="button" class="file-remove" aria-label="Remove file">${icon("x")}</button>`;
    $(".file-name", li).textContent = file.name;
    $(".file-meta", li).textContent = `${ext.toUpperCase() || "FILE"} · ${formatSize(file.size)}`;
    $(".file-remove", li).addEventListener("click", () => removeFile(i));
    list.appendChild(li);
  });
  count.textContent = selectedFiles.length
    ? `${selectedFiles.length} file${selectedFiles.length === 1 ? "" : "s"} selected`
    : "";
}

// Called by the "Start Screening" button.
async function startScreening() {
  const banner = $("#formMessage");
  const btn = $("#startBtn");
  const jobDescription = $("#jobDescription").value.trim();

  const problems = [];
  if (!jobDescription) problems.push("Paste a job description.");
  if (!selectedFiles.length) problems.push("Upload at least one CV.");
  if (problems.length) {
    showBanner(banner, "Please fix the following:", "error", problems);
    return;
  }

  hideBanner(banner);
  btn.disabled = true;
  btn.lastChild.textContent = " Starting…";

  try {
    const screeningId = await sendScreeningRequest(jobDescription, selectedFiles);
    sessionStorage.setItem("resumeai.screeningId", screeningId);
    sessionStorage.setItem("resumeai.candidateIndex", "0");
    window.location.href = "screening.html";
  } catch (err) {
    showBanner(banner, err.message, err instanceof BackendNotConnectedError ? "info" : "error");
    btn.disabled = false;
    btn.lastChild.textContent = " Start Screening";
  }
}

// Step 1: create the screening with the job description + settings.
// Step 2: upload the CV files. Returns the screeningId.
async function sendScreeningRequest(jobDescription, files) {
  const s = getSettings();
  const created = await apiRequest(CONFIG.ENDPOINTS.createScreening(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jobDescription,
      options: {
        minMatchScore: s.minScore,
        skillSensitivity: s.sensitivity,
        aiExplanation: s.aiExplanation,
      },
    }),
  });
  await uploadResumes(created.screeningId, files);
  return created.screeningId;
}

async function uploadResumes(screeningId, files) {
  const form = new FormData();
  files.forEach((file) => form.append("resumes", file, file.name));
  return apiRequest(CONFIG.ENDPOINTS.uploadResumes(screeningId), { method: "POST", body: form });
}

/* ----------------------------------------------------------
   7. PROCESSING (screening.html)
   ---------------------------------------------------------- */
const STEP_KEYS = [
  "readingJobDescription",
  "uploadingCvs",
  "extractingInformation",
  "matchingSkills",
  "calculatingScore",
  "generatingExplanation",
];
const STATE_LABELS = { pending: "Waiting", active: "In progress", done: "Done", error: "Failed" };

function initProcessing() {
  const id = currentScreeningId();
  if (!id) {
    $("#processContent").classList.add("hidden");
    $("#noScreening").classList.remove("hidden");
    return;
  }
  updateProcessingStatus({ steps: {} }); // everything starts as "Waiting"
  pollStatus(id);
}

/*
  Expected backend response from GET /api/screenings/:id/status
  {
    "status": "processing" | "completed" | "failed",
    "message": "optional text shown to the user",
    "steps": {
      "readingJobDescription": "pending" | "active" | "done" | "error",
      ... one entry per key in STEP_KEYS
    }
  }
*/
function updateProcessingStatus(data) {
  const steps = data.steps || {};
  let doneCount = 0;
  STEP_KEYS.forEach((key) => {
    const li = $(`.step[data-step="${key}"]`);
    if (!li) return;
    const state = STATE_LABELS[steps[key]] ? steps[key] : "pending";
    li.classList.remove("active", "done", "error");
    if (state !== "pending") li.classList.add(state);
    $(".step-state", li).textContent = STATE_LABELS[state];
    $(".step-dot", li).innerHTML = state === "done" ? icon("check") : state === "error" ? icon("x") : "";
    if (state === "done") doneCount++;
  });
  $("#progressFill").style.width = `${(doneCount / STEP_KEYS.length) * 100}%`;
  setText("#statusMessage", data.message, "");
}

async function pollStatus(id) {
  const banner = $("#processMessage");
  try {
    const data = await apiRequest(CONFIG.ENDPOINTS.status(id));
    hideBanner(banner);
    updateProcessingStatus(data);
    if (data.status === "completed") {
      window.location.href = "candidate.html";
      return;
    }
    if (data.status === "failed") {
      showBanner(banner, data.message || "Screening failed. Please try again.", "error");
      $("#retryLink").classList.remove("hidden");
      return;
    }
  } catch (err) {
    showBanner(banner, err.message, err instanceof BackendNotConnectedError ? "info" : "error");
    if (err instanceof BackendNotConnectedError) return; // nothing to poll yet
  }
  setTimeout(() => pollStatus(id), CONFIG.POLL_INTERVAL_MS);
}

/* ----------------------------------------------------------
   8. CANDIDATE REVIEW (candidate.html)
   ---------------------------------------------------------- */
let candidateTotal = null;

function initCandidate() {
  const id = currentScreeningId();
  if (!id) {
    $("#reviewContent").classList.add("hidden");
    $("#noScreening").classList.remove("hidden");
    return;
  }
  const index = parseInt(new URLSearchParams(location.search).get("i") ?? sessionStorage.getItem("resumeai.candidateIndex") ?? "0", 10) || 0;
  $("#prevBtn").addEventListener("click", () => goToCandidate(index - 1));
  $("#nextBtn").addEventListener("click", () => goToCandidate(index + 1));
  loadCandidate(index);
}

function goToCandidate(index) {
  if (candidateTotal !== null && index >= candidateTotal) {
    window.location.href = "summary.html";
    return;
  }
  if (index < 0) return;
  sessionStorage.setItem("resumeai.candidateIndex", String(index));
  history.replaceState(null, "", `candidate.html?i=${index}`);
  initCandidateIndex(index);
}

function initCandidateIndex(index) {
  // re-bind buttons to the new index
  const prev = $("#prevBtn").cloneNode(true);
  const next = $("#nextBtn").cloneNode(true);
  $("#prevBtn").replaceWith(prev);
  $("#nextBtn").replaceWith(next);
  prev.addEventListener("click", () => goToCandidate(index - 1));
  next.addEventListener("click", () => goToCandidate(index + 1));
  loadCandidate(index);
}

/*
  Expected backend response from GET /api/screenings/:id/candidates/:index
  {
    "total": number,                 // how many candidates in this screening
    "name": string,
    "role": string,
    "experience": string,            // e.g. "3 years"
    "location": string,
    "matchScore": number,            // 0–100, calculated by the backend
    "matchedSkills": string[],
    "missingSkills": string[],
    "experienceSummary": string,
    "explanation": string,           // written by the backend AI
    "resumeUrl": string | null
  }
*/
async function loadCandidate(index) {
  const banner = $("#reviewMessage");
  $("#prevBtn").disabled = index <= 0;
  try {
    const candidate = await apiRequest(CONFIG.ENDPOINTS.candidate(currentScreeningId(), index));
    hideBanner(banner);
    candidateTotal = typeof candidate.total === "number" ? candidate.total : null;
    renderCandidate(candidate, index);
  } catch (err) {
    showBanner(banner, err.message, err instanceof BackendNotConnectedError ? "info" : "error");
  }
}

function renderChips(container, items, cls, emptyText) {
  container.innerHTML = "";
  if (!Array.isArray(items) || !items.length) {
    container.innerHTML = `<span class="empty-inline">${emptyText}</span>`;
    return;
  }
  items.forEach((skill) => {
    const chip = document.createElement("span");
    chip.className = `chip ${cls}`;
    chip.textContent = skill;
    container.appendChild(chip);
  });
}

function renderCandidate(c, index) {
  setText("#candName", c.name, "Candidate Name");
  setText("#candRole", c.role, "Job Role");
  setText("#candExperience", c.experience);
  setText("#candLocation", c.location);
  setText("#candAvatar", initials(c.name));

  const score = Number(c.matchScore);
  const hasScore = Number.isFinite(score);
  setText("#candScore", hasScore ? `${score}%` : "—");
  $("#scoreRing").style.setProperty("--pct", hasScore ? Math.max(0, Math.min(100, score)) : 0);

  renderChips($("#matchedSkills"), c.matchedSkills, "chip-matched", "No matched skills returned.");
  renderChips($("#missingSkills"), c.missingSkills, "chip-missing", "No missing skills returned.");
  setText("#matchedCount", Array.isArray(c.matchedSkills) ? c.matchedSkills.length : "", "");
  setText("#missingCount", Array.isArray(c.missingSkills) ? c.missingSkills.length : "", "");

  setText("#expSummary", c.experienceSummary, "No experience details returned.");
  setText("#aiExplanation", c.explanation, "No explanation returned.");

  const total = candidateTotal;
  setText("#candCounter", total ? `Candidate ${index + 1} of ${total}` : `Candidate ${index + 1}`);

  const next = $("#nextBtn");
  const isLast = total !== null && index + 1 >= total;
  next.innerHTML = `${isLast ? "View Summary" : "Next Candidate"} ${icon("arrow-right")}`;

  const resumeBtn = $("#resumeBtn");
  resumeBtn.disabled = !c.resumeUrl;
  resumeBtn.onclick = () => { if (c.resumeUrl) window.open(c.resumeUrl, "_blank", "noopener"); };
}

/* ----------------------------------------------------------
   9. SUMMARY (summary.html)
   ---------------------------------------------------------- */
function initSummary() {
  if (!currentScreeningId()) {
    $("#summaryContent").classList.add("hidden");
    $("#noScreening").classList.remove("hidden");
    return;
  }
  loadSummary();
}

/*
  Expected backend response from GET /api/screenings/:id/summary
  {
    "totalCandidates": number,
    "strongMatches": number,
    "averageMatch": number,          // 0–100
    "topMatch": number,              // 0–100
    "candidates": [ { "name": string, "role": string, "matchScore": number } ]  // already sorted by the backend
  }
*/
async function loadSummary() {
  const banner = $("#summaryMessage");
  try {
    const data = await apiRequest(CONFIG.ENDPOINTS.summary(currentScreeningId()));
    hideBanner(banner);
    renderSummary(data);
  } catch (err) {
    showBanner(banner, err.message, err instanceof BackendNotConnectedError ? "info" : "error");
  }
}

function renderSummary(data) {
  const pct = (v) => (Number.isFinite(Number(v)) && v !== null && v !== undefined ? `${v}%` : "—");
  setText("#statTotal", data.totalCandidates);
  setText("#statStrong", data.strongMatches);
  setText("#statAverage", pct(data.averageMatch));
  setText("#statTop", pct(data.topMatch));

  const list = $("#resultList");
  list.innerHTML = "";
  const candidates = Array.isArray(data.candidates) ? data.candidates : [];
  if (!candidates.length) {
    list.innerHTML = '<li class="empty-state">No candidates returned.</li>';
    return;
  }
  candidates.forEach((c, i) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <a class="result-row" href="candidate.html?i=${i}">
        <span class="rank">${i + 1}</span>
        <span class="result-avatar"></span>
        <span class="result-main"><div class="result-name"></div><div class="result-role"></div></span>
        <span class="score-pill"></span>
        ${icon("chevron-right")}
      </a>`;
    $(".result-avatar", li).textContent = initials(c.name);
    $(".result-name", li).textContent = c.name || "Unnamed candidate";
    $(".result-role", li).textContent = c.role || "";
    $(".score-pill", li).textContent = pct(c.matchScore);
    list.appendChild(li);
  });
}

/* ----------------------------------------------------------
   10. SETTINGS (settings.html)
   ---------------------------------------------------------- */
function initSettings() {
  fillSettingsForm(getSettings());

  const range = $("#minScore");
  range.addEventListener("input", () => setText("#minScoreValue", `${range.value}%`));
  $$('input[name="theme"]').forEach((r) => r.addEventListener("change", () => applyTheme(r.value)));

  $("#saveBtn").addEventListener("click", saveSettings);
  $("#resetBtn").addEventListener("click", () => {
    localStorage.removeItem("resumeai.settings");
    fillSettingsForm({ ...DEFAULT_SETTINGS });
    applyTheme(DEFAULT_SETTINGS.theme);
    renderUserChip();
    showToast("Settings reset to defaults");
  });
}

function fillSettingsForm(s) {
  $("#setName").value = s.name;
  $("#setEmail").value = s.email;
  $("#minScore").value = s.minScore;
  setText("#minScoreValue", `${s.minScore}%`);
  $("#sensitivity").value = s.sensitivity;
  $("#aiExplanation").checked = s.aiExplanation;
  $("#maxFileMB").value = s.maxFileMB;
  $$('input[name="format"]').forEach((cb) => { cb.checked = s.formats.includes(cb.value); });
  $$('input[name="theme"]').forEach((r) => { r.checked = r.value === s.theme; });
  $("#notifyComplete").checked = s.notifyComplete;
  $("#notifyErrors").checked = s.notifyErrors;
}

function saveSettings() {
  const banner = $("#settingsMessage");
  const formats = $$('input[name="format"]:checked').map((cb) => cb.value);
  const maxFileMB = parseFloat($("#maxFileMB").value);

  const problems = [];
  if (!formats.length) problems.push("Choose at least one allowed CV format.");
  if (!(maxFileMB > 0 && maxFileMB <= 100)) problems.push("Maximum file size must be between 1 and 100 MB.");
  if (problems.length) {
    showBanner(banner, "Settings were not saved:", "error", problems);
    return;
  }
  hideBanner(banner);

  const settings = {
    name: $("#setName").value.trim(),
    email: $("#setEmail").value.trim(),
    minScore: parseInt($("#minScore").value, 10),
    sensitivity: $("#sensitivity").value,
    aiExplanation: $("#aiExplanation").checked,
    maxFileMB,
    formats,
    theme: ($('input[name="theme"]:checked') || { value: "light" }).value,
    notifyComplete: $("#notifyComplete").checked,
    notifyErrors: $("#notifyErrors").checked,
  };
  localStorage.setItem("resumeai.settings", JSON.stringify(settings));
  applyTheme(settings.theme);
  renderUserChip();
  showToast("Settings saved");
}

/* ----------------------------------------------------------
   11. BOOT
   ---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  applyTheme(getSettings().theme);
  renderSidebar();
  renderUserChip();
  hydrateIcons();

  const page = document.body.dataset.page;
  if (page === "dashboard") initDashboard();
  if (page === "screening") initProcessing();
  if (page === "candidate") initCandidate();
  if (page === "summary") initSummary();
  if (page === "settings") initSettings();
});