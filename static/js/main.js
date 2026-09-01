document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initSidebar();
    initUserMenu();
    initCreatorPopups();
    initLikeButtons();
    initCommentToggles();
    initContentPlayerActions();
    initSubscriptionPopups();
});

/* Ambient particle field -------------------------------------------------- */
function initParticles() {
    const field = document.getElementById('particleField');
    if (!field) return;

    const COUNT = 28;
    for (let i = 0; i < COUNT; i++) {
        const p = document.createElement('span');
        p.className = 'particle';
        p.style.left = `${Math.random() * 100}%`;
        p.style.animationDuration = `${12 + Math.random() * 14}s`;
        p.style.animationDelay = `${Math.random() * 12}s`;
        p.style.opacity = `${0.3 + Math.random() * 0.4}`;
        field.appendChild(p);
    }
}

/* Off-canvas sidebar -------------------------------------------------------- */
function initSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!toggle || !sidebar || !overlay) return;

    const close = () => {
        sidebar.classList.remove('is-open');
        overlay.classList.remove('is-open');
    };

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('is-open');
        overlay.classList.toggle('is-open');
    });
    overlay.addEventListener('click', close);
}

/* User avatar dropdown -------------------------------------------------------- */
function initUserMenu() {
    const toggle = document.getElementById('userMenuToggle');
    const menu = document.getElementById('userMenu');
    if (!toggle || !menu) return;

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        menu.classList.toggle('is-open');
    });
    document.addEventListener('click', (e) => {
        if (!menu.contains(e.target)) menu.classList.remove('is-open');
    });
}

/* Creator mini profile popups (one open at a time) -------------------------- */
function initCreatorPopups() {
    const triggers = document.querySelectorAll('[data-creator-trigger]');

    triggers.forEach((trigger) => {
        const popup = trigger.querySelector('.creator-popup');
        if (!popup) return;

        // Move the popup out of the card into <body>, so the card's
        // overflow:hidden (needed for rounded media thumbnails) can't
        // clip it anymore. Position is calculated fresh on every open.
        document.body.appendChild(popup);

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasOpen = popup.classList.contains('is-open');
            document.querySelectorAll('.creator-popup.is-open').forEach((p) => p.classList.remove('is-open'));

            if (!wasOpen) {
                const rect = trigger.getBoundingClientRect();
                popup.style.top = `${rect.bottom + 6}px`;
                popup.style.left = `${rect.left}px`;
                popup.classList.add('is-open');
            }
        });
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.creator-popup.is-open').forEach((p) => p.classList.remove('is-open'));
    });
}

/* Like buttons (visual only for now — no backend yet) ------------------------ */
function initLikeButtons() {
    document.querySelectorAll('[data-like-trigger]').forEach((btn) => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('is-active');
            const countEl = btn.querySelector('.action-count');
            if (!countEl) return;
            const current = parseInt(countEl.textContent, 10) || 0;
            countEl.textContent = btn.classList.contains('is-active') ? current + 1 : current - 1;
        });
    });
}

/* Comments section toggle ---------------------------------------------------- */
function initCommentToggles() {
    document.querySelectorAll('[data-comment-trigger]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const container = btn.closest('.content-card, .content-player');
            const panel = container?.querySelector('.content-card__comments, .content-player__comments');
            if (panel) panel.hidden = !panel.hidden;
        });
    });
}

/* Content player actions --------------------------------------------------- */
function initContentPlayerActions() {
    document.querySelectorAll('[data-share-trigger]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(window.location.href);
                btn.textContent = 'Link copied';
                window.setTimeout(() => { btn.textContent = 'Share'; }, 1800);
            } catch {
                window.prompt('Copy this link:', window.location.href);
            }
        });
    });

    document.querySelectorAll('[data-fullscreen-trigger]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const player = btn.closest('.content-player');
            if (player?.requestFullscreen) player.requestFullscreen();
        });
    });
}

/* Subscription detail popups (one open at a time) --------------------------- */
function initSubscriptionPopups() {
    const triggers = document.querySelectorAll('[data-subscription-trigger]');

    triggers.forEach((trigger) => {
        const popup = trigger.querySelector('.subscription-popup');
        if (!popup) return;

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            if (e.target.closest('[data-stop-propagation]')) return;
            const wasOpen = popup.classList.contains('is-open');
            document.querySelectorAll('.subscription-popup.is-open').forEach((p) => p.classList.remove('is-open'));
            if (!wasOpen) popup.classList.add('is-open');
        });
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.subscription-popup.is-open').forEach((p) => p.classList.remove('is-open'));
    });
}
