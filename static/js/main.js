document.addEventListener('DOMContentLoaded', () => {
    const inits = [
        initParticles, initSidebar, initUserMenu, initCreatorPopups,
        initLikeButtons, initSaveButtons, initCommentToggles, initSubscriptionPopups,
        initDeleteConfirmations, initFileInputs, initEmojiPickers, initWatchHistory, initContentPlayerActions,
    ];
    inits.forEach((fn) => {
        try {
            fn();
        } catch (err) {
            console.error(`${fn.name} failed:`, err);
        }
    });
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

/* Persistent like buttons ---------------------------------------------------- */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    return parts.length === 2 ? parts.pop().split(';').shift() : '';
}

async function initLikeButtons() {
    document.querySelectorAll('[data-like-trigger]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            if (btn.dataset.loginUrl) {
                window.location.href = btn.dataset.loginUrl;
                return;
            }
            if (btn.dataset.loading === 'true') return;
            btn.dataset.loading = 'true';

            try {
                const response = await fetch(btn.dataset.likeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to like this content.');

                btn.classList.toggle('is-active', data.liked);
                const countEl = btn.querySelector('.action-count');
                if (countEl) countEl.textContent = data.count;
            } catch (err) {
                console.error(err);
            } finally {
                btn.dataset.loading = 'false';
            }
        });
    });
}

/* Saved for later ------------------------------------------------------------ */
async function initSaveButtons() {
    document.querySelectorAll('[data-save-trigger]').forEach((btn) => {
        btn.addEventListener('click', async (event) => {
            event.preventDefault();
            event.stopPropagation();

            if (btn.dataset.loginUrl) {
                window.location.href = btn.dataset.loginUrl;
                return;
            }
            if (btn.dataset.loading === 'true') return;
            btn.dataset.loading = 'true';

            try {
                const response = await fetch(btn.dataset.saveUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to save this item.');

                btn.classList.toggle('is-active', data.saved);
                const label = btn.querySelector('.action-label, .save-label, span:last-child');
                if (label) label.textContent = data.saved ? 'Saved' : (btn.classList.contains('collection-card__save') ? 'Save' : 'Save');

                if (!data.saved && btn.closest('.saved-page')) {
                    const card = btn.closest('.content-card, .collection-card');
                    const section = btn.closest('.saved-section');
                    if (card) card.remove();
                    const countEl = section?.querySelector('.saved-section__count');
                    if (countEl) {
                        const count = Math.max(0, Number(countEl.textContent) - 1);
                        countEl.textContent = count;
                    }
                    if (section && !section.querySelector('.content-card, .collection-card')) {
                        const empty = document.createElement('div');
                        empty.className = 'saved-empty';
                        empty.innerHTML = btn.classList.contains('collection-card__save')
                            ? '<span class="saved-empty__icon">📚</span><h3>No collections saved</h3><p>Save a collection and it will appear here.</p>'
                            : '<span class="saved-empty__icon">🔖</span><h3>Nothing saved yet</h3><p>Use the Save button on content you want to find again later.</p>';
                        const grid = section.querySelector('.content-grid, .collection-grid');
                        grid?.replaceWith(empty);
                    }
                }
            } catch (err) {
                console.error(err);
            } finally {
                btn.dataset.loading = 'false';
            }
        });
    });
}

/* Comments ------------------------------------------------------------------- */
function renderComment(comment) {
    const article = document.createElement('article');
    article.className = 'comment-item';
    article.dataset.commentId = comment.id;

    let avatar;
    if (comment.author_avatar_url) {
        avatar = document.createElement('img');
        avatar.className = 'avatar avatar--sm avatar--image comment-item__avatar';
        avatar.src = comment.author_avatar_url;
        avatar.alt = comment.author_name;
        avatar.style.objectPosition = `${comment.author_avatar_position_x ?? 50}% ${comment.author_avatar_position_y ?? 50}%`;
    } else {
        avatar = document.createElement('span');
        avatar.className = 'avatar avatar--sm comment-item__avatar';
        avatar.textContent = comment.author_initial;
    }

    const body = document.createElement('div');
    body.className = 'comment-item__body';

    const header = document.createElement('div');
    header.className = 'comment-item__header';

    const author = document.createElement('strong');
    author.textContent = comment.author_name;

    const time = document.createElement('time');
    time.className = 'comment-item__time';
    time.dateTime = comment.created_at;
    time.textContent = comment.time_ago || 'just now';

    header.append(author, time);

    const text = document.createElement('p');
    text.className = 'comment-item__text';
    text.textContent = comment.body;

    body.append(header, text);
    article.append(avatar, body);
    return article;
}

function initCommentToggles() {
    document.querySelectorAll('[data-comment-trigger]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const container = btn.closest('.content-card, .content-player');
            const panel = container?.querySelector('.content-card__comments, .content-player__comments');
            if (!panel) return;
            panel.hidden = !panel.hidden;
            if (!panel.hidden) {
                const input = panel.querySelector('textarea, input');
                if (input) input.focus();
            }
        });
    });

    document.querySelectorAll('[data-comment-form]').forEach((form) => {
        const textarea = form.querySelector('[name="body"]');
        const submit = form.querySelector('button[type="submit"]');
        const cancel = form.querySelector('[data-comment-cancel]');

        const resize = () => {
            if (!textarea) return;
            textarea.style.height = '40px';
            textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
            textarea.style.overflowY = textarea.scrollHeight > 150 ? 'auto' : 'hidden';
        };

        const updateSubmitState = () => {
            if (submit) submit.disabled = !textarea?.value.trim();
        };

        textarea?.addEventListener('input', () => {
            resize();
            updateSubmitState();
        });
        textarea?.addEventListener('focus', resize);

        cancel?.addEventListener('click', () => {
            if (!textarea) return;
            textarea.value = '';
            resize();
            updateSubmitState();
            textarea.blur();
        });

        resize();
        updateSubmitState();

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const body = textarea?.value.trim();
            if (!body || form.dataset.loading === 'true') return;

            form.dataset.loading = 'true';
            if (submit) submit.disabled = true;
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: new URLSearchParams({ body }),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to post comment.');

                const panel = form.closest('.content-card__comments, .content-player__comments');
                const list = panel?.querySelector('.comments-list');
                const empty = panel?.querySelector('.comments-empty');
                if (empty) empty.remove();
                if (list) list.appendChild(renderComment(data));

                const container = form.closest('.content-card, .content-player');
                const countEl = container?.querySelector('.comment-count');
                if (countEl && data.count !== undefined) {
                    countEl.textContent = `Comments (${data.count})`;
                }

                textarea.value = '';
                resize();
            } catch (err) {
                console.error(err);
            } finally {
                form.dataset.loading = 'false';
                updateSubmitState();
            }
        });
    });
}

