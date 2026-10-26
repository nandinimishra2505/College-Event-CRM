document.addEventListener("DOMContentLoaded", () => {
  const message = document.getElementById("admin-message");
  const eventList = document.getElementById("event-list");
  const registrationsBody = document.getElementById("registrations-body");

  function showMessage(text, isError = false) {
    message.textContent = text;
    message.className = `form-message message ${isError ? "error" : "success"}`;
  }

  async function api(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      ...options
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Request failed.");
    return data;
  }

  function makeCell(text) {
    const td = document.createElement("td");
    td.textContent = text ?? "";
    return td;
  }

  async function loadEvents() {
    const events = await api("/api/events");
    document.getElementById("event-total").textContent = events.length;
    eventList.replaceChildren();
    if (!events.length) {
      eventList.textContent = "No events yet.";
      return;
    }
    events.forEach((event) => {
      const item = document.createElement("div");
      item.className = "admin-event-row";
      const info = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = event.title;
      const detail = document.createElement("p");
      detail.textContent = `${event.event_date} · ${event.venue} · ${event.registration_count} registrations`;
      info.append(title, detail);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "button button-danger";
      remove.textContent = "Delete";
      remove.addEventListener("click", async () => {
        if (!window.confirm(`Delete "${event.title}" and its registrations?`)) return;
        try {
          await api(`/api/admin/events/${event.id}`, { method: "DELETE" });
          showMessage("Event deleted.");
          await refreshAll();
        } catch (error) {
          showMessage(error.message, true);
        }
      });
      item.append(info, remove);
      eventList.append(item);
    });
  }

  async function loadRegistrations() {
    const rows = await api("/api/admin/registrations");
    document.getElementById("registration-total").textContent = rows.length;
    registrationsBody.replaceChildren();
    if (!rows.length) {
      const tr = document.createElement("tr");
      tr.append(makeCell("No registrations yet."));
      const td = tr.firstElementChild;
      td.colSpan = 4;
      registrationsBody.append(tr);
      return;
    }
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.append(
        makeCell(row.name),
        makeCell(`${row.email}\n${row.phone}`),
        makeCell(`${row.event_title} (${row.event_date})`),
        makeCell(row.created_at)
      );
      registrationsBody.append(tr);
    });
  }

  async function refreshAll() {
    try {
      await Promise.all([loadEvents(), loadRegistrations()]);
    } catch (error) {
      showMessage(error.message, true);
    }
  }

  document.getElementById("event-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await api("/api/admin/events", {
        method: "POST",
        body: JSON.stringify({
          title: document.getElementById("event-title").value.trim(),
          event_date: document.getElementById("event-date").value,
          venue: document.getElementById("event-venue").value.trim(),
          description: document.getElementById("event-description").value.trim()
        })
      });
      event.currentTarget.reset();
      showMessage("Event added successfully.");
      await refreshAll();
    } catch (error) {
      showMessage(error.message, true);
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("refresh-registrations").addEventListener("click", refreshAll);
  refreshAll();
});
