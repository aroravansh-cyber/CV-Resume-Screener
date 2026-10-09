/* ==========================================================
   ResumeAI — shared script
   ----------------------------------------------------------
   Frontend interface for ResumeAI.

   Backend:
   Flask API running on:
   http://127.0.0.1:5000

   This file handles:
     - collecting input
     - validating files
     - sending data to Flask backend
     - displaying backend results
   ========================================================== */


/* ----------------------------------------------------------
   1. CONFIGURATION
   ---------------------------------------------------------- */

const CONFIG = {

  // Flask backend from main.py
  API_BASE: "http://127.0.0.1:8000",

  ENDPOINTS: {

    // Create screening
    createScreening: () =>
      "/api/screenings",

    // Upload resumes
    uploadResumes: (id) =>
      `/api/screenings/${id}/resumes`,

    // Processing status
    status: (id) =>
      `/api/screenings/${id}/status`,

    // Candidate information
    candidate: (id, i) =>
      `/api/screenings/${id}/candidates/${i}`,

    // Screening summary
    summary: (id) =>
      `/api/screenings/${id}/summary`,
  },

  // How frequently the frontend checks processing status
  POLL_INTERVAL_MS: 2000,

  // Supported formats
  ALL_FORMATS: [
    "pdf",
    "doc",
    "docx",
    "jpg",
    "jpeg",
    "png"
  ],
};


/* ----------------------------------------------------------
   2. SMALL HELPERS
   ---------------------------------------------------------- */

const $ = (sel, root = document) =>
  root.querySelector(sel);

const $$ = (sel, root = document) =>
  Array.from(root.querySelectorAll(sel));


/* ----------------------------------------------------------
   ICONS
   ---------------------------------------------------------- */

const ICONS = {

  logo:
    '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>' +
    '<path d="M19 16l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',

  grid:
    '<rect x="3" y="3" width="7" height="7" rx="1.5"/>' +
    '<rect x="14" y="3" width="7" height="7" rx="1.5"/>' +
    '<rect x="14" y="14" width="7" height="7" rx="1.5"/>' +
    '<rect x="3" y="14" width="7" height="7" rx="1.5"/>',

  plus:
    '<circle cx="12" cy="12" r="9"/>' +
    '<path d="M12 8v8M8 12h8"/>',

  clock:
    '<circle cx="12" cy="12" r="9"/>' +
    '<path d="M12 7v5l3 2"/>',

  settings:
    '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/>' +
    '<circle cx="16" cy="6" r="2"/>' +
    '<circle cx="10" cy="12" r="2"/>' +
    '<circle cx="18" cy="18" r="2"/>',

  file:
    '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>' +
    '<path d="M14 3v5h5M9 13h6M9 17h6"/>',

  image:
    '<rect x="3" y="4" width="18" height="16" rx="2"/>' +
    '<circle cx="9" cy="10" r="1.5"/>' +
    '<path d="m21 16-5-5-8 9"/>',

  upload:
    '<path d="M12 16V4M7 9l5-5 5 5"/>' +
    '<path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',

  x:
    '<path d="M6 6l12 12M18 6 6 18"/>',

  check:
    '<path d="m5 12 5 5 9-10"/>',

  "arrow-left":
    '<path d="M19 12H5M11 6l-6 6 6 6"/>',

  "arrow-right":
    '<path d="M5 12h14M13 6l6 6-6 6"/>',

  "chevron-right":
    '<path d="m9 6 6 6-6 6"/>',

  play:
    '<path d="M7 4v16l13-8z"/>',

  pin:
    '<path d="M12 21s7-6.2 7-11a7 7 0 0 0-14 0c0 4.8 7 11 7 11z"/>' +
    '<circle cx="12" cy="10" r="2.5"/>',

  briefcase:
    '<rect x="3" y="7" width="18" height="13" rx="2"/>' +
    '<path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',

  users:
    '<circle cx="9" cy="8" r="3.5"/>' +
    '<path d="M2.5 20a6.5 6.5 0 0 1 13 0"/>' +
    '<path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',

  star:
    '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',

  trend:
    '<path d="m3 17 6-6 4 4 8-8"/>' +
    '<path d="M15 7h6v6"/>',

  refresh:
    '<path d="M20 11a8 8 0 0 0-14.5-4M4 4v4h4"/>' +
    '<path d="M4 13a8 8 0 0 0 14.5 4M20 20v-4h-4"/>',

  alert:
    '<circle cx="12" cy="12" r="9"/>' +
    '<path d="M12 8v5M12 16.5v.5"/>',

  info:
    '<circle cx="12" cy="12" r="9"/>' +
    '<path d="M12 11v6M12 7.5v.5"/>',

  sparkle:
    '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',

  warn:
    '<path d="M12 3 2 20h20z"/>' +
    '<path d="M12 10v4M12 17v.5"/>',
};


/* ----------------------------------------------------------
   ICON FUNCTION
   ---------------------------------------------------------- */

function icon(name) {

  return `
    <svg
      class="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      ${ICONS[name] || ""}
    </svg>
  `;
}