/* Emoji picker -------------------------------------------------------------- */
const KALEIDO_EMOJIS = [
    '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃',
    '😉', '😌', '😍', '🥰', '😘', '😎', '🤩', '🥳', '😏', '😅', '🤔', '🫡',
    '😮', '😯', '😲', '🥺', '😭', '😤', '😡', '🤯', '😱', '😴', '🤗', '🤭',
    '🤫', '🫠', '🤪', '😈', '👻', '💀', '☠️', '👽', '🤖', '💜', '🖤', '🤍',
    '❤️', '🧡', '💛', '💚', '💙', '🩵', '🩷', '💫', '✨', '🔥', '⭐', '🌙',
    '🌟', '💥', '🎉', '🎊', '🎁', '🎮', '🎵', '🎶', '🎨', '📸', '💡', '🚀',
    '👍', '👎', '👏', '🙌', '🤝', '🙏', '💪', '👀', '👋', '❤️‍🔥', '💯', '✅',
    '❌', '⚡', '💎', '🏆', '🌈', '☀️', '🌧️', '🍀', '🌸', '🌹', '🍕', '☕',
];

function initEmojiPickers() {
    const fields = Array.from(document.querySelectorAll('textarea, input.field-input'))
        .filter((field) => {
            if (field.disabled || field.readOnly) return false;
            if (field.tagName === 'INPUT' && field.type !== 'text') return false;
            if (field.tagName === 'INPUT') {
                const haystack = `${field.id} ${field.name} ${field.placeholder}`.toLowerCase();
                if (haystack.includes('search') || field.name === 'q') return false;
            }
            return true;
        });

    if (!fields.length) return;

    const closeAll = (except = null) => {
        document.querySelectorAll('.emoji-picker.is-open').forEach((picker) => {
            if (picker === except) return;
            picker.classList.remove('is-open');
            const trigger = picker.parentElement?.querySelector('.emoji-input__trigger');
            trigger?.setAttribute('aria-expanded', 'false');
        });
    };

    fields.forEach((field) => {
        if (field.dataset.emojiReady === 'true') return;
        field.dataset.emojiReady = 'true';

        const wrapper = document.createElement('div');
        wrapper.className = 'emoji-input';
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(field);

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'emoji-input__trigger';
        button.setAttribute('aria-label', 'Add emoji');
        button.setAttribute('aria-expanded', 'false');
        button.textContent = '😊';

        const picker = document.createElement('div');
        picker.className = 'emoji-picker';
        picker.setAttribute('role', 'dialog');
        picker.setAttribute('aria-label', 'Emoji picker');

        const header = document.createElement('div');
        header.className = 'emoji-picker__header';
        header.textContent = 'Add an emoji';
        picker.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'emoji-picker__grid';
        KALEIDO_EMOJIS.forEach((emoji) => {
            const emojiButton = document.createElement('button');
            emojiButton.type = 'button';
            emojiButton.className = 'emoji-picker__item';
            emojiButton.textContent = emoji;
            emojiButton.setAttribute('aria-label', `Insert ${emoji}`);
            emojiButton.addEventListener('click', (event) => {
                event.stopPropagation();
                const start = field.selectionStart ?? field.value.length;
                const end = field.selectionEnd ?? start;
                field.setRangeText(emoji, start, end, 'end');
                field.dispatchEvent(new Event('input', { bubbles: true }));
                field.focus();
            });
            grid.appendChild(emojiButton);
        });
        picker.appendChild(grid);

        wrapper.append(button, picker);

        button.addEventListener('click', (event) => {
            event.stopPropagation();
            const willOpen = !picker.classList.contains('is-open');
            closeAll(picker);
            picker.classList.toggle('is-open', willOpen);
            button.setAttribute('aria-expanded', String(willOpen));
            if (willOpen) field.focus();
        });

        picker.addEventListener('click', (event) => event.stopPropagation());
    });

    document.addEventListener('click', () => closeAll());
}

