console.log("Tracking enabled!");

// ======================
//  GESTION DES COOKIES
// ======================
function getUserId() {
    let userId = document.cookie.match(/userId=([^;]+)/);
    if (!userId) {
        userId = 'user_' + Date.now() + Math.random().toString(36).substr(2);
        document.cookie = `userId=${userId};path=/;max-age=31536000`; // 1 an
    } else {
        userId = userId[1];
    }
    return userId;
}

// ======================
//  IDENTIFIANT DE SESSION
// ======================
const sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);

// ======================
//  STRUCTURE DE DONNÉES SESSION
// ======================
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
    interactions: [],
    lastUpdate: new Date().toISOString()
};

// ==================================
//  CAPTURE DES CLICS (LIENS & BOUTONS)
// ==================================
document.addEventListener("click", (e) => {
    let element = e.target;
    let interactionData = null;

    // Si c'est un lien ou dans un lien
    if (element.tagName === "A" || element.closest("a")) {
        const anchor = element.tagName === "A" ? element : element.closest("a");
        interactionData = {
            type: 'link',
            text: anchor.innerText.trim(),
            timestamp: new Date().toISOString()
        };
    }

    // Si c'est un bouton ou dans un bouton
    if (element.tagName === "BUTTON" || element.closest("button")) {
        const button = element.tagName === "BUTTON" ? element : element.closest("button");
        interactionData = {
            type: 'button',
            text: button.innerText.trim(),
            timestamp: new Date().toISOString()
        };
    }

    // On enregistre l'interaction
    if (interactionData) {
        sessionData.interactions.push(interactionData);
        sessionData.lastUpdate = new Date().toISOString();
    }
});

// ======================
//  SUIVI SOURIS & SCROLL
// ======================
let lastMousePosition = null;
let lastScrollY = window.scrollY;
const trackingInterval = 10; // 10ms

function getCurrentScrollRange() {
    return {
        from: Math.round(window.scrollY),
        to: Math.round(window.scrollY + window.innerHeight),
        timestamp: new Date().toISOString()
    };
}

// Mise à jour à intervalles réguliers (10ms)
setInterval(() => {
    const timestamp = new Date().toISOString();
    const currentScroll = getCurrentScrollRange();

    // Enregistrement de la position de la souris
    if (lastMousePosition) {
        const position = {
            x: lastMousePosition.x,
            y: lastMousePosition.y + currentScroll.from, // Y relatif au scroll
            timestamp: timestamp,
            scrollPosition: currentScroll.from
        };
        sessionData.mouseMovements.push(position);

        // Calcul d'une "zone" (exemple : segment 100px)
        const zone = `${Math.floor(position.x / 100)}-${Math.floor(position.y / 100)}`;
        sessionData.dwellTimes[zone] = (sessionData.dwellTimes[zone] || 0) + trackingInterval;
    }

    // Détection de scroll
    if (lastScrollY !== window.scrollY) {
        sessionData.scrollData.scrollRanges.push({
            ...currentScroll,
            scrollDuration: trackingInterval
        });
        lastScrollY = window.scrollY;
    }

    sessionData.lastUpdate = timestamp;
}, trackingInterval);

// Mise à jour de la position souris en temps réel
document.addEventListener("mousemove", (e) => {
    lastMousePosition = {
        x: e.clientX,
        y: e.clientY
    };
});

// ======================
//  OBSERVER LES REDIMENSIONS DE LA PAGE
// ======================
const resizeObserver = new ResizeObserver(() => {
    sessionData.pageHeight = document.documentElement.scrollHeight;
    sessionData.scrollData.viewportHeight = window.innerHeight;
});
resizeObserver.observe(document.documentElement);

// ======================
//  ENVOI PÉRIODIQUE DES DONNÉES (PUSH VERS LE SERVEUR)
// ======================
setInterval(() => {
    // On n'envoie que si on a quelque chose de nouveau
    if (
        sessionData.mouseMovements.length > 0 ||
        sessionData.scrollData.scrollRanges.length > 0 ||
        sessionData.interactions.length > 0
    ) {
        fetch("/record-session-data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(sessionData)
        })
            .then((response) => response.json())
            .then((data) => {
                // Pour cette approche "pull-based", on ne fait que loguer la réponse.
                console.log("Session data recorded:", data);
                // Pas d'appel direct à applyRecommendations ici.
            })
            .catch((err) => {
                console.error("Erreur lors de l'envoi des données de session :", err);
            });

        // On réinitialise les tableaux pour ne pas renvoyer les mêmes données en boucle
        sessionData.mouseMovements = [];
        sessionData.scrollData.scrollRanges = [];
        sessionData.interactions = [];
    }
}, 5000);

