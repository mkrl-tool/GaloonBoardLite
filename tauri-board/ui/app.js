// ガルーン行動予定表 (Tauri + Web フロントエンド)

const MIN_ROWS = 12;
let currentDate = new Date();
let currentMembers = [];
let appConfig = {
  garoon_url: "http://garoon.example.local/cgi-bin/cbgrn/grn.cgi",
  username: "",
  password: "",
  use_basic_auth: false,
  basic_username: "",
  basic_password: "",
  verify_ssl: true,
  refresh_interval_minutes: 20,
  mock_mode: true
};

// Tauri IPCが利用可能かチェック
const isTauri = typeof window.__TAURI__ !== "undefined";

async function invokeTauri(cmd, args = {}) {
  if (isTauri && window.__TAURI__.invoke) {
    return await window.__TAURI__.invoke(cmd, args);
  }
  // ブラウザ単体実行時のモックフォールバック
  return mockInvoke(cmd, args);
}

// 初期化
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  updateDateLabel();
  await loadSettings();
  await refreshData();
  startAutoRefresh();
});

function setupEventListeners() {
  document.getElementById("btn-prev").addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() - 1);
    updateDateLabel();
    refreshData();
  });

  document.getElementById("btn-next").addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() + 1);
    updateDateLabel();
    refreshData();
  });

  document.getElementById("btn-today").addEventListener("click", () => {
    currentDate = new Date();
    updateDateLabel();
    refreshData();
  });

  document.getElementById("btn-refresh").addEventListener("click", refreshData);
  document.getElementById("btn-pin").addEventListener("click", togglePin);
  document.getElementById("btn-settings").addEventListener("click", openSettings);

  // モーダル
  document.getElementById("modal-close-btn").addEventListener("click", closeModal);
  document.getElementById("modal-ok-btn").addEventListener("click", closeModal);
  document.getElementById("settings-close-btn").addEventListener("click", closeSettings);
  document.getElementById("settings-cancel-btn").addEventListener("click", closeSettings);
  document.getElementById("settings-save-btn").addEventListener("click", saveSettings);
  document.getElementById("btn-test-conn").addEventListener("click", testConnection);

  document.getElementById("cfg-use-basic").addEventListener("change", (e) => {
    const grp = document.getElementById("basic-auth-group");
    if (e.target.checked) grp.classList.remove("hidden");
    else grp.classList.add("hidden");
  });
}

function updateDateLabel() {
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const m = currentDate.getMonth() + 1;
  const d = currentDate.getDate();
  const w = weekdays[currentDate.getDay()];
  document.getElementById("date-label").textContent = `${m}月 ${d}日 (${w})`;
}

async function refreshData() {
  const statusEl = document.getElementById("footer-status");
  statusEl.textContent = "更新中...";

  const dateStr = currentDate.toISOString().split("T")[0];
  try {
    currentMembers = await invokeTauri("get_board_data", { date: dateStr });
    renderRows(currentMembers);
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    statusEl.textContent = `更新: ${hh}:${mm}${appConfig.mock_mode ? " (デモ)" : ""}`;
  } catch (err) {
    statusEl.textContent = "取得エラー";
    console.error("Refresh error:", err);
  }
}

function renderRows(members) {
  const container = document.getElementById("board-rows");
  container.innerHTML = "";

  // メンバー行の描画
  members.forEach((m) => {
    const row = document.createElement("div");
    row.className = "board-row";

    const inkClass = getInkClass(m.board_ink_color);

    row.innerHTML = `
      <div class="cell-name">${escapeHtml(m.user.name)}</div>
      <div class="cell-dest ${inkClass}">${escapeHtml(m.destination_text)}</div>
      <div class="cell-time ${inkClass}">${escapeHtml(m.return_time_text)}</div>
    `;

    row.addEventListener("click", () => openEventModal(m));
    container.appendChild(row);
  });

  // 空欄行でMIN_ROWSまで埋める（ホワイトボードの罫線のみ）
  const emptyNeeded = Math.max(0, MIN_ROWS - members.length);
  for (let i = 0; i < emptyNeeded; i++) {
    const emptyRow = document.createElement("div");
    emptyRow.className = "board-row";
    emptyRow.innerHTML = `
      <div class="cell-name"></div>
      <div class="cell-dest"></div>
      <div class="cell-time empty-colon">:</div>
    `;
    container.appendChild(emptyRow);
  }
}

