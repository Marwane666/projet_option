console.log("Tracking enabled!");

// Track clicks on anchor links and buttons
document.addEventListener("click", (e) => {
    let element = e.target;

    // Handle anchor link clicks
    if (element.tagName === "A" || element.closest("a")) {
        const anchor = element.tagName === "A" ? element : element.closest("a");
        fetch("/record-interaction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                interaction: anchor.innerText.trim(), // Use link text as the interaction
                page: window.location.pathname,
                user: "User123" // Replace with dynamic user ID if available
            })
        });
        return; // Prevent further processing for this event
    }

    // Handle button clicks
    if (element.tagName === "BUTTON" || element.closest("button")) {
        const button = element.tagName === "BUTTON" ? element : element.closest("button");
        fetch("/record-interaction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                interaction: button.innerText.trim(), // Use button text as the interaction
                page: window.location.pathname,
                user: "User123" // Replace with dynamic user ID if available
            })
        });
    }
});

// Track page navigation
window.onload = () => {
    fetch("/record-navigation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            page: window.location.pathname,
            user: "User123"
        })
    });
};

// Track mouse movements for heatmap
let mouseMovements = [];
document.addEventListener("mousemove", (e) => {
    mouseMovements.push({ x: e.clientX, y: e.clientY, timestamp: new Date().toISOString() });
});

setInterval(() => {
    if (mouseMovements.length > 0) {
        fetch("/record-mouse-movements", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                movements: mouseMovements,
                page: window.location.pathname,
                user: "User123"
            })
        });
        mouseMovements = [];
    }
}, 5000);