/* ----------------------------------------------------------
   HYDRATE ICONS
   ---------------------------------------------------------- */

function hydrateIcons(root = document) {

  $$("i[data-icon]", root).forEach((el) => {

    el.innerHTML = icon(el.dataset.icon);

    el.removeAttribute("data-icon");

  });
}


/* ----------------------------------------------------------
   FORMAT FILE SIZE
   ---------------------------------------------------------- */

function formatSize(bytes) {

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}


/* ----------------------------------------------------------
   GET FILE EXTENSION
   ---------------------------------------------------------- */

function getExt(name) {

  const dot = name.lastIndexOf(".");

  return dot === -1
    ? ""
    : name.slice(dot + 1).toLowerCase();
}


/* ----------------------------------------------------------
   INITIALS
   ---------------------------------------------------------- */

function initials(name) {

  if (!name) {
    return "?";
  }

  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();
}


/* ----------------------------------------------------------
   SET TEXT
   ---------------------------------------------------------- */

function setText(sel, value, fallback = "—") {

  const el = $(sel);

  if (!el) {
    return;
  }

  el.textContent =
    value === undefined ||
    value === null ||
    value === ""
      ? fallback
      : value;
}


/* ----------------------------------------------------------
   TOAST
   ---------------------------------------------------------- */

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

  showToast._timer = setTimeout(() => {

    t.classList.remove("show");

  }, 2600);
}


/* ----------------------------------------------------------
   SHOW BANNER
   ---------------------------------------------------------- */