/* Watch history + video resume ---------------------------------------------- */
function initWatchHistory() {
    document.querySelectorAll('[data-history-video]').forEach((video) => {
        const url = video.dataset.historyUrl;
        if (!url) return;

        const savedPosition = Number.parseFloat(video.dataset.resumePosition || '0');
        let lastSavedAt = 0;
        let saving = false;
        let hasMetadata = false;

        const saveProgress = async (completed = false, keepalive = false) => {
            if (!hasMetadata || saving) return;
            const position = Number.isFinite(video.currentTime) ? video.currentTime : 0;
            const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : '';
            const body = new URLSearchParams({
                csrfmiddlewaretoken: getCookie('csrftoken'),
                position: String(position),
                duration: String(duration),
                completed: completed ? 'true' : 'false',
            });

            saving = true;
            try {
                await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    },
                    body,
                    keepalive,
                });
                lastSavedAt = Date.now();
            } catch (err) {
                if (!keepalive) console.error('Unable to save watch progress:', err);
            } finally {
                saving = false;
            }
        };

        video.addEventListener('loadedmetadata', () => {
            hasMetadata = true;
            if (savedPosition > 0 && Number.isFinite(video.duration) && savedPosition < Math.max(video.duration - 2, 0)) {
                try {
                    video.currentTime = savedPosition;
                } catch {
                    // Some browsers may reject seeking before the media is ready.
                }
            }
        }, { once: true });

        video.addEventListener('timeupdate', () => {
            if (!hasMetadata || video.paused) return;
            if (Date.now() - lastSavedAt >= 5000) saveProgress(false);
        });

        video.addEventListener('pause', () => saveProgress(false));
        video.addEventListener('ended', () => saveProgress(true));
        window.addEventListener('beforeunload', () => saveProgress(false, true));
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') saveProgress(false, true);
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

/* Generic delete confirmation modal — any form with class "js-confirm-delete" */
function initDeleteConfirmations() {
    const overlay = document.getElementById('confirmModalOverlay');
    const messageEl = document.getElementById('confirmModalMessage');
    const cancelBtn = document.getElementById('confirmModalCancel');
    const confirmBtn = document.getElementById('confirmModalConfirm');
    if (!overlay || !messageEl || !cancelBtn || !confirmBtn) return;

    let pendingForm = null;

    document.querySelectorAll('form.js-confirm-delete, form.js-confirm-action').forEach((form) => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            pendingForm = form;
            messageEl.textContent = form.dataset.confirmMessage || 'Are you sure? This cannot be undone.';
            confirmBtn.textContent = form.dataset.confirmButtonText || 'Delete';
            overlay.classList.add('is-open');
        });
    });

    cancelBtn.addEventListener('click', () => {
        overlay.classList.remove('is-open');
        pendingForm = null;
    });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('is-open');
            pendingForm = null;
        }
    });
    confirmBtn.addEventListener('click', () => {
        if (pendingForm) pendingForm.submit();
        overlay.classList.remove('is-open');
    });
}

/* File inputs — replaces the ugly native "Seleccionar archivo" button with
   a styled, English button + filename, on every file input site-wide. */
function initFileInputs() {
    document.querySelectorAll('input[type="file"]').forEach((input) => {
        if (input.hidden || input.dataset.enhanced) return;
        input.dataset.enhanced = 'true';

        const wrapper = document.createElement('div');
        wrapper.className = 'file-input-wrapper';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn--ghost btn--sm file-input-wrapper__button';
        button.textContent = 'Choose file';

        const label = document.createElement('span');
        label.className = 'file-input-wrapper__filename';
        label.textContent = 'No file chosen';

        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(button);
        wrapper.appendChild(label);
        input.classList.add('file-input-wrapper__native');

        button.addEventListener('click', () => input.click());
        input.addEventListener('change', () => {
            label.textContent = input.files.length ? input.files[0].name : 'No file chosen';
        });
    });
}