function getInkClass(hex) {
  if (hex === "#dc2626") return "ink-red";
  if (hex === "#2563eb") return "ink-blue";
  if (hex === "#0284c7") return "ink-cyan";
  if (hex === "#71717a") return "ink-gray";
  return "ink-black";
}

function openEventModal(member) {
  const ev = member.current_event || (member.today_events && member.today_events[0]);
  if (!ev) return;

  document.getElementById("modal-menu-badge").textContent = ev.event_menu || member.current_status;
  document.getElementById("modal-title").textContent = ev.subject || "（無題）";
  document.getElementById("modal-time").textContent = ev.time_range_str || "終日";
  document.getElementById("modal-attendees").textContent = (ev.attendees && ev.attendees.length > 0) ? ev.attendees.join(", ") : member.user.name;
  document.getElementById("modal-notes").textContent = ev.notes || "（メモはありません）";

  document.getElementById("event-modal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("event-modal").classList.add("hidden");
}

async function loadSettings() {
  try {
    appConfig = await invokeTauri("load_config");
  } catch (e) {
    console.warn("Failed to load settings from Tauri:", e);
  }
}

function openSettings() {
  document.getElementById("cfg-mock-mode").checked = appConfig.mock_mode;
  document.getElementById("cfg-url").value = appConfig.garoon_url || "";
  document.getElementById("cfg-username").value = appConfig.username || "";
  document.getElementById("cfg-password").value = appConfig.password || "";
  document.getElementById("cfg-verify-ssl").checked = appConfig.verify_ssl;
  document.getElementById("cfg-use-basic").checked = appConfig.use_basic_auth;
  document.getElementById("cfg-basic-user").value = appConfig.basic_username || "";
  document.getElementById("cfg-basic-pass").value = appConfig.basic_password || "";
  document.getElementById("cfg-interval").value = String(appConfig.refresh_interval_minutes || 3);

  const basicGrp = document.getElementById("basic-auth-group");
  if (appConfig.use_basic_auth) basicGrp.classList.remove("hidden");
  else basicGrp.classList.add("hidden");

  document.getElementById("test-result-msg").textContent = "";
  document.getElementById("settings-modal").classList.remove("hidden");
}

function closeSettings() {
  document.getElementById("settings-modal").classList.add("hidden");
}

async function saveSettings() {
  appConfig.mock_mode = document.getElementById("cfg-mock-mode").checked;
  appConfig.garoon_url = document.getElementById("cfg-url").value.trim();
  appConfig.username = document.getElementById("cfg-username").value.trim();
  appConfig.password = document.getElementById("cfg-password").value;
  appConfig.verify_ssl = document.getElementById("cfg-verify-ssl").checked;
  appConfig.use_basic_auth = document.getElementById("cfg-use-basic").checked;
  appConfig.basic_username = document.getElementById("cfg-basic-user").value.trim();
  appConfig.basic_password = document.getElementById("cfg-basic-pass").value;
  appConfig.refresh_interval_minutes = parseInt(document.getElementById("cfg-interval").value, 10);

  await invokeTauri("save_config", { config: appConfig });
  closeSettings();
  startAutoRefresh();
  refreshData();
}

async function testConnection() {
  const resultMsg = document.getElementById("test-result-msg");
  resultMsg.textContent = "テスト中...";
  resultMsg.style.color = "#64748b";

  const tempCfg = {
    garoon_url: document.getElementById("cfg-url").value.trim(),
    username: document.getElementById("cfg-username").value.trim(),
    password: document.getElementById("cfg-password").value,
    use_basic_auth: document.getElementById("cfg-use-basic").checked,
    basic_username: document.getElementById("cfg-basic-user").value.trim(),
    basic_password: document.getElementById("cfg-basic-pass").value,
    verify_ssl: document.getElementById("cfg-verify-ssl").checked,
    mock_mode: document.getElementById("cfg-mock-mode").checked,
  };

  try {
    const [ok, msg] = await invokeTauri("test_connection", { config: tempCfg });
    resultMsg.textContent = ok ? "✅ " + msg : "❌ " + msg;
    resultMsg.style.color = ok ? "#16a34a" : "#dc2626";
  } catch (err) {
    resultMsg.textContent = "❌ " + String(err);
    resultMsg.style.color = "#dc2626";
  }
}

let refreshTimer = null;
function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  const minutes = appConfig.refresh_interval_minutes || 3;
  if (minutes > 0) {
    refreshTimer = setInterval(refreshData, minutes * 60 * 1000);
  }
}

