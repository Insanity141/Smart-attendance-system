// ICONS
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
});

// SIDEBAR TOGGLE (MOBILE)
function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (sidebar) sidebar.classList.toggle("open");
}

// PROFILE PANEL TOGGLE
function toggleProfile() {
  const panel = document.getElementById("profilePanel");
  const overlay = document.getElementById("overlay");

  if (panel) panel.classList.toggle("open");
  if (overlay) overlay.classList.toggle("active");

  if (window.lucide) lucide.createIcons();
}

// KEBAB MENU TOGGLE
function toggleMenu(button) {
  const menu = button.closest(".action-menu");
  const isOpen = menu.classList.contains("active");

  // Close all menus first
  document.querySelectorAll(".action-menu")
    .forEach(m => m.classList.remove("active"));

  // Open current if it wasn't open
  if (!isOpen) {
    menu.classList.add("active");
  }
}

// CLICK OUTSIDE HANDLER
document.addEventListener("click", function (e) {

  // Close kebab menus
  if (!e.target.closest(".action-menu")) {
    document.querySelectorAll(".action-menu")
      .forEach(m => m.classList.remove("active"));
  }

  // Close profile if clicking overlay
  const overlay = document.getElementById("overlay");
  if (e.target === overlay) {
    const panel = document.getElementById("profilePanel");
    if (panel) panel.classList.remove("open");
    if (overlay) overlay.classList.remove("active");
  }

  // Close modals if clicking outside
  document.querySelectorAll(".modal").forEach(modal => {
    if (e.target === modal) {
      modal.classList.remove("active");
    }
  });

});


// ESC KEY HANDLER
document.addEventListener("keydown", function (e) {

  if (e.key === "Escape") {

    // Close all modals
    document.querySelectorAll(".modal")
      .forEach(modal => modal.classList.remove("active"));

    // Close profile panel
    const panel = document.getElementById("profilePanel");
    const overlay = document.getElementById("overlay");

    if (panel) panel.classList.remove("open");
    if (overlay) overlay.classList.remove("active");

    // Close all kebab menus
    document.querySelectorAll(".action-menu")
      .forEach(m => m.classList.remove("active"));

    // Close sidebar (mobile)
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) sidebar.classList.remove("open");
  }

});