document.addEventListener('DOMContentLoaded', () => {
    const trigger   = document.getElementById('askvera-trigger');
    const bubble    = document.querySelector('.askvera-bubble');
    const windowEl  = document.getElementById('askvera-window');
    const closeBtn  = document.getElementById('askvera-close');
    const input     = document.getElementById('askvera-input');
    const sendBtn   = document.getElementById('askvera-send');
    const messages  = document.getElementById('askvera-messages');

    // ── Role & page context ───────────────────────────────────────────────────
    // Expose these in your base Jinja2 template BEFORE loading this script:
    //   <script>
    //     const CURRENT_USER_ROLE = "{{ current_user.role if current_user.is_authenticated else 'guest' }}";
    //     const CURRENT_PAGE = "{{ request.endpoint }}";
    //   </script>
    const USER_ROLE = (typeof CURRENT_USER_ROLE !== 'undefined') ? CURRENT_USER_ROLE : 'guest';
    const PAGE_NAME = (typeof CURRENT_PAGE      !== 'undefined') ? CURRENT_PAGE      : window.location.pathname;

    // ── Role-aware suggestion chips ───────────────────────────────────────────
    const ROLE_SUGGESTIONS = {
        admin: [
            "How do I approve a service listing?",
            "How do I reject a skill submission?",
            "How do I manage users?",
            "How do I add a new category?",
            "Where can I see all platform orders?",
        ],
        provider: [
            "How do I create a service listing?",
            "How do I accept or reject an order?",
            "How do I set my availability slots?",
            "How do I mark an order as complete?",
            "Why was my skill submission rejected?",
        ],
        customer: [
            "How do I place an order?",
            "How do I book a session?",
            "How do I track my order?",
            "How do I download my certificate?",
            "How do I leave a review?",
        ],
        guest: [
            "How do I sign up?",
            "How do I find a service?",
            "How do I place an order?",
            "What categories are available?",
        ],
    };

    let isOpen         = false;
    let hasInitialized = false;

    // ── Open / close ──────────────────────────────────────────────────────────
    const toggleChat = () => {
        isOpen = !isOpen;
        windowEl.classList.toggle('hidden', !isOpen);

        trigger.style.display = isOpen ? 'none' : 'flex';
        if (bubble) bubble.style.display = isOpen ? 'none' : 'block';

        if (isOpen && !hasInitialized) {
            // Show role-specific chips immediately — no extra network call needed
            const chips = ROLE_SUGGESTIONS[USER_ROLE] || ROLE_SUGGESTIONS.guest;
            appendSuggestions(chips);
            hasInitialized = true;
        }

        if (isOpen) input.focus();
    };

    trigger.onclick = toggleChat;
    closeBtn.onclick = toggleChat;

    // ── Append a chat bubble ──────────────────────────────────────────────────
    function appendMessage(text, type) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';

        if (type === 'ai') {
            avatar.innerHTML = '<img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="AI" style="width:100%;height:100%;object-fit:cover;">';
            avatar.style.background = 'transparent';
        } else {
            avatar.innerHTML = '<i class="bi bi-person-fill"></i>';
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');

        wrapper.appendChild(avatar);
        wrapper.appendChild(msgDiv);
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    // ── Typing indicator ──────────────────────────────────────────────────────
    function showTyping() {
        const id = 'typing-' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper ai';
        wrapper.id = id;
        wrapper.innerHTML = `
            <div class="message-avatar" style="background:transparent">
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="AI"
                     style="width:100%;height:100%;object-fit:cover;">
            </div>
            <div class="message">
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>`;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // ── Send a message ────────────────────────────────────────────────────────
    async function sendMessage(overrideText) {
        const text = (overrideText !== undefined ? overrideText : input.value).trim();
        if (!text) return;

        // Clear any existing suggestion chips before sending
        messages.querySelectorAll('.askvera-suggestions').forEach(el => el.remove());

        appendMessage(text, 'user');
        input.value = '';
        sendBtn.disabled = true;

        const typingId = showTyping();

        try {
            const res = await fetch('/chat/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message:   text,
                    context:   { page: PAGE_NAME },
                    user_role: USER_ROLE,        // ← passed to chat_manager.py
                }),
            });

            const data = await res.json();
            removeTyping(typingId);

            if (data.error && data.fallback) {
                appendMessage("Sorry, I'm having trouble connecting right now. Please try again.", 'ai');
            } else {
                appendMessage(data.response || data.error || "I didn't get that — could you rephrase?", 'ai');
                if (data.suggestions && data.suggestions.length > 0) {
                    appendSuggestions(data.suggestions);
                }
            }
        } catch (e) {
            removeTyping(typingId);
            appendMessage("Connection error. Please check your internet and try again.", 'ai');
            console.error('AskVera error:', e);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    // ── Render suggestion chips ───────────────────────────────────────────────
    function appendSuggestions(suggestions) {
        const container = document.createElement('div');
        container.className = 'askvera-suggestions';

        suggestions.forEach(text => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = text;
            chip.onclick = () => {
                messages.querySelectorAll('.askvera-suggestions').forEach(el => el.remove());
                sendMessage(text);
            };
            container.appendChild(chip);
        });

        messages.appendChild(container);
        messages.scrollTop = messages.scrollHeight;
    }

    // ── Event listeners ───────────────────────────────────────────────────────
    sendBtn.onclick = () => sendMessage();
    input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
});