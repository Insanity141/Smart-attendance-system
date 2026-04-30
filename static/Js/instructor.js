// Initialize icons
document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        lucide.createIcons();
    }
});

/* Sidebar */
function toggleSidebar() {
    document.querySelector(".sidebar").classList.toggle("open");
}

/* Profile panel */
function toggleProfile() {
    document.getElementById("profilePanel").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("active");
}

/* Kebab menu */
function toggleKebabMenu(button) {
    const currentMenu = button.nextElementSibling;

    // Close others
    document.querySelectorAll(".kebab-dropdown").forEach(menu => {
        if (menu !== currentMenu) {
            menu.classList.remove("show");
        }
    });

    // Toggle current
    currentMenu.classList.toggle("show");
}

/* Close kebab when clicking outside */
document.addEventListener("click", function (event) {
    if (!event.target.closest(".kebab-container")) {
        document.querySelectorAll(".kebab-dropdown").forEach(menu => {
            menu.classList.remove("show");
        });
    }
});

/* create section modal */
// Make functions global
window.openCreateSectionModal = function () {
  document.getElementById("createSectionModal").classList.add("show");
  document.getElementById("createSectionOverlay").classList.add("show");
};

window.closeCreateSectionModal = function () {
  document.getElementById("createSectionModal").classList.remove("show");
  document.getElementById("createSectionOverlay").classList.remove("show");
};