let isAlwaysOnTop = false;
async function togglePin() {
  isAlwaysOnTop = !isAlwaysOnTop;
  const pinBtn = document.getElementById("btn-pin");
  pinBtn.style.color = isAlwaysOnTop ? "#0284c7" : "#64748b";
  if (isTauri) {
    await invokeTauri("set_always_on_top", { alwaysOnTop: isAlwaysOnTop });
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ブラウザ単体テスト時のモック
function mockInvoke(cmd, args) {
  if (cmd === "load_config") {
    return Promise.resolve(appConfig);
  }
  if (cmd === "save_config") {
    appConfig = args.config;
    return Promise.resolve(true);
  }
  if (cmd === "test_connection") {
    return Promise.resolve([true, "接続成功（ブラウザテスト）"]);
  }
  if (cmd === "get_board_data") {
    return Promise.resolve([
      {
        user: { id: "1", name: "山田 太郎" },
        current_status: "外出",
        destination_text: "外出 株式会社ABC様",
        return_time_text: "17:30",
        board_ink_color: "#dc2626",
        current_event: {
          subject: "株式会社ABC様 定例打ち合わせ",
          event_menu: "外出",
          time_range_str: "10:00 - 17:30",
          notes: "新システム導入の進捗報告および今後のスケジュール調整",
          attendees: ["山田 太郎", "佐藤 美咲"]
        }
      },
      {
        user: { id: "2", name: "佐藤 美咲" },
        current_status: "テレワーク",
        destination_text: "在宅勤務 (WebMTG)",
        return_time_text: "終日",
        board_ink_color: "#0284c7",
        current_event: {
          subject: "終日在宅勤務",
          event_menu: "テレワーク",
          time_range_str: "終日",
          notes: "連絡はTeamsにてお願いします。",
          attendees: ["佐藤 美咲"]
        }
      },
      {
        user: { id: "3", name: "鈴木 一郎" },
        current_status: "在席",
        destination_text: "在席 (次 14:00〜)",
        return_time_text: "―",
        board_ink_color: "#111827",
        current_event: null
      },
      {
        user: { id: "4", name: "高橋 健太" },
        current_status: "休暇",
        destination_text: "有給休暇",
        return_time_text: "終日",
        board_ink_color: "#71717a",
        current_event: {
          subject: "有給休暇（私用）",
          event_menu: "休暇",
          time_range_str: "終日",
          notes: "終日不在",
          attendees: ["高橋 健太"]
        }
      },
      {
        user: { id: "5", name: "伊藤 翔太" },
        current_status: "外出",
        destination_text: "品川DC保守 (直帰)",
        return_time_text: "直帰",
        board_ink_color: "#dc2626",
        current_event: {
          subject: "データセンター機器保守立ち会い",
          event_menu: "外出",
          time_range_str: "14:30 - 18:00",
          notes: "品川DC / 完了後そのまま直帰予定",
          attendees: ["伊藤 翔太"]
        }
      },
      {
        user: { id: "6", name: "渡辺 裕子" },
        current_status: "会議中",
        destination_text: "面談 (応接1)",
        return_time_text: "12:00",
        board_ink_color: "#2563eb",
        current_event: {
          subject: "採用面接（エンジニア候補者）",
          event_menu: "面談",
          time_range_str: "11:00 - 12:00",
          notes: "応接室1",
          attendees: ["渡辺 裕子"]
        }
      }
    ]);
  }
  return Promise.resolve(null);
}
