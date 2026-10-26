document.addEventListener("DOMContentLoaded", () => {
  const formPanel = document.getElementById("registration");
  const registrationForm = document.getElementById("registration-form");
  const message = document.getElementById("form-message");
  const eventIdInput = document.getElementById("event-id");
  const formTitle = document.getElementById("form-title");
  const submitButton = registrationForm.querySelector('button[type="submit"]');

  document.querySelectorAll(".register-trigger").forEach((button) => {
    button.addEventListener("click", () => {
      eventIdInput.value = button.dataset.eventId;
      formTitle.textContent = `Register for ${button.dataset.eventTitle}`;
      message.textContent = "";
      message.className = "form-message";
      formPanel.classList.remove("hidden");
      formPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      document.getElementById("name").focus({ preventScroll: true });
    });
  });

  document.getElementById("close-form").addEventListener("click", () => {
    formPanel.classList.add("hidden");
    registrationForm.reset();
    message.textContent = "";
  });

  registrationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    submitButton.disabled = true;
    message.className = "form-message";
    message.textContent = "Submitting…";
    const payload = {
      event_id: eventIdInput.value,
      name: document.getElementById("name").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim()
    };

    try {
      const response = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Registration failed. Please try again.");
      message.className = "form-message message success";
      message.textContent = result.message;
      registrationForm.reset();
      const cardButton = document.querySelector(`.register-trigger[data-event-id="${CSS.escape(String(payload.event_id))}"]`);
      if (cardButton) {
        const count = cardButton.closest(".event-card").querySelector(".event-meta span:last-child");
        const match = count.textContent.match(/\d+/);
        if (match) count.textContent = `${Number(match[0]) + 1} registered`;
      }
    } catch (error) {
      message.className = "form-message message error";
      message.textContent = error.message || "Could not connect. Please try again.";
    } finally {
      submitButton.disabled = false;
    }
  });
});