function showBanner(
  container,
  message,
  type = "error",
  list = []
) {

  if (!container) {
    return;
  }

  container.className =
    `banner banner-${type}`;

  container.innerHTML = "";

  container.insertAdjacentHTML(
    "afterbegin",
    icon(type === "error" ? "alert" : "info")
  );

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


/* ----------------------------------------------------------
   HIDE BANNER
   ---------------------------------------------------------- */

function hideBanner(container) {

  if (container) {

    container.classList.add("hidden");

  }
}


/* ==========================================================
   3. SETTINGS
   ========================================================== */

const DEFAULT_SETTINGS = {

  name: "",

  email: "",

  minScore: 60,

  sensitivity: "balanced",

  aiExplanation: true,

  maxFileMB: 10,

  formats: [
    "pdf",
    "doc",
    "docx",
    "jpg",
    "jpeg",
    "png"
  ],

  theme: "light",

  notifyComplete: true,

  notifyErrors: true,
};


/* ----------------------------------------------------------
   GET SETTINGS
   ---------------------------------------------------------- */

function getSettings() {

  try {

    const saved =
      JSON.parse(
        localStorage.getItem(
          "resumeai.settings"
        ) || "{}"
      );

    return {
      ...DEFAULT_SETTINGS,
      ...saved
    };

  } catch (e) {

    return {
      ...DEFAULT_SETTINGS
    };

  }
}


/* ----------------------------------------------------------
   APPLY THEME
   ---------------------------------------------------------- */

function applyTheme(theme) {

  document.documentElement.setAttribute(
    "data-theme",
    theme === "dark"
      ? "dark"
      : "light"
  );
}


/* ==========================================================
   4. SIDEBAR
   ========================================================== */

function renderSidebar() {

  const sidebar = $("#sidebar");

  if (!sidebar) {
    return;
  }

  const page =
    document.body.dataset.page;

  const links = [

    {
      href: "index.html",
      icon: "grid",
      label: "Dashboard",
      pages: ["dashboard"]
    },

    {
      href: "index.html#new",
      icon: "plus",
      label: "New Screening",
      pages: [
        "screening",
        "candidate"
      ]
    },

    {
      href: "summary.html",
      icon: "clock",
      label: "Screening History",
      pages: ["summary"]
    },

  ];

  const item = (l) => {

    return `
      <a
        class="nav-link ${
          l.pages.includes(page)
            ? "active"
            : ""
        }"
        href="${l.href}"
      >
        ${icon(l.icon)}
        <span>${l.label}</span>
      </a>
    `;

  };


  sidebar.innerHTML = `

    <a class="brand" href="index.html">

      ${icon("logo")}

      <span>ResumeAI</span>

    </a>

    <nav class="nav">

      ${links.map(item).join("")}

    </nav>

    <nav class="nav nav-bottom">

      <a
        class="nav-link ${
          page === "settings"
            ? "active"
            : ""
        }"
        href="settings.html"
      >

        ${icon("settings")}

        <span>Settings</span>

      </a>

    </nav>

  `;
}


/* ----------------------------------------------------------
   USER CHIP
   ---------------------------------------------------------- */

function renderUserChip() {

  const s = getSettings();

  const name =
    s.name.trim() ||
    "Recruiter";

  setText(
    "#userName",
    name
  );

  setText(
    "#userAvatar",
    initials(name)
  );
}


/* ==========================================================
   5. API LAYER
   ========================================================== */


/* ----------------------------------------------------------
   BACKEND ERROR
   ---------------------------------------------------------- */

class BackendNotConnectedError
  extends Error {

  constructor() {

    super(
      "The backend is not connected. " +
      "Make sure Flask is running at " +
      CONFIG.API_BASE
    );

    this.name =
      "BackendNotConnectedError";
  }
}


/* ----------------------------------------------------------
   API REQUEST
   ---------------------------------------------------------- */

async function apiRequest(
  path,
  options = {}
) {

  if (!CONFIG.API_BASE) {

    throw new BackendNotConnectedError();

  }

  let res;

  try {

    res = await fetch(
      CONFIG.API_BASE + path,
      options
    );

  } catch (err) {

    throw new Error(
      "Cannot connect to ResumeAI backend. " +
      "Make sure Flask is running at " +
      CONFIG.API_BASE
    );

  }


  if (!res.ok) {

    let detail = "";

    try {

      const data =
        await res.json();

      detail =
        data.message ||
        data.error ||
        "";

    } catch (e) {

      // Response wasn't JSON.

    }

    throw new Error(
      detail ||
      `Request failed (${res.status})`
    );

  }


  try {

    return await res.json();

  } catch (err) {

    throw new Error(
      "Backend returned an invalid JSON response."
    );

  }
}


/* ----------------------------------------------------------
   CURRENT SCREENING ID
   ---------------------------------------------------------- */

function currentScreeningId() {

  return sessionStorage.getItem(
    "resumeai.screeningId"
  );
}


/* ==========================================================
   6. DASHBOARD
   ========================================================== */

const selectedFiles = [];


/* ----------------------------------------------------------
   INITIALIZE DASHBOARD
   ---------------------------------------------------------- */

function initDashboard() {

  const jd =
    $("#jobDescription");

  const counter =
    $("#charCount");

  const clearBtn =
    $("#clearJd");

  const dropzone =
    $("#dropzone");

  const fileInput =
    $("#fileInput");

  const settings =
    getSettings();


  if (!jd || !fileInput) {
    return;
  }


  const formatHint =
    $("#formatHint");

  if (formatHint) {

    formatHint.textContent =
      `${settings.formats
        .map((f) => f.toUpperCase())
        .join(", ")}
        · max ${settings.maxFileMB} MB each`;

  }


  fileInput.setAttribute(
    "accept",
    settings.formats
      .map((f) => "." + f)
      .join(",")
  );


  jd.addEventListener(
    "input",
    () => {

      if (counter) {

        counter.textContent =
          jd.value.length.toLocaleString();

      }

    }
  );


  if (clearBtn) {

    clearBtn.addEventListener(
      "click",
      () => {

        jd.value = "";

        if (counter) {
          counter.textContent = "0";
        }

        jd.focus();

      }
    );

  }


  const browseBtn =
    $("#browseBtn");

  if (browseBtn) {

    browseBtn.addEventListener(
      "click",
      () => fileInput.click()
    );

  }


  fileInput.addEventListener(
    "change",
    () => {

      addFiles(fileInput.files);

      fileInput.value = "";

    }
  );


  if (dropzone) {

    [
      "dragenter",
      "dragover"
    ].forEach((evt) => {

      dropzone.addEventListener(
        evt,
        (e) => {

          e.preventDefault();

          dropzone.classList.add(
            "dragover"
          );

        }
      );

    });


    [
      "dragleave",
      "drop"
    ].forEach((evt) => {

      dropzone.addEventListener(
        evt,
        (e) => {

          e.preventDefault();

          dropzone.classList.remove(
            "dragover"
          );

        }
      );

    });


    dropzone.addEventListener(
      "drop",
      (e) => {

        addFiles(
          e.dataTransfer.files
        );

      }
    );

  }


  const startBtn =
    $("#startBtn");

  if (startBtn) {

    startBtn.addEventListener(
      "click",
      startScreening
    );

  }


  renderFileList();
}


/* ----------------------------------------------------------
   VALIDATE FILE
   ---------------------------------------------------------- */

function validateFile(
  file,
  settings
) {

  const ext =
    getExt(file.name);


  if (
    !settings.formats.includes(ext)
  ) {

    return `
      "${file.name}" —
      .${ext || "?"} files are not allowed.
    `;

  }


  if (
    file.size >
    settings.maxFileMB * 1024 * 1024
  ) {

    return `
      "${file.name}" —
      larger than ${settings.maxFileMB} MB
      (${formatSize(file.size)}).
    `;

  }


  if (file.size === 0) {

    return `
      "${file.name}" —
      the file is empty.
    `;

  }


  return null;
}


/* ----------------------------------------------------------
   ADD FILES
   ---------------------------------------------------------- */

function addFiles(fileList) {

  const settings =
    getSettings();

  const errors = [];


  Array.from(fileList).forEach(
    (file) => {

      const problem =
        validateFile(
          file,
          settings
        );


      if (problem) {

        errors.push(problem);

        return;

      }


      const duplicate =
        selectedFiles.some(
          (f) =>
            f.name === file.name &&
            f.size === file.size &&
            f.lastModified ===
              file.lastModified
        );


      if (duplicate) {

        errors.push(
          `"${file.name}" — already added.`
        );

        return;

      }


      selectedFiles.push(file);

    }
  );


  renderFileList();


  const banner =
    $("#formMessage");


  if (errors.length) {

    showBanner(
      banner,
      "Some files were not added:",
      "error",
      errors
    );

  } else {

    hideBanner(banner);

  }
}


/* ----------------------------------------------------------
   REMOVE FILE
   ---------------------------------------------------------- */

function removeFile(index) {

  selectedFiles.splice(
    index,
    1
  );

  renderFileList();
}


/* ----------------------------------------------------------
   RENDER FILE LIST
   ---------------------------------------------------------- */

function renderFileList() {

  const list =
    $("#fileList");

  const count =
    $("#fileCount");


  if (!list) {
    return;
  }


  list.innerHTML = "";


  selectedFiles.forEach(
    (file, i) => {

      const ext =
        getExt(file.name);

      const isImage =
        [
          "jpg",
          "jpeg",
          "png"
        ].includes(ext);


      const li =
        document.createElement("li");

      li.className =
        "file-item";


      li.innerHTML = `

        <span class="file-icon">

          ${icon(
            isImage
              ? "image"
              : "file"
          )}

        </span>

        <div class="file-info">

          <div class="file-name"></div>

          <div class="file-meta"></div>

        </div>

        <button
          type="button"
          class="file-remove"
          aria-label="Remove file"
        >

          ${icon("x")}

        </button>

      `;


      $(".file-name", li)
        .textContent =
        file.name;


      $(".file-meta", li)
        .textContent =
        `${ext.toUpperCase() || "FILE"} · ${
          formatSize(file.size)
        }`;


      $(".file-remove", li)
        .addEventListener(
          "click",
          () => removeFile(i)
        );


      list.appendChild(li);

    }
  );


  if (count) {

    count.textContent =
      selectedFiles.length
        ? `${selectedFiles.length} file${
            selectedFiles.length === 1
              ? ""
              : "s"
          } selected`
        : "";

  }
}


/* ==========================================================
   START SCREENING
   ========================================================== */

async function startScreening() {

  const banner =
    $("#formMessage");

  const btn =
    $("#startBtn");

  const jd =
    $("#jobDescription");


  if (!jd || !btn) {
    return;
  }


  const jobDescription =
    jd.value.trim();


  const problems = [];


  if (!jobDescription) {

    problems.push(
      "Paste a job description."
    );

  }


  if (!selectedFiles.length) {

    problems.push(
      "Upload at least one CV."
    );

  }


  if (problems.length) {

    showBanner(
      banner,
      "Please fix the following:",
      "error",
      problems
    );

    return;
  }


  hideBanner(banner);


  btn.disabled = true;


  if (btn.lastChild) {

    btn.lastChild.textContent =
      " Starting…";

  }


  try {

    const screeningId =
      await sendScreeningRequest(
        jobDescription,
        selectedFiles
      );


    sessionStorage.setItem(
      "resumeai.screeningId",
      screeningId
    );


    sessionStorage.setItem(
      "resumeai.candidateIndex",
      "0"
    );


    window.location.href =
      "screening.html";


  } catch (err) {

    showBanner(
      banner,
      err.message,
      err instanceof BackendNotConnectedError
        ? "info"
        : "error"
    );


    btn.disabled = false;


    if (btn.lastChild) {

      btn.lastChild.textContent =
        " Start Screening";

    }

  }
}


/* ==========================================================
   SEND SCREENING REQUEST
   ========================================================== */

async function sendScreeningRequest(
  jobDescription,
  files
) {

  const s =
    getSettings();


  /* ---------------------------------------
     STEP 1:
     Create screening
     --------------------------------------- */

  const created =
    await apiRequest(
      CONFIG.ENDPOINTS.createScreening(),
      {

        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({

          jobDescription,

          options: {

            minMatchScore:
              s.minScore,

            skillSensitivity:
              s.sensitivity,

            aiExplanation:
              s.aiExplanation,

          },

        }),

      }
    );


  if (!created.screeningId) {

    throw new Error(
      "Backend did not return a screening ID."
    );

  }


  /* ---------------------------------------
     STEP 2:
     Upload resumes
     --------------------------------------- */

  await uploadResumes(
    created.screeningId,
    files
  );


  return created.screeningId;
}


/* ----------------------------------------------------------
   UPLOAD RESUMES
   ---------------------------------------------------------- */

async function uploadResumes(
  screeningId,
  files
) {

  const form =
    new FormData();


  files.forEach(
    (file) => {

      form.append(
        "resumes",
        file,
        file.name
      );

    }
  );


  return apiRequest(
    CONFIG.ENDPOINTS.uploadResumes(
      screeningId
    ),
    {
      method: "POST",
      body: form
    }
  );
}


/* ==========================================================
   7. PROCESSING
   ========================================================== */

const STEP_KEYS = [

  "readingJobDescription",

  "uploadingCvs",

  "extractingInformation",

  "matchingSkills",

  "calculatingScore",

  "generatingExplanation",

];


const STATE_LABELS = {

  pending:
    "Waiting",

  active:
    "In progress",

  done:
    "Done",

  error:
    "Failed",

};


/* ----------------------------------------------------------
   INITIALIZE PROCESSING
   ---------------------------------------------------------- */

function initProcessing() {

  const id =
    currentScreeningId();


  if (!id) {

    const processContent =
      $("#processContent");

    const noScreening =
      $("#noScreening");


    if (processContent) {
      processContent.classList.add(
        "hidden"
      );
    }


    if (noScreening) {
      noScreening.classList.remove(
        "hidden"
      );
    }


    return;
  }


  updateProcessingStatus({
    steps: {}
  });


  pollStatus(id);
}


/* ----------------------------------------------------------
   UPDATE PROCESSING STATUS
   ---------------------------------------------------------- */

function updateProcessingStatus(data) {

  const steps =
    data.steps || {};


  let doneCount = 0;


  STEP_KEYS.forEach(
    (key) => {

      const li =
        $(`.step[data-step="${key}"]`);


      if (!li) {
        return;
      }


      const state =
        STATE_LABELS[steps[key]]
          ? steps[key]
          : "pending";


      li.classList.remove(
        "active",
        "done",
        "error"
      );


      if (state !== "pending") {

        li.classList.add(
          state
        );

      }


      const stateEl =
        $(".step-state", li);


      if (stateEl) {

        stateEl.textContent =
          STATE_LABELS[state];

      }


      const dot =
        $(".step-dot", li);


      if (dot) {

        dot.innerHTML =
          state === "done"
            ? icon("check")
            : state === "error"
              ? icon("x")
              : "";

      }


      if (state === "done") {

        doneCount++;

      }

    }
  );


  const progress =
    $("#progressFill");


  if (progress) {

    progress.style.width =
      `${(
        doneCount /
        STEP_KEYS.length
      ) * 100}%`;

  }


  setText(
    "#statusMessage",
    data.message,
    ""
  );
}


/* ----------------------------------------------------------
   POLL STATUS
   ---------------------------------------------------------- */

async function pollStatus(id) {

  const banner =
    $("#processMessage");


  try {

    const data =
      await apiRequest(
        CONFIG.ENDPOINTS.status(id)
      );


    hideBanner(banner);


    updateProcessingStatus(
      data
    );


    /* -------------------------------
       SCREENING COMPLETE
       ------------------------------- */

    if (
      data.status ===
      "completed"
    ) {

      window.location.href =
        "candidate.html";

      return;

    }


    /* -------------------------------
       SCREENING FAILED
       ------------------------------- */

    if (
      data.status ===
      "failed"
    ) {

      showBanner(
        banner,
        data.message ||
          "Screening failed. Please try again.",
        "error"
      );


      const retry =
        $("#retryLink");


      if (retry) {

        retry.classList.remove(
          "hidden"
        );

      }


      return;
    }


  } catch (err) {

    showBanner(
      banner,
      err.message,
      err instanceof BackendNotConnectedError
        ? "info"
        : "error"
    );


    if (
      err instanceof
      BackendNotConnectedError
    ) {

      return;

    }

  }


  setTimeout(
    () => pollStatus(id),
    CONFIG.POLL_INTERVAL_MS
  );
}


/* ==========================================================
   8. CANDIDATE REVIEW
   ========================================================== */

let candidateTotal = null;


/* ----------------------------------------------------------
   INITIALIZE CANDIDATE
   ---------------------------------------------------------- */

function initCandidate() {

  const id =
    currentScreeningId();


  if (!id) {

    const reviewContent =
      $("#reviewContent");

    const noScreening =
      $("#noScreening");


    if (reviewContent) {

      reviewContent.classList.add(
        "hidden"
      );

    }


    if (noScreening) {

      noScreening.classList.remove(
        "hidden"
      );

    }


    return;

  }


  const params =
    new URLSearchParams(
      location.search
    );


  const storedIndex =
    sessionStorage.getItem(
      "resumeai.candidateIndex"
    );


  const index =
    parseInt(
      params.get("i") ??
      storedIndex ??
      "0",
      10
    ) || 0;


  const prevBtn =
    $("#prevBtn");

  const nextBtn =
    $("#nextBtn");


  if (prevBtn) {

    prevBtn.addEventListener(
      "click",
      () =>
        goToCandidate(
          index - 1
        )
    );

  }


  if (nextBtn) {

    nextBtn.addEventListener(
      "click",
      () =>
        goToCandidate(
          index + 1
        )
    );

  }


  loadCandidate(index);
}


/* ----------------------------------------------------------
   GO TO CANDIDATE
   ---------------------------------------------------------- */

function goToCandidate(index) {

  if (
    candidateTotal !== null &&
    index >= candidateTotal
  ) {

    window.location.href =
      "summary.html";

    return;
  }


  if (index < 0) {
    return;
  }


  sessionStorage.setItem(
    "resumeai.candidateIndex",
    String(index)
  );


  history.replaceState(
    null,
    "",
    `candidate.html?i=${index}`
  );


  initCandidateIndex(index);
}


/* ----------------------------------------------------------
   INITIALIZE CANDIDATE INDEX
   ---------------------------------------------------------- */

function initCandidateIndex(index) {

  const prevOld =
    $("#prevBtn");

  const nextOld =
    $("#nextBtn");


  if (!prevOld || !nextOld) {
    return;
  }


  const prev =
    prevOld.cloneNode(true);

  const next =
    nextOld.cloneNode(true);


  prevOld.replaceWith(prev);

  nextOld.replaceWith(next);


  prev.addEventListener(
    "click",
    () =>
      goToCandidate(
        index - 1
      )
  );


  next.addEventListener(
    "click",
    () =>
      goToCandidate(
        index + 1
      )
  );


  loadCandidate(index);
}


/* ----------------------------------------------------------
   LOAD CANDIDATE
   ---------------------------------------------------------- */

async function loadCandidate(index) {

  const banner =
    $("#reviewMessage");


  const prevBtn =
    $("#prevBtn");


  if (prevBtn) {

    prevBtn.disabled =
      index <= 0;

  }


  try {

    const candidate =
      await apiRequest(
        CONFIG.ENDPOINTS.candidate(
          currentScreeningId(),
          index
        )
      );


    hideBanner(banner);


    candidateTotal =
      typeof candidate.total ===
      "number"
        ? candidate.total
        : null;


    renderCandidate(
      candidate,
      index
    );


  } catch (err) {

    showBanner(
      banner,
      err.message,
      err instanceof BackendNotConnectedError
        ? "info"
        : "error"
    );

  }
}


/* ----------------------------------------------------------
   RENDER CHIPS
   ---------------------------------------------------------- */

function renderChips(
  container,
  items,
  cls,
  emptyText
) {

  if (!container) {
    return;
  }


  container.innerHTML = "";


  if (
    !Array.isArray(items) ||
    !items.length
  ) {

    container.innerHTML =
      `<span class="empty-inline">
        ${emptyText}
      </span>`;

    return;
  }


  items.forEach(
    (skill) => {

      const chip =
        document.createElement(
          "span"
        );


      chip.className =
        `chip ${cls}`;


      chip.textContent =
        skill;


      container.appendChild(
        chip
      );

    }
  );
}


/* ==========================================================
   RENDER CANDIDATE
   ========================================================== */

function renderCandidate(
  c,
  index
) {

  setText(
    "#candName",
    c.name,
    "Candidate Name"
  );


  setText(
    "#candRole",
    c.role,
    "Job Role"
  );


  setText(
    "#candExperience",
    c.experience
  );


  setText(
    "#candLocation",
    c.location
  );


  setText(
    "#candAvatar",
    initials(c.name)
  );


  /* ---------------------------------------
     SCORE
     --------------------------------------- */

  const score =
    Number(c.matchScore);


  const hasScore =
    Number.isFinite(score);


  setText(
    "#candScore",
    hasScore
      ? `${score}%`
      : "—"
  );


  const scoreRing =
    $("#scoreRing");


  if (scoreRing) {

    scoreRing.style.setProperty(
      "--pct",
      hasScore
        ? Math.max(
            0,
            Math.min(
              100,
              score
            )
          )
        : 0
    );

  }


  /* ---------------------------------------
     MATCHED SKILLS
     --------------------------------------- */

  renderChips(
    $("#matchedSkills"),
    c.matchedSkills,
    "chip-matched",
    "No matched skills returned."
  );


  /* ---------------------------------------
     MISSING SKILLS
     --------------------------------------- */

  renderChips(
    $("#missingSkills"),
    c.missingSkills,
    "chip-missing",
    "No missing skills returned."
  );


  /* ---------------------------------------
     COUNTS
     --------------------------------------- */

  setText(
    "#matchedCount",
    Array.isArray(c.matchedSkills)
      ? c.matchedSkills.length
      : "",
    ""
  );


  setText(
    "#missingCount",
    Array.isArray(c.missingSkills)
      ? c.missingSkills.length
      : "",
    ""
  );


  /* ---------------------------------------
     EXPERIENCE
     --------------------------------------- */

  setText(
    "#expSummary",
    c.experienceSummary,
    "No experience details returned."
  );


  /* ---------------------------------------
     AI EXPLANATION
     --------------------------------------- */

  setText(
    "#aiExplanation",
    c.explanation,
    "No explanation returned."
  );


  /* ---------------------------------------
     CANDIDATE COUNTER
     --------------------------------------- */

  const total =
    candidateTotal;


  setText(
    "#candCounter",
    total
      ? `Candidate ${index + 1} of ${total}`
      : `Candidate ${index + 1}`
  );


  /* ---------------------------------------
     NEXT BUTTON
     --------------------------------------- */

  const next =
    $("#nextBtn");


  if (next) {

    const isLast =
      total !== null &&
      index + 1 >= total;


    next.innerHTML =
      `${
        isLast
          ? "View Summary"
          : "Next Candidate"
      } ${icon("arrow-right")}`;

  }


  /* ---------------------------------------
     RESUME BUTTON
     --------------------------------------- */

  const resumeBtn =
    $("#resumeBtn");


  if (!resumeBtn) {
    return;
  }


  resumeBtn.disabled =
    !c.resumeUrl;


  resumeBtn.onclick =
    () => {

      if (!c.resumeUrl) {
        return;
      }


      /*
        Backend returns:

        /api/files/{screening_id}/{filename}

        This is a relative URL.

        We must add the Flask API base URL.
      */

      const resumeUrl =
        c.resumeUrl.startsWith(
          "http://"
        ) ||
        c.resumeUrl.startsWith(
          "https://"
        )
          ? c.resumeUrl
          : CONFIG.API_BASE +
            c.resumeUrl;


      window.open(
        resumeUrl,
        "_blank",
        "noopener,noreferrer"
      );

    };
}


/* ==========================================================
   9. SUMMARY
   ========================================================== */


/* ----------------------------------------------------------
   INITIALIZE SUMMARY
   ---------------------------------------------------------- */

function initSummary() {

  if (!currentScreeningId()) {

    const summaryContent =
      $("#summaryContent");

    const noScreening =
      $("#noScreening");


    if (summaryContent) {

      summaryContent.classList.add(
        "hidden"
      );

    }


    if (noScreening) {

      noScreening.classList.remove(
        "hidden"
      );

    }


    return;
  }


  loadSummary();
}


/* ----------------------------------------------------------
   LOAD SUMMARY
   ---------------------------------------------------------- */

async function loadSummary() {

  const banner =
    $("#summaryMessage");


  try {

    const data =
      await apiRequest(
        CONFIG.ENDPOINTS.summary(
          currentScreeningId()
        )
      );


    hideBanner(banner);


    renderSummary(data);


  } catch (err) {

    showBanner(
      banner,
      err.message,
      err instanceof BackendNotConnectedError
        ? "info"
        : "error"
    );

  }
}


/* ----------------------------------------------------------
   RENDER SUMMARY
   ---------------------------------------------------------- */

function renderSummary(data) {

  const pct = (v) => {

    return (
      Number.isFinite(
        Number(v)
      ) &&
      v !== null &&
      v !== undefined
    )
      ? `${v}%`
      : "—";

  };


  setText(
    "#statTotal",
    data.totalCandidates
  );


  setText(
    "#statStrong",
    data.strongMatches
  );


  setText(
    "#statAverage",
    pct(data.averageMatch)
  );


  setText(
    "#statTop",
    pct(data.topMatch)
  );


  const list =
    $("#resultList");


  if (!list) {
    return;
  }


  list.innerHTML = "";


  const candidates =
    Array.isArray(
      data.candidates
    )
      ? data.candidates
      : [];


  if (!candidates.length) {

    list.innerHTML =
      '<li class="empty-state">' +
      'No candidates returned.' +
      '</li>';

    return;
  }


  candidates.forEach(
    (c, i) => {

      const li =
        document.createElement(
          "li"
        );


      li.innerHTML = `

        <a
          class="result-row"
          href="candidate.html?i=${i}"
        >

          <span class="rank">
            ${i + 1}
          </span>

          <span class="result-avatar"></span>

          <span class="result-main">

            <div class="result-name"></div>

            <div class="result-role"></div>

          </span>

          <span class="score-pill"></span>

          ${icon(
            "chevron-right"
          )}

        </a>

      `;


      $(".result-avatar", li)
        .textContent =
        initials(c.name);


      $(".result-name", li)
        .textContent =
        c.name ||
        "Unnamed candidate";


      $(".result-role", li)
        .textContent =
        c.role || "";


      $(".score-pill", li)
        .textContent =
        pct(c.matchScore);


      list.appendChild(li);

    }
  );
}


/* ==========================================================
   10. SETTINGS
   ========================================================== */


/* ----------------------------------------------------------
   INITIALIZE SETTINGS
   ---------------------------------------------------------- */

function initSettings() {

  fillSettingsForm(
    getSettings()
  );


  const range =
    $("#minScore");


  if (range) {

    range.addEventListener(
      "input",
      () => {

        setText(
          "#minScoreValue",
          `${range.value}%`
        );

      }
    );

  }


  $$('input[name="theme"]')
    .forEach(
      (r) => {

        r.addEventListener(
          "change",
          () =>
            applyTheme(
              r.value
            )
        );

      }
    );


  const saveBtn =
    $("#saveBtn");


  if (saveBtn) {

    saveBtn.addEventListener(
      "click",
      saveSettings
    );

  }


  const resetBtn =
    $("#resetBtn");


  if (resetBtn) {

    resetBtn.addEventListener(
      "click",
      () => {

        localStorage.removeItem(
          "resumeai.settings"
        );


        fillSettingsForm(
          {
            ...DEFAULT_SETTINGS
          }
        );


        applyTheme(
          DEFAULT_SETTINGS.theme
        );


        renderUserChip();


        showToast(
          "Settings reset to defaults"
        );

      }
    );

  }
}


/* ----------------------------------------------------------
   FILL SETTINGS FORM
   ---------------------------------------------------------- */

function fillSettingsForm(s) {

  const setName =
    $("#setName");

  const setEmail =
    $("#setEmail");

  const minScore =
    $("#minScore");

  const sensitivity =
    $("#sensitivity");

  const aiExplanation =
    $("#aiExplanation");

  const maxFileMB =
    $("#maxFileMB");

  const notifyComplete =
    $("#notifyComplete");

  const notifyErrors =
    $("#notifyErrors");


  if (setName) {
    setName.value =
      s.name || "";
  }


  if (setEmail) {
    setEmail.value =
      s.email || "";
  }


  if (minScore) {

    minScore.value =
      s.minScore;

  }


  setText(
    "#minScoreValue",
    `${s.minScore}%`
  );


  if (sensitivity) {

    sensitivity.value =
      s.sensitivity;

  }


  if (aiExplanation) {

    aiExplanation.checked =
      s.aiExplanation;

  }


  if (maxFileMB) {

    maxFileMB.value =
      s.maxFileMB;

  }


  $$('input[name="format"]')
    .forEach(
      (cb) => {

        cb.checked =
          s.formats.includes(
            cb.value
          );

      }
    );


  $$('input[name="theme"]')
    .forEach(
      (r) => {

        r.checked =
          r.value === s.theme;

      }
    );


  if (notifyComplete) {

    notifyComplete.checked =
      s.notifyComplete;

  }


  if (notifyErrors) {

    notifyErrors.checked =
      s.notifyErrors;

  }
}


/* ----------------------------------------------------------
   SAVE SETTINGS
   ---------------------------------------------------------- */

function saveSettings() {

  const banner =
    $("#settingsMessage");


  const formats =
    $$('input[name="format"]:checked')
      .map(
        (cb) => cb.value
      );


  const maxFileMB =
    parseFloat(
      $("#maxFileMB")?.value
    );


  const problems = [];


  if (!formats.length) {

    problems.push(
      "Choose at least one allowed CV format."
    );

  }


  if (
    !(maxFileMB > 0) ||
    maxFileMB > 100
  ) {

    problems.push(
      "Maximum file size must be between 1 and 100 MB."
    );

  }


  if (problems.length) {

    showBanner(
      banner,
      "Settings were not saved:",
      "error",
      problems
    );

    return;
  }


  hideBanner(banner);


  const themeRadio =
    $('input[name="theme"]:checked');


  const settings = {

    name:
      $("#setName")?.value.trim() ||
      "",

    email:
      $("#setEmail")?.value.trim() ||
      "",

    minScore:
      parseInt(
        $("#minScore")?.value,
        10
      ) || 60,

    sensitivity:
      $("#sensitivity")?.value ||
      "balanced",

    aiExplanation:
      $("#aiExplanation")?.checked ??
      true,

    maxFileMB,

    formats,

    theme:
      themeRadio?.value ||
      "light",

    notifyComplete:
      $("#notifyComplete")?.checked ??
      true,

    notifyErrors:
      $("#notifyErrors")?.checked ??
      true,

  };


  localStorage.setItem(
    "resumeai.settings",
    JSON.stringify(settings)
  );


  applyTheme(
    settings.theme
  );


  renderUserChip();


  showToast(
    "Settings saved"
  );
}


/* ==========================================================
   11. BOOT
   ========================================================== */

document.addEventListener(
  "DOMContentLoaded",
  () => {

    /* ---------------------------------------
       Apply saved theme
       --------------------------------------- */

    applyTheme(
      getSettings().theme
    );


    /* ---------------------------------------
       Sidebar
       --------------------------------------- */

    renderSidebar();


    /* ---------------------------------------
       User information
       --------------------------------------- */

    renderUserChip();


    /* ---------------------------------------
       SVG icons
       --------------------------------------- */

    hydrateIcons();


    /* ---------------------------------------
       Determine current page
       --------------------------------------- */

    const page =
      document.body.dataset.page;


    /* ---------------------------------------
       Dashboard
       --------------------------------------- */

    if (
      page === "dashboard"
    ) {

      initDashboard();

    }


    /* ---------------------------------------
       Screening processing
       --------------------------------------- */

    if (
      page === "screening"
    ) {

      initProcessing();

    }


    /* ---------------------------------------
       Candidate
       --------------------------------------- */

    if (
      page === "candidate"
    ) {

      initCandidate();

    }


    /* ---------------------------------------
       Summary
       --------------------------------------- */

    if (
      page === "summary"
    ) {

      initSummary();

    }


    /* ---------------------------------------
       Settings
       --------------------------------------- */

    if (
      page === "settings"
    ) {

      initSettings();

    }

  }
);  