document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        lucide.createIcons();
    }
});

function toggleSidebar() {
    document.querySelector(".sidebar").classList.toggle("open");
}

function filterAttendance() {
    const input = document.getElementById("attendanceSearch").value.toLowerCase().trim();
    const groups = document.querySelectorAll(".attendance-group");

    groups.forEach(group => {
        const dateHeader = group.querySelector(".date-title").innerText.toLowerCase();
        const rows = group.querySelectorAll(".attendance-row");

        let hasVisibleRows = false;

        rows.forEach(row => {
            const rowText = row.innerText.toLowerCase();

            if (rowText.includes(input) || dateHeader.includes(input)) {
                row.style.display = "";
                hasVisibleRows = true;
            } else {
                row.style.display = "none";
            }
        });

        if (dateHeader.includes(input)) {
            rows.forEach(row => {
                row.style.display = "";
            });
            group.style.display = "";
        } else if (hasVisibleRows) {
            group.style.display = "";
        } else {
            group.style.display = "none";
        }
    });
}