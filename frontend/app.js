const API_BASE = "/api";
const STATUS = document.getElementById("status");
const form = document.getElementById("transaction-form");
const refreshButton = document.getElementById("refresh-data");

const selects = {
  source: document.getElementById("source-account"),
  destination: document.getElementById("destination-account"),
  budget: document.getElementById("budget"),
  category: document.getElementById("category"),
  tags: document.getElementById("tag-options"),
};


function safeName(item, fallback = "未命名") {
  const raw = item?.name || item?.attributes?.name || "";
  const trimmed = typeof raw === "string" ? raw.trim() : "";
  return trimmed || fallback;
}

function accountLabel(item) {
  const name = safeName(item, "未命名账户");
  const type = item?.type || item?.account_type || item?.attributes?.type;
  return type ? `${name} (${type})` : name;
}
function setTodayAsDefault() {
  const today = new Date();
  const offset = today.getTimezoneOffset();
  const localDate = new Date(today.getTime() - offset * 60 * 1000);
  document.getElementById("date").value = localDate.toISOString().split("T")[0];
}

async function fetchJSON(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    let message = `请求失败：${response.status}`;
    try {
      const data = await response.json();
      message = data.message || data.error || message;
    } catch (_) {
      /* ignore */
    }
    throw new Error(message);
  }
  return response.json();
}

function populateSelect(selectEl, items, { placeholder, getLabel, getValue }) {
  selectEl.innerHTML = "";
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    selectEl.appendChild(option);
  }

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = getValue(item);
    option.textContent = getLabel(item);
    selectEl.appendChild(option);
  });
}

function populateTagOptions(items, getLabel) {
  selects.tags.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = getLabel(item);
    selects.tags.appendChild(option);
  });
}

function normalizeResource(data) {
  if (!data) {
    return [];
  }
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data.data)) {
    return data.data.map((entry) => ({
      id: entry.id,
      ...(entry.attributes || {}),
    }));
  }
  return [];
}

async function loadAllData() {
  setStatus("正在加载数据…", "info");
  try {
    const [accounts, budgets, categories, tags] = await Promise.all([
      fetchJSON("/accounts"),
      fetchJSON("/budgets"),
      fetchJSON("/categories"),
      fetchJSON("/tags"),
    ]);

    const normalizedAccounts = normalizeResource(accounts);
    populateSelect(selects.source, normalizedAccounts, {
      placeholder: "请选择来源账户",
      getLabel: (item) => accountLabel(item),
      getValue: (item) => item.id,
    });
    populateSelect(selects.destination, normalizedAccounts, {
      placeholder: "请选择目标账户",
      getLabel: (item) => accountLabel(item),
      getValue: (item) => item.id,
    });

    populateSelect(selects.budget, normalizeResource(budgets), {
      placeholder: "不使用预算",
      getLabel: (item) => safeName(item),
      getValue: (item) => item.id,
    });

    populateSelect(selects.category, normalizeResource(categories), {
      placeholder: "不指定分类",
      getLabel: (item) => safeName(item),
      getValue: (item) => item.id,
    });

    populateTagOptions(normalizeResource(tags), (item) => safeName(item));
    setStatus("数据加载完成，可以开始记账啦！", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message || "加载数据时出现错误。", "error");
  }
}

function setStatus(message, type) {
  STATUS.textContent = message || "";
  STATUS.classList.remove("status--success", "status--error");
  if (type === "success") {
    STATUS.classList.add("status--success");
  } else if (type === "error") {
    STATUS.classList.add("status--error");
  }
}

async function submitTransaction(event) {
  event.preventDefault();
  setStatus("正在提交…", "info");

  const body = {
    description: document.getElementById("description").value.trim(),
    date: document.getElementById("date").value,
    amount: document.getElementById("amount").value,
    source_account_id: document.getElementById("source-account").value,
    destination_account_id: document.getElementById("destination-account").value,
    budget_id: document.getElementById("budget").value,
    category_id: document.getElementById("category").value,
    tags: document.getElementById("tags").value,
    notes: document.getElementById("notes").value,
    transaction_type: document.getElementById("transaction-type").value,
  };

  try {
    const response = await fetch(`${API_BASE}/transactions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "提交失败，请稍后再试。");
    }

    form.reset();
    setTodayAsDefault();
    setStatus("提交成功，已写入 Firefly III！", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message || "提交失败，请稍后再试。", "error");
  }
}

refreshButton.addEventListener("click", loadAllData);
form.addEventListener("submit", submitTransaction);

setTodayAsDefault();
loadAllData();
