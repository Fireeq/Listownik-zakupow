const API_URL = "http://127.0.0.1:5000/api";
const productVisuals = [
  { name: "milk", pattern: /\b(mleko|mleka|milk)\b/ },
  { name: "bread", pattern: /\b(chleb\w*|pieczywo|bulki|bulka|bagiet\w*|bread)\b/ },
  { name: "apple", pattern: /\b(jablk\w*|apples?)\b/ },
  { name: "banana", pattern: /\b(banan\w*)\b/ },
  { name: "carrot", pattern: /\b(marchew\w*|carrots?)\b/ },
  { name: "tomato", pattern: /\b(pomidor\w*|tomato\w*)\b/ },
  { name: "eggs", pattern: /\b(jajk\w*|jaja|eggs?)\b/ },
  { name: "cheese", pattern: /\b(ser|sera|cheese)\b/ },
];
const state = {
  lists: [],
  activeList: null,
  filter: "all",
  busy: false,
  loaded: false,
  pendingDelete: null,
};
let toastTimeout;

function getElement(id) {
  return document.getElementById(id);
}

async function request(path, method = "GET", body) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(10000),
      cache: "no-store",
    });
  } catch {
    throw new Error("Nie można połączyć się z backendem. Sprawdź, czy jest uruchomiony, i spróbuj ponownie.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) throw new Error(data?.error || "Nie udało się wykonać operacji.");
  return data;
}

function setBusy(value) {
  state.busy = value;
  getElement("main-content").setAttribute("aria-busy", String(value));
  document.querySelectorAll("button, input").forEach((control) => {
    control.disabled = value || control.dataset.unavailable === "true";
  });
}

function clearErrors() {
  getElement("page-error").hidden = true;
  document.querySelectorAll(".form-error").forEach((element) => {
    element.hidden = true;
    element.textContent = "";
  });
}

function showError(message) {
  const dialogError = document.querySelector("dialog[open] .form-error");
  if (dialogError) {
    dialogError.textContent = message;
    dialogError.hidden = false;
  } else {
    getElement("page-error-message").textContent = message;
    getElement("page-error").hidden = false;
  }
}

function showToast(message) {
  clearTimeout(toastTimeout);
  getElement("toast").textContent = message;
  getElement("toast").hidden = false;
  toastTimeout = setTimeout(() => { getElement("toast").hidden = true; }, 3500);
}

async function run(action, message = "", focusId = "") {
  if (state.busy) return;
  let nextFocusId = document.activeElement.id;
  setBusy(true);
  clearErrors();
  try {
    await action();
    if (message) showToast(message);
    nextFocusId = focusId || nextFocusId;
  } catch (error) {
    if (state.activeList) renderItems();
    showError(error.message);
  } finally {
    getElement("loading").hidden = true;
    setBusy(false);
    getElement(nextFocusId)?.focus();
  }
}

async function refreshLists(preferredId = state.activeList?.id) {
  const lists = await request("/lists");
  const selectedList = lists.find((list) => list.id === preferredId) || lists[0];
  const activeList = selectedList ? await request(`/lists/${selectedList.id}`) : null;
  if (state.activeList?.id !== activeList?.id) state.filter = "all";
  state.lists = lists;
  state.activeList = activeList;
  state.loaded = true;
  render();
}

function renderLists() {
  const fragment = document.createDocumentFragment();
  for (const list of state.lists) {
    const entry = getElement("list-template").content.cloneNode(true);
    const button = entry.querySelector("button");
    const remaining = list.total_count - list.purchased_count;
    button.id = `list-choice-${list.id}`;
    button.dataset.listId = list.id;
    button.setAttribute("aria-current", String(list.id === state.activeList?.id));
    entry.querySelector(".list-name").textContent = list.name;
    entry.querySelector(".list-meta").textContent = list.total_count === 0
      ? "Pusta lista" : remaining === 0 ? "Wszystko kupione" : `${remaining} do kupienia`;
    entry.querySelector(".list-count").textContent = list.total_count;
    fragment.append(entry);
  }
  getElement("shopping-lists").replaceChildren(fragment);
  getElement("list-count").textContent = state.lists.length;
  getElement("header-pending-count").textContent = state.lists.reduce(
    (total, list) => total + list.total_count - list.purchased_count, 0,
  );
  getElement("lists-empty").hidden = !state.loaded || state.lists.length > 0;
}

function getProductVisual(name) {
  const normalizedName = name.toLocaleLowerCase("pl").normalize("NFD").replace(/\p{Diacritic}/gu, "").replace(/ł/g, "l");
  return productVisuals.find((visual) => visual.pattern.test(normalizedName))?.name || "other";
}

function prepareItemActions(entry, item) {
  const labels = { edit: "Edytuj", delete: "Usuń", decrease: "Zmniejsz ilość", increase: "Zwiększ ilość" };
  for (const button of entry.querySelectorAll("button")) {
    const action = button.dataset.action;
    button.id = `item-${action}-${item.id}`;
    button.setAttribute("aria-label", `${labels[action]}: ${item.name}`);
    button.dataset.unavailable = String(
      (action === "decrease" && item.quantity === 1) || (action === "increase" && item.quantity === 999),
    );
    button.disabled = state.busy || button.dataset.unavailable === "true";
  }
}

function renderSummary() {
  const items = state.activeList.items;
  const purchased = items.filter((item) => item.is_purchased).length;
  const percent = items.length ? Math.round(purchased / items.length * 100) : 0;
  getElement("active-list-name").textContent = state.activeList.name;
  getElement("progress-text").textContent = `Kupione: ${purchased} z ${items.length}`;
  getElement("progress-percent").textContent = `${percent}%`;
  getElement("shopping-progress").max = items.length || 1;
  getElement("shopping-progress").value = purchased;
  getElement("all-count").textContent = items.length;
  getElement("pending-count").textContent = items.length - purchased;
  getElement("purchased-count").textContent = purchased;
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.filter === state.filter));
  });
}