// ======================
//  GESTION FIN DE PAGE
// ======================
window.addEventListener('beforeunload', () => {
    sessionData.endTime = new Date().toISOString();
    fetch("/record-session-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            ...sessionData,
            isFinal: true
        }),
        // keepalive permet (souvent) d'assurer l'envoi même lors du déchargement
        keepalive: true
    });
});

// ======================
//  RÉCUPÉRATION DES RECO (PULL DU SERVEUR)
// ======================
function fetchRecommendations() {
    return fetch("/recommendations")
        .then(response => {
            if (!response.ok) {
                // ex: 400 => "No persona found in session"
                throw new Error("Aucun persona disponible pour le moment");
            }
            return response.json();
        })
        .then(data => {
            // { persona: "Précipité", recommendations: [...] }
            console.log("Recommendations from server:", data);
            localStorage.setItem("persona", data.persona);
            return data;
        })
        .catch(err => {
            console.warn("Impossible de récupérer les recommandations :", err);
            return null; // On gère le cas d'erreur
        });
}

/**
 * applyPersonaIfExists
 * --------------------
 * Tente d'appliquer le persona stocké dans localStorage,
 * s'il existe déjà (par ex. si on change de page).
 */
function applyPersonaIfExists() {
    const storedPersona = localStorage.getItem("persona");
    if (storedPersona) {
        console.log("Applying persona from localStorage:", storedPersona);
        applyRecommendations(storedPersona);
    }
}

// ======================
//  LOGIQUE DE RECOMMANDATIONS
// ======================
function applyRecommendations(persona) {
    // Afficher le badge du persona en haut/à gauche
    showPersonaBadge(persona);

    switch (persona) {
        case "Découvreur":
            showTutorialCallToAction();
            suggestPopularContent();
            break;
        case "Précipité":
            enableFastCheckout();
            showQuickLinks();
            break;
        case "Chercheur de bonnes affaires":
            showPromotionalPopup();
            highlightBestDeals();
            break;
        default:
            console.log("Aucune recommandation spécifique pour ce persona.");
            break;
    }
}

