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
    scrollData: {
        totalScrolls: 0,
        scrollRanges: [],
        lastPosition: 0
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

// Track mouse movements and zones
let mouseMovements = [];
let dwellTimeData = {};
let lastMousePosition = null;
let lastMoveTimestamp = null;
const DWELL_THRESHOLD = 1000; // 1 second threshold for dwell time

// Initialize scroll tracking
let lastScrollPosition = 0;
let scrollActivity = {
    totalScrolls: 0,
    scrollRanges: []
};

// Track scroll position and percentage
function getScrollPercentage() {
    const h = document.documentElement;
    const b = document.body;
    const st = 'scrollTop';
    const sh = 'scrollHeight';
    return (h[st]||b[st]) / ((h[sh]||b[sh]) - h.clientHeight) * 100;
}

// Handle mouse movements
document.addEventListener("mousemove", (e) => {
    const currentTime = new Date().getTime();
    const position = { 
        x: e.clientX, 
        y: e.clientY + window.scrollY, // Add scroll offset
        timestamp: new Date().toISOString()
    };

    // Calculate dwell time for zones
    if (lastMousePosition && lastMoveTimestamp) {
        const timeDiff = currentTime - lastMoveTimestamp;
        if (timeDiff > DWELL_THRESHOLD) {
            const zone = `${Math.floor(lastMousePosition.x / 100)}-${Math.floor(lastMousePosition.y / 100)}`;
            dwellTimeData[zone] = (dwellTimeData[zone] || 0) + timeDiff;
        }
    }

    mouseMovements.push(position);
    lastMousePosition = position;
    lastMoveTimestamp = currentTime;
});

// Track scrolling
document.addEventListener("scroll", () => {
    const currentScroll = window.scrollY;
    const scrollPercentage = getScrollPercentage();
    
    scrollActivity.totalScrolls++;
    scrollActivity.scrollRanges.push({
        from: lastScrollPosition,
        to: currentScroll,
        percentage: scrollPercentage,
        timestamp: new Date().toISOString()
    });
    
    lastScrollPosition = currentScroll;
});

// Send data periodically
setInterval(() => {
    if (mouseMovements.length > 0) {
        fetch("/record-mouse-movements", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                movements: mouseMovements,
                page: window.location.pathname,
                user: "User123",
                scrollPercentage: getScrollPercentage(),
                dwellTime: dwellTimeData,
                scrollActivity: scrollActivity
            })
        });
        
        // Reset tracking data
        mouseMovements = [];
        dwellTimeData = {};
        scrollActivity = {
            totalScrolls: 0,
            scrollRanges: []
        };
    }
}, 5000);

// Track mouse movements
document.addEventListener("mousemove", (e) => {
    const currentTime = new Date().getTime();
    const position = {
        x: e.clientX,
        y: e.clientY + window.scrollY,
        timestamp: new Date().toISOString()
    };

    // Add to session data
    sessionData.mouseMovements.push(position);
    sessionData.lastUpdate = new Date().toISOString();

    // Calculate dwell time
    const zone = `${Math.floor(position.x / 100)}-${Math.floor(position.y / 100)}`;
    sessionData.dwellTimes[zone] = (sessionData.dwellTimes[zone] || 0) + 100;
});

// Track scrolling
document.addEventListener("scroll", () => {
    const currentScroll = window.scrollY;
    const scrollPercentage = (currentScroll / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
    
    sessionData.scrollData.totalScrolls++;
    sessionData.scrollData.scrollRanges.push({
        from: sessionData.scrollData.lastPosition,
        to: currentScroll,
        percentage: scrollPercentage,
        timestamp: new Date().toISOString()
    });
    
    sessionData.scrollData.lastPosition = currentScroll;
    sessionData.lastUpdate = new Date().toISOString();
});

// Send session data periodically
setInterval(() => {
    if (sessionData.mouseMovements.length > 0 || 
        sessionData.scrollData.scrollRanges.length > 0 || 
        sessionData.interactions.length > 0) {
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