function renderItems() {
  const items = state.activeList.items.filter((item) => {
    if (state.filter === "pending") return !item.is_purchased;
    if (state.filter === "purchased") return item.is_purchased;
    return true;
  });
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    const entry = getElement("item-template").content.cloneNode(true);
    const row = entry.querySelector("li");
    row.dataset.itemId = item.id;
    row.classList.toggle("is-purchased", item.is_purchased);
    const checkbox = entry.querySelector("input");
    checkbox.id = `item-check-${item.id}`;
    checkbox.checked = item.is_purchased;
    checkbox.setAttribute("aria-label", `${item.is_purchased ? "Cofnij zakup" : "Oznacz jako kupione"}: ${item.name}`);
    entry.querySelector(".item-status").textContent = item.is_purchased ? "Kupione" : "Do kupienia";
    entry.querySelector(".product-photo").dataset.product = getProductVisual(item.name);
    entry.querySelector(".item-name").textContent = item.name;
    entry.querySelector(".item-quantity").textContent = `${item.quantity} szt.`;
    prepareItemActions(entry, item);
    fragment.append(entry);
  }
  getElement("items").replaceChildren(fragment);
  renderEmptyItems(items.length === 0);
}

function renderEmptyItems(isEmpty) {
  getElement("items-empty").hidden = !isEmpty;
  const noProducts = state.activeList.items.length === 0;
  const completed = !noProducts && state.filter === "pending";
  getElement("items-empty-icon").setAttribute("href", completed ? "#icon-check" : "#icon-list");
  getElement("items-empty-title").textContent = noProducts ? "Dodaj pierwszy produkt"
    : completed ? "Wszystko kupione!" : "Jeszcze nic nie jest kupione";
  getElement("items-empty-description").textContent = noProducts
    ? "Wpisz nazwę i ilość w formularzu powyżej."
    : completed ? "Gotowe. Wszystkie produkty z tej listy są już kupione."
      : "Odhacz produkt, aby pojawił się w tym widoku.";
}

function render() {
  renderLists();
  getElement("welcome").hidden = !state.loaded || Boolean(state.activeList);
  getElement("list-detail").hidden = !state.activeList;
  getElement("products-link").hidden = !state.activeList;
  if (state.activeList) {
    renderSummary();
    renderItems();
  }
  setBusy(state.busy);
}

function readName(inputId) {
  const input = getElement(inputId);
  const name = input.value.trim();
  input.setCustomValidity(name ? "" : "Wpisz nazwę. Sama spacja nie wystarczy.");
  return input.reportValidity() ? name : null;
}

function openListDialog(mode) {
  clearErrors();
  getElement("list-form").dataset.mode = mode;
  getElement("list-name").value = mode === "create" ? "" : state.activeList.name;
  getElement("list-name").setCustomValidity("");
  getElement("list-dialog-title").textContent = mode === "create" ? "Nowa lista zakupów" : "Zmień nazwę listy";
  getElement("save-list").textContent = mode === "create" ? "Utwórz listę" : "Zapisz zmiany";
  getElement("list-dialog").showModal();
  getElement("list-name").focus();
}

function saveList(event) {
  event.preventDefault();
  const name = readName("list-name");
  if (!name) return;
  const isNew = getElement("list-form").dataset.mode === "create";
  run(async () => {
    const list = await request(isNew ? "/lists" : `/lists/${state.activeList.id}`, isNew ? "POST" : "PATCH", { name });
    getElement("list-dialog").close();
    await refreshLists(list.id);
  }, isNew ? "Lista została utworzona." : "Nazwa listy została zmieniona.", "item-name");
}

