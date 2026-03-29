/**
 * AI Agent Frontend Application
 * Handles chat interactions, code preview, and UI state management.
 */

(function () {
    'use strict';

    // --- DOM Elements ---
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const previewPanel = document.getElementById('previewPanel');
    const previewFrame = document.getElementById('previewFrame');
    const previewPlaceholder = document.getElementById('previewPlaceholder');
    const previewToggle = document.getElementById('previewToggle');
    const closePreview = document.getElementById('closePreview');
    const openNewTab = document.getElementById('openNewTab');
    const newChatBtn = document.getElementById('newChatBtn');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const suggestionCards = document.querySelectorAll('.suggestion-card');

    // --- State ---
    let chatHistory = [];
    let isLoading = false;
    let lastGeneratedCode = '';

    // --- API ---
    const API_URL = '/api/chat';

    async function sendMessage(userMessage) {
        if (isLoading || !userMessage.trim()) return;
        isLoading = true;

        // Hide welcome screen
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
        }

        // Add user message
        appendMessage('user', userMessage);
        chatHistory.push({ role: 'user', content: userMessage });

        // Clear input
        messageInput.value = '';
        autoResize(messageInput);
        updateSendButton();

        // Show typing indicator
        const typingEl = showTypingIndicator();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage,
                    history: chatHistory.slice(-10) // last 10 messages for context
                }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Server error (${response.status})`);
            }

            const data = await response.json();

            // Check if backend included an agent badge e.g. "**[Frontend Agent]**"
            let agentName = "AI Agent";
            let responseText = data.response;
            const badgeMatch = responseText.match(/^\*\*\[(.*?)\]\*\*\s*\n\n/);
            
            if (badgeMatch) {
                agentName = badgeMatch[1];
                responseText = responseText.replace(badgeMatch[0], "");
            }

            // Remove typing indicator
            typingEl.remove();

            // Add assistant response
            appendMessage('assistant', responseText, agentName);
            chatHistory.push({ role: 'assistant', content: data.response });

            // Auto-detect and show preview for HTML content
            const htmlCode = extractHTMLCode(responseText);
            if (htmlCode) {
                lastGeneratedCode = htmlCode;
                showPreview(htmlCode);
            }

        } catch (error) {
            typingEl.remove();
            appendMessage('assistant', `⚠️ Error: ${error.message}\n\nMake sure the server is running and your OpenAI API key is set in the .env file.`, "System");
        } finally {
            isLoading = false;
        }
    }

    // --- Message Rendering ---

    function appendMessage(role, content, agentNameStr = "AI Agent") {
        const messageEl = document.createElement('div');
        
        // Add agent-specific class based on name
        let agentClass = "";
        if (role === 'assistant') {
            if (agentNameStr.includes('PM')) agentClass = "agent-pm";
            else if (agentNameStr.includes('R&D') || agentNameStr.includes('RD')) agentClass = "agent-rd";
            else if (agentNameStr.includes('Frontend')) agentClass = "agent-frontend";
            else if (agentNameStr.includes('Backend')) agentClass = "agent-backend";
            else if (agentNameStr.includes('Tester')) agentClass = "agent-tester";
            else if (agentNameStr.includes('DevOps')) agentClass = "agent-devops";
            else agentClass = "agent-orchestrator";
        }
        
        messageEl.className = `message ${role} ${agentClass}`;

        let avatar = role === 'user' ? 'U' : 'AI';
        
        if (role === 'assistant') {
            if (agentClass === "agent-pm") avatar = "PM";
            else if (agentClass === "agent-rd") avatar = "R&D";
            else if (agentClass === "agent-frontend") avatar = "FE";
            else if (agentClass === "agent-backend") avatar = "BE";
            else if (agentClass === "agent-tester") avatar = "QA";
            else if (agentClass === "agent-devops") avatar = "DO";
        }

        const roleName = role === 'user' ? 'You' : `<span class="agent-badge">${agentNameStr}</span>`;

        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-role">${roleName}</div>
                <div class="message-body">${formatMessage(content)}</div>
            </div>
        `;

        chatMessages.appendChild(messageEl);
        scrollToBottom();

        // Attach event listeners to new code block buttons
        messageEl.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = decodeURIComponent(btn.dataset.code);
                navigator.clipboard.writeText(code).then(() => {
                    btn.textContent = '✓ Copied';
                    setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
                });
            });
        });

        messageEl.querySelectorAll('.preview-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = decodeURIComponent(btn.dataset.code);
                lastGeneratedCode = code;
                showPreview(code);
            });
        });
    }

    function formatMessage(text) {
        // Handle code blocks with language
        text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            lang = lang || 'code';
            const encoded = encodeURIComponent(code.trim());
            const isHTML = lang.toLowerCase() === 'html' && (code.includes('<!DOCTYPE') || code.includes('<html'));

            let actions = `<button class="code-action-btn copy-btn" data-code="${encoded}">Copy</button>`;
            if (isHTML) {
                actions += `<button class="code-action-btn preview-btn" data-code="${encoded}">▶ Preview</button>`;
            }

            return `<div class="code-block-wrapper">
                <div class="code-block-header">
                    <span class="code-block-lang">${lang}</span>
                    <div class="code-block-actions">${actions}</div>
                </div>
                <pre><code>${escapeHtml(code.trim())}</code></pre>
            </div>`;
        });

        // Handle inline code
        text = text.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.06);padding:2px 6px;border-radius:4px;font-family:var(--font-mono);font-size:13px;">$1</code>');

        // Handle bold text
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Handle italic text
        text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Handle line breaks and paragraphs
        text = text.replace(/\n\n/g, '</p><p>');
        text = text.replace(/\n/g, '<br>');

        // Wrap in paragraph if not already structured
        if (!text.startsWith('<div') && !text.startsWith('<p')) {
            text = `<p>${text}</p>`;
        }

        return text;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- HTML Code Extraction ---

    function extractHTMLCode(text) {
        // Try to find HTML code blocks
        const codeBlockMatch = text.match(/```html\n([\s\S]*?)```/);
        if (codeBlockMatch) {
            return codeBlockMatch[1].trim();
        }

        // Try to find raw HTML (starts with <!DOCTYPE or <html)
        const htmlMatch = text.match(/(<!DOCTYPE html[\s\S]*<\/html>)/i);
        if (htmlMatch) {
            return htmlMatch[1].trim();
        }

        return null;
    }

    // --- Preview Panel ---

    function showPreview(htmlCode) {
        previewPanel.classList.add('open');
        previewToggle.classList.add('active');
        previewPlaceholder.classList.add('hidden');

        // Write HTML to iframe
        const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
        doc.open();
        doc.write(htmlCode);
        doc.close();
    }

    function togglePreview() {
        if (previewPanel.classList.contains('open')) {
            previewPanel.classList.remove('open');
            previewToggle.classList.remove('active');
        } else {
            previewPanel.classList.add('open');
            previewToggle.classList.add('active');
        }
    }

    // --- Typing Indicator ---

    function showTypingIndicator() {
        const el = document.createElement('div');
        el.className = 'typing-indicator';
        el.innerHTML = `
            <div class="message-avatar" style="background: var(--gradient-primary); color: white;">AI</div>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatMessages.appendChild(el);
        scrollToBottom();
        return el;
    }

    // --- Utility ---

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }

    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }

    function updateSendButton() {
        sendBtn.disabled = !messageInput.value.trim() || isLoading;
    }

    function newChat() {
        chatHistory = [];
        lastGeneratedCode = '';
        chatMessages.innerHTML = '';

        // Re-add welcome screen
        if (welcomeScreen) {
            chatMessages.appendChild(welcomeScreen);
            welcomeScreen.style.display = '';
        }

        // Reset preview
        previewPanel.classList.remove('open');
        previewToggle.classList.remove('active');
        previewPlaceholder.classList.remove('hidden');
        const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
        doc.open();
        doc.write('');
        doc.close();
    }

    // --- Event Listeners ---

    // Send message
    sendBtn.addEventListener('click', () => {
        sendMessage(messageInput.value);
    });

    // Enter to send (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(messageInput.value);
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        autoResize(messageInput);
        updateSendButton();
    });

    // Suggestion cards
    suggestionCards.forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.dataset.prompt;
            messageInput.value = prompt;
            updateSendButton();
            sendMessage(prompt);
        });
    });

    // Preview toggle
    previewToggle.addEventListener('click', togglePreview);
    closePreview.addEventListener('click', () => {
        previewPanel.classList.remove('open');
        previewToggle.classList.remove('active');
    });

    // Open in new tab
    openNewTab.addEventListener('click', () => {
        if (lastGeneratedCode) {
            const blob = new Blob([lastGeneratedCode], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
        }
    });

    // New chat
    newChatBtn.addEventListener('click', newChat);

    // Mobile menu
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });

    // Focus input on load
    messageInput.focus();

})();
