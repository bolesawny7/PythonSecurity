function closeAllAlerts() {
	const alerts = document.querySelectorAll(".alert");
	alerts.forEach((alertNode) => {
		new bootstrap.Alert(alertNode).close();
	});
}

document.addEventListener("DOMContentLoaded", () => {
	setTimeout(closeAllAlerts, 3000); 
});