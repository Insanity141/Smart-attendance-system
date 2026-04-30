document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
});

function toggleSidebar() {
  document.querySelector(".sidebar").classList.toggle("open");
}

function toggleProfile() {
  document.getElementById("profilePanel")?.classList.toggle("open");
  document.getElementById("overlay")?.classList.toggle("active");
}

function openAddStudentModal() {
    document.getElementById("addStudentModal").classList.add("show");
    document.getElementById("addStudentOverlay").classList.add("show");
}

function closeAddStudentModal() {
  document.getElementById("addStudentModal").classList.remove("show");
  document.getElementById("addStudentOverlay").classList.remove("show");
}

function filterStudents() {
  const input = document.getElementById("studentSearch").value.toLowerCase();
  const rows = document.querySelectorAll("#studentTable tbody tr");

  rows.forEach(row => {
    const studentId = row.cells[0].textContent.toLowerCase();
    const studentName = row.cells[1].textContent.toLowerCase();

    row.style.display = (
      studentId.includes(input) || studentName.includes(input)
    ) ? "" : "none";
  });
}

function toggleKebabMenu(button) {
  const currentMenu = button.nextElementSibling;

  document.querySelectorAll(".kebab-dropdown").forEach(menu => {
    if (menu !== currentMenu) {
      menu.classList.remove("show");
    }
  });

  currentMenu.classList.toggle("show");
}

document.addEventListener("click", function(event) {
  if (!event.target.closest(".kebab-container")) {
    document.querySelectorAll(".kebab-dropdown").forEach(menu => {
      menu.classList.remove("show");
    });
  }
});