function addItem(event) {
  event.preventDefault();
  const name = readName("item-name");
  if (!name) return;
  const quantity = getElement("item-quantity").valueAsNumber;
  run(async () => {
    await request(`/lists/${state.activeList.id}/items`, "POST", { name, quantity });
    getElement("add-item-form").reset();
    state.filter = "all";
    await refreshLists();
  }, "Produkt został dodany.", "item-name");
}

function openItemDialog(item) {
  clearErrors();
  getElement("edit-item-form").dataset.itemId = item.id;
  getElement("edit-item-name").value = item.name;
  getElement("edit-item-name").setCustomValidity("");
  getElement("edit-item-quantity").value = item.quantity;
  getElement("item-dialog").showModal();
}

function saveItem(event) {
  event.preventDefault();
  const name = readName("edit-item-name");
  if (!name) return;
  const itemId = getElement("edit-item-form").dataset.itemId;
  const quantity = getElement("edit-item-quantity").valueAsNumber;
  run(async () => {
    await request(`/lists/${state.activeList.id}/items/${itemId}`, "PATCH", { name, quantity });
    getElement("item-dialog").close();
    await refreshLists();
  }, "Produkt został zmieniony.", `item-edit-${itemId}`);
}

function openDeleteDialog(item = null) {
  clearErrors();
  state.pendingDelete = item
    ? { path: `/lists/${state.activeList.id}/items/${item.id}`, message: "Produkt został usunięty.", focusId: "item-name" }
    : { path: `/lists/${state.activeList.id}`, message: "Lista została usunięta.", focusId: "new-list" };
  getElement("delete-dialog-title").textContent = item ? "Usunąć produkt?" : "Usunąć listę?";
  getElement("delete-description").textContent = item
    ? `Produkt „${item.name}” zostanie usunięty z listy.`
    : `Lista „${state.activeList.name}” zostanie usunięta razem ze wszystkimi produktami. Tej operacji nie można cofnąć.`;
  getElement("delete-dialog").showModal();
}

function confirmDelete(event) {
  event.preventDefault();
  const { path, message, focusId } = state.pendingDelete;
  run(async () => {
    await request(path, "DELETE");
    getElement("delete-dialog").close();
    state.pendingDelete = null;
    await refreshLists();
  }, message, focusId);
}

function changeQuantity(item, change) {
  const quantity = item.quantity + change;
  if (quantity < 1 || quantity > 999) return;
  run(async () => {
    await request(`/lists/${state.activeList.id}/items/${item.id}`, "PATCH", { quantity });
    await refreshLists();
  });
}

getElement("new-list").addEventListener("click", () => openListDialog("create"));
getElement("hero-new-list").addEventListener("click", () => openListDialog("create"));
getElement("new-list-inline").addEventListener("click", () => openListDialog("create"));
getElement("create-first-list").addEventListener("click", () => openListDialog("create"));
getElement("rename-list").addEventListener("click", () => openListDialog("rename"));
getElement("delete-list").addEventListener("click", () => openDeleteDialog());
getElement("list-form").addEventListener("submit", saveList);
getElement("add-item-form").addEventListener("submit", addItem);
getElement("edit-item-form").addEventListener("submit", saveItem);
getElement("delete-form").addEventListener("submit", confirmDelete);
getElement("retry").addEventListener("click", () => run(() => refreshLists()));

getElement("shopping-lists").addEventListener("click", (event) => {
  const button = event.target.closest("[data-list-id]");
  if (!button) return;
  run(async () => {
    state.activeList = await request(`/lists/${button.dataset.listId}`);
    state.filter = "all";
    getElement("add-item-form").reset();
    getElement("item-name").setCustomValidity("");
    render();
  });
});

getElement("filters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter]");
  if (!button || state.busy) return;
  state.filter = button.dataset.filter;
  renderSummary();
  renderItems();
});

getElement("items").addEventListener("change", (event) => {
  if (!event.target.matches(".item-checkbox")) return;
  const itemId = event.target.closest("[data-item-id]").dataset.itemId;
  const isPurchased = event.target.checked;
  run(async () => {
    await request(`/lists/${state.activeList.id}/items/${itemId}`, "PATCH", { is_purchased: isPurchased });
    await refreshLists();
  }, isPurchased ? "Produkt oznaczony jako kupiony." : "Produkt wrócił do kupienia.");
});

getElement("items").addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (!button || state.busy) return;
  const itemId = Number(button.closest("[data-item-id]").dataset.itemId);
  const item = state.activeList.items.find((entry) => entry.id === itemId);
  if (button.dataset.action === "edit") openItemDialog(item);
  if (button.dataset.action === "delete") openDeleteDialog(item);
  if (button.dataset.action === "decrease") changeQuantity(item, -1);
  if (button.dataset.action === "increase") changeQuantity(item, 1);
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});
document.querySelectorAll("input[name='name']").forEach((input) => {
  input.addEventListener("input", () => input.setCustomValidity(""));
});
document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("cancel", (event) => { if (state.busy) event.preventDefault(); });
});

run(() => refreshLists());