// -------------------
// STYLE DU BADGE PERSONA
// -------------------
function showPersonaBadge(persona) {
    const existingBadge = document.getElementById('persona-badge');
    if (existingBadge) existingBadge.remove();

    const badge = document.createElement("div");
    badge.id = 'persona-badge';
    badge.style.position = "fixed";
    badge.style.top = "80px"; // Modifié pour être sous le header
    badge.style.left = "20px";
    badge.style.zIndex = "999"; // Réduit pour être sous certains éléments du header si nécessaire
    badge.style.padding = "12px 24px";
    badge.style.borderRadius = "30px";
    badge.style.fontSize = "15px";
    badge.style.fontWeight = "600";
    badge.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
    badge.style.cursor = "pointer";
    badge.style.transition = "all 0.3s ease";
    badge.style.backdropFilter = "blur(6px)";
    badge.style.border = "2px solid transparent";
    badge.style.opacity = "0";
    badge.style.animation = "slideBadgeIn 0.5s ease forwards";

    // Couleurs selon le persona
    switch (persona) {
        case "Découvreur":
            badge.style.backgroundColor = "rgba(227, 242, 253, 0.95)";
            badge.style.color = "#1565c0";
            badge.style.borderColor = "#1976d2";
            break;
        case "Précipité":
            badge.style.backgroundColor = "rgba(252, 228, 236, 0.95)";
            badge.style.color = "#ad1457";
            badge.style.borderColor = "#c2185b";
            break;
        case "Chercheur de bonnes affaires":
            badge.style.backgroundColor = "rgba(241, 248, 233, 0.95)";
            badge.style.color = "#558b2f";
            badge.style.borderColor = "#7cb342";
            break;
    }

    // Contenu avec icône et texte
    badge.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.2em;">👤</span>
            <span style="white-space:nowrap;">${persona}</span>
        </div>
    `;

    // Effets de survol améliorés
    badge.addEventListener('mouseover', () => {
        badge.style.transform = 'translateY(-2px)';
        badge.style.boxShadow = '0 6px 16px rgba(0,0,0,0.15)';
    });

    badge.addEventListener('mouseout', () => {
        badge.style.transform = 'translateY(0)';
        badge.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
    });

    document.body.appendChild(badge);
}

// -------------------
// RECO 1: "Découvreur"
// -------------------
function showTutorialCallToAction() {
    const cta = document.createElement("div");
    cta.id = 'tutorial-cta';
    cta.classList.add("card", "shadow", "border-0");
    cta.style.position = "fixed";
    cta.style.bottom = "20px";
    cta.style.right = "20px";
    cta.style.zIndex = "9998"; // Un peu plus bas que suggestions
    cta.style.width = "320px"; // Largeur fixe pour aligner avec suggestions
    cta.style.borderRadius = "12px";
    cta.style.overflow = "hidden";
    cta.style.animation = "fadeIn 0.5s ease";

    cta.innerHTML = `
      <div class="card-body" style="background-color:#eef;position:relative;">
        <div style="position:absolute;top:5px;right:5px;cursor:pointer;padding:5px;font-size:1.2em;color:#666;" 
             onclick="document.getElementById('tutorial-cta').remove()">×</div>
        <h5 class="card-title" style="color:#333;font-weight:600;font-size:1.1rem;margin:10px 0;">
          Envie de découverte ?
        </h5>
        <p class="card-text" style="font-size:0.95rem;color:#555;margin-bottom:15px;">
          Consultez nos tutoriels pour profiter au maximum de la plateforme !
        </p>
        <a href="/tutos" class="btn btn-primary btn-sm" style="width:100%;">Voir les tutoriels</a>
      </div>
    `;

    document.body.appendChild(cta);
}

function suggestPopularContent() {
    const suggestions = document.createElement("div");
    suggestions.id = 'popular-content';
    suggestions.classList.add("card", "shadow-lg");
    suggestions.style.position = "fixed";
    suggestions.style.bottom = "180px"; // Positionné au-dessus du CTA
    suggestions.style.right = "20px";
    suggestions.style.zIndex = "9999";
    suggestions.style.width = "320px"; // Même largeur que le CTA
    suggestions.style.borderRadius = "10px";
    suggestions.style.animation = "fadeInUp 0.5s ease";
    suggestions.style.overflow = "hidden";

    suggestions.innerHTML = `
      <div class="card-header" style="background-color:#2196f3;color:white;font-weight:600;display:flex;justify-content:space-between;align-items:center;">
        <span>À découvrir</span>
        <span style="cursor:pointer;padding:0 5px;" onclick="document.getElementById('popular-content').remove()">×</span>
      </div>
      <ul class="list-group list-group-flush">
        <li class="list-group-item d-flex align-items-center hover-effect">
          <span style="font-size:1.3rem;">📚</span>
          <a href="/top-articles" class="ms-2" style="text-decoration:none;color:#007bff;font-weight:500;flex-grow:1;">
            Articles les plus lus
          </a>
        </li>
        <li class="list-group-item d-flex align-items-center hover-effect">
          <span style="font-size:1.3rem;">🎥</span>
          <a href="/videos" class="ms-2" style="text-decoration:none;color:#007bff;font-weight:500;flex-grow:1;">
            Vidéos populaires
          </a>
        </li>
        <li class="list-group-item d-flex align-items-center hover-effect">
          <span style="font-size:1.3rem;">💡</span>
          <a href="/nouveautes" class="ms-2" style="text-decoration:none;color:#007bff;font-weight:500;flex-grow:1;">
            Dernières nouveautés
          </a>
        </li>
      </ul>
    `;

    // Ajouter des styles pour l'effet de survol
    const style = document.createElement('style');
    style.textContent = `
        .hover-effect {
            transition: all 0.3s ease;
        }
        .hover-effect:hover {
            background-color: rgba(33, 150, 243, 0.1);
            transform: translateX(5px);
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(suggestions);
}

// -------------------
// RECO 2: "Précipité"
// -------------------
function enableFastCheckout() {
    const addToCartButtons = document.querySelectorAll(".add-to-cart-btn");
    addToCartButtons.forEach((btn) => {
        btn.addEventListener("click", (event) => {
            event.preventDefault();
            window.location.href = "/checkout";
        });
    });

    // Petit message d'info
    const notice = document.createElement("div");
    notice.classList.add("alert", "alert-warning");
    notice.style.position = "fixed";
    notice.style.top = "60px";
    notice.style.right = "20px";
    notice.style.zIndex = "9999";
    notice.style.minWidth = "240px";
    notice.style.boxShadow = "0 4px 8px rgba(0,0,0,0.1)";
    notice.style.animation = "fadeIn 0.5s ease";
    notice.innerText = "Votre parcours est rapide : redirection immédiate vers la commande !";

    document.body.appendChild(notice);
}

function showQuickLinks() {
    const quickNav = document.createElement("div");
    quickNav.classList.add("card");
    quickNav.style.position = "fixed";
    quickNav.style.top = "50%";
    quickNav.style.right = "20px";
    quickNav.style.transform = "translateY(-50%)";
    quickNav.style.zIndex = "9999";
    quickNav.style.minWidth = "140px";
    quickNav.style.borderRadius = "10px";
    quickNav.style.overflow = "hidden";
    quickNav.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
    quickNav.style.animation = "fadeInRight 0.6s ease";

    quickNav.innerHTML = `
      <div class="card-body p-2" style="background-color:#fff;">
        <a href="/checkout" class="btn btn-primary w-100 my-1">🛒 Panier</a>
        <a href="/compte" class="btn btn-secondary w-100 my-1">👤 Compte</a>
        <a href="/aide" class="btn btn-info w-100 my-1 text-white">❓ Aide</a>
      </div>
    `;

    document.body.appendChild(quickNav);
}

// -------------------
// RECO 3: "Chercheur de bonnes affaires"
// -------------------
function showPromotionalPopup() {
    // Suppression de l'ancien popup s'il existe
    const existingPopup = document.getElementById('promo-popup');
    if (existingPopup) existingPopup.remove();

    // Création du nouveau popup stylé
    const popup = document.createElement('div');
    popup.id = 'promo-popup';
    popup.style.position = 'fixed';
    popup.style.top = '50%';
    popup.style.left = '50%';
    popup.style.transform = 'translate(-50%, -50%)';
    popup.style.backgroundColor = 'white';
    popup.style.padding = '25px';
    popup.style.borderRadius = '15px';
    popup.style.boxShadow = '0 5px 30px rgba(0,0,0,0.2)';
    popup.style.zIndex = '10000';
    popup.style.maxWidth = '400px';
    popup.style.width = '90%';
    popup.style.animation = 'popupFadeIn 0.5s ease';
    popup.style.border = '2px solid #4caf50';

    // Contenu du popup
    popup.innerHTML = `
        <div style="text-align: center;">
            <div style="position: absolute; top: -20px; right: -20px; background: #4caf50; color: white; padding: 10px; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: bold;" onclick="this.parentElement.parentElement.remove()">×</div>
            <div style="font-size: 3em; margin-bottom: 10px;">🎉</div>
            <h2 style="color: #4caf50; margin-bottom: 15px; font-size: 1.5em;">Offre Spéciale !</h2>
            <div style="background: #e8f5e9; padding: 15px; border-radius: 10px; margin: 15px 0;">
                <span style="font-size: 2em; font-weight: bold; color: #2e7d32;">-15%</span>
                <p style="margin: 10px 0; color: #1b5e20;">sur votre première commande</p>
            </div>
            <div style="background: #f5f5f5; padding: 10px; border-radius: 8px; margin: 15px 0;">
                <p style="margin: 0; font-family: monospace; font-size: 1.2em; letter-spacing: 2px; color: #333;">PROMO15</p>
            </div>
            <p style="font-size: 0.9em; color: #666; margin: 15px 0;">À utiliser avant la fin du mois !</p>
            <button onclick="copyPromoCode()" style="background: #4caf50; color: white; border: none; padding: 12px 25px; border-radius: 25px; cursor: pointer; font-weight: bold; transition: all 0.3s ease;">
                Copier le code
            </button>
        </div>
    `;

    // Ajout du popup au body
    document.body.appendChild(popup);

    // Ajout d'un overlay semi-transparent
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
    overlay.style.zIndex = '9999';
    overlay.style.animation = 'fadeIn 0.3s ease';
    overlay.onclick = () => {
        overlay.remove();
        popup.remove();
    };
    document.body.appendChild(overlay);
}

function copyPromoCode() {
    navigator.clipboard.writeText('PROMO15').then(() => {
        const button = document.querySelector('#promo-popup button');
        button.textContent = 'Code copié !';
        button.style.backgroundColor = '#2e7d32';
        setTimeout(() => {
            button.textContent = 'Copier le code';
            button.style.backgroundColor = '#4caf50';
        }, 2000);
    });
}

function highlightBestDeals() {
    const deals = document.querySelectorAll('.product-card');
    deals.forEach(card => {
        if (card.dataset.discount && parseInt(card.dataset.discount) > 20) {
            card.style.position = 'relative';
            card.style.transform = 'scale(1.02)';
            card.style.boxShadow = '0 8px 20px rgba(76,175,80,0.2)';
            card.style.transition = 'all 0.3s ease';
            card.style.border = '2px solid #4caf50';
            card.style.borderRadius = '12px';
            card.style.overflow = 'hidden';

            // Ruban amélioré
            const ribbon = document.createElement('div');
            ribbon.style.position = 'absolute';
            ribbon.style.top = '15px';
            ribbon.style.right = '-35px';
            ribbon.style.transform = 'rotate(45deg)';
            ribbon.style.backgroundColor = '#4caf50';
            ribbon.style.color = 'white';
            ribbon.style.padding = '8px 40px';
            ribbon.style.fontSize = '0.85rem';
            ribbon.style.fontWeight = '600';
            ribbon.style.boxShadow = '0 2px 6px rgba(0,0,0,0.2)';
            ribbon.style.letterSpacing = '1px';

            // Ajout d'une icône et du texte
            ribbon.innerHTML = `
                <span style="margin-right: 5px;">🔥</span> 
                <span>MEILLEURE OFFRE</span>
            `;

            // Badge de réduction
            const discountBadge = document.createElement('div');
            discountBadge.style.position = 'absolute';
            discountBadge.style.top = '10px';
            discountBadge.style.left = '10px';
            discountBadge.style.backgroundColor = '#ff5252';
            discountBadge.style.color = 'white';
            discountBadge.style.padding = '5px 10px';
            discountBadge.style.borderRadius = '20px';
            discountBadge.style.fontWeight = 'bold';
            discountBadge.style.fontSize = '0.9em';
            discountBadge.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            discountBadge.innerHTML = `-${card.dataset.discount}%`;

            card.appendChild(ribbon);
            card.appendChild(discountBadge);

            // Effets de survol améliorés
            card.addEventListener('mouseover', () => {
                card.style.transform = 'scale(1.04)';
                card.style.boxShadow = '0 12px 30px rgba(76,175,80,0.3)';
            });
            card.addEventListener('mouseout', () => {
                card.style.transform = 'scale(1.02)';
                card.style.boxShadow = '0 8px 20px rgba(76,175,80,0.2)';
            });
        }
    });
}

// ======================
//  GESTION DU HERO VIDEO
// ======================
document.addEventListener("DOMContentLoaded", function () {
    const video = document.getElementById("heroVideo");
    const heroSection = document.querySelector(".hero");
    if (!video) return; // Si la page n'a pas de vidéo, on sort.

    // Lorsque la vidéo est prête
    video.addEventListener("loadeddata", function () {
        heroSection.classList.add("video-loaded");
    });

    // En cas d'erreur
    video.addEventListener("error", function (e) {
        console.error("Error loading video:", e);
        heroSection.classList.add("fallback-mode");
    });

    // Fallback après 5s si la vidéo n'est toujours pas prête
    setTimeout(() => {
        if (!(video.readyState >= 3)) {
            heroSection.classList.add("fallback-mode");
        }
    }, 5000);
});

// ======================
//  RÉCUPÉRATION DU PERSONA AU CHARGEMENT (exemple)
// ======================
document.addEventListener("DOMContentLoaded", function () {
    // 1. Applique immédiatement un persona stocké si disponible
    applyPersonaIfExists();

    // 2. Au bout de 3 secondes, on tente de récupérer un persona frais
    //    (si le back-end en a un)
    setTimeout(() => {
        fetchRecommendations().then(data => {
            if (data && data.persona) {
                applyRecommendations(data.persona);
            }
        });
    }, 500);
});

// -------------------
// Petites animations css @keyframes
// -------------------
const style = document.createElement('style');
style.innerHTML = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes popupFadeIn {
    from {
        opacity: 0;
        transform: translate(-50%, -40%);
    }
    to {
        opacity: 1;
        transform: translate(-50%, -50%);
    }
}
@keyframes slideBadgeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;
document.head.appendChild(style);
