console.log("Tracking enabled!");

// Add cookie management at the top
function getUserId() {
    let userId = document.cookie.match(/userId=([^;]+)/);
    if (!userId) {
        userId = 'user_' + Date.now() + Math.random().toString(36).substr(2);
        document.cookie = `userId=${userId};path=/;max-age=31536000`; // 1 year
    } else {
        userId = userId[1];
    }
    return userId;
}

// Generate a unique session ID
const sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);

// Session data structure
let sessionData = {
    sessionId: sessionId,
    user: getUserId(),
    page: window.location.pathname,
    startTime: new Date().toISOString(),
    mouseMovements: [],
    dwellTimes: {},
    pageHeight: document.documentElement.scrollHeight,
    scrollData: {
        totalScrolls: 0,
        scrollRanges: [],
        lastPosition: window.scrollY,
        viewportHeight: window.innerHeight
    },
    interactions: [], // Add interactions array
    lastUpdate: new Date().toISOString()
};

// Track clicks on anchor links and buttons
document.addEventListener("click", (e) => {
    let element = e.target;
    let interactionData = null;

    // Handle anchor link clicks
    if (element.tagName === "A" || element.closest("a")) {
        const anchor = element.tagName === "A" ? element : element.closest("a");
        interactionData = {
            type: 'link',
            text: anchor.innerText.trim(),
            timestamp: new Date().toISOString()
        };
    }

    // Handle button clicks
    if (element.tagName === "BUTTON" || element.closest("button")) {
        const button = element.tagName === "BUTTON" ? element : element.closest("button");
        interactionData = {
            type: 'button',
            text: button.innerText.trim(),
            timestamp: new Date().toISOString()
        };
    }

    if (interactionData) {
        sessionData.interactions.push(interactionData);
        sessionData.lastUpdate = new Date().toISOString();
    }
});

// Track position and scroll state
let lastMousePosition = null;
let lastScrollY = window.scrollY;
const trackingInterval = 10; // 10ms

// Function to get current scroll range
function getCurrentScrollRange() {
    return {
        from: Math.round(window.scrollY),
        to: Math.round(window.scrollY + window.innerHeight),
        timestamp: new Date().toISOString()
    };
}

// Track both mouse and scroll every 10ms
setInterval(() => {
    const timestamp = new Date().toISOString();
    const currentScroll = getCurrentScrollRange();
    
    // Record mouse position with current scroll position
    if (lastMousePosition) {
        const position = {
            x: lastMousePosition.x,
            y: lastMousePosition.y + currentScroll.from, // Add scroll position to Y coordinate
            timestamp: timestamp,
            scrollPosition: currentScroll.from // Store scroll position for reference
        };
        
        sessionData.mouseMovements.push(position);
        
        const zone = `${Math.floor(position.x / 100)}-${Math.floor(position.y / 100)}`;
        sessionData.dwellTimes[zone] = (sessionData.dwellTimes[zone] || 0) + trackingInterval;
    }

    // Record scroll position if changed
    if (lastScrollY !== window.scrollY) {
        sessionData.scrollData.scrollRanges.push({
            ...currentScroll,
            scrollDuration: trackingInterval
        });
        lastScrollY = window.scrollY;
    }

    sessionData.lastUpdate = timestamp;
}, trackingInterval);

// Update mouse position on movement
document.addEventListener("mousemove", (e) => {
    lastMousePosition = {
        x: e.clientX,
        y: e.clientY  // Store raw Y coordinate without scroll offset
    };
});

// Update page height on dynamic content changes
const resizeObserver = new ResizeObserver(() => {
    sessionData.pageHeight = document.documentElement.scrollHeight;
    sessionData.scrollData.viewportHeight = window.innerHeight;
});

resizeObserver.observe(document.documentElement);

// Send session data periodically
setInterval(() => {
    if (sessionData.mouseMovements.length > 0 || 
        sessionData.scrollData.scrollRanges.length > 0 || 
        sessionData.interactions.length > 0) {
        
        // Ensure current scroll position is recorded before sending
        fetch("/record-session-data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(sessionData)
        });

        // Clear arrays but keep the session
        sessionData.mouseMovements = [];
        sessionData.scrollData.scrollRanges = [];
        sessionData.interactions = [];
    }
}, 5000);

// Handle page unload
window.addEventListener('beforeunload', () => {
    sessionData.endTime = new Date().toISOString();
    fetch("/record-session-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            ...sessionData,
            isFinal: true
        }),
        // Use sendBeacon for more reliable delivery during page unload
        keepalive: true
    });
});
