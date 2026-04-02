let isSignupMode = false;
let activeChatHistory = []; // --- CONVERSATIONAL MEMORY ---

// --- AUTH ---
function checkAuth() {
    const token = sessionStorage.getItem('token');
    if (token) {
        document.getElementById('authView').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('authView').style.display = 'none';
            document.getElementById('appView').style.display = 'flex';
            document.getElementById('appView').style.opacity = '0';
            setTimeout(() => document.getElementById('appView').style.opacity = '1', 50);
        }, 400);

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const user = payload.sub || "User";
            document.getElementById('userNameDisp').innerText = user;
            document.getElementById('userInitial').innerText = user[0].toUpperCase();
        } catch (e) { console.error("Token parse error:", e); }

        loadHistory();
    } else {
        resetUI();
    }
}

function resetUI() {
    // --- ABSOLUTE PRIVACY: Wipe everything ---
    document.getElementById('authView').style.display = 'flex';
    document.getElementById('authView').style.opacity = '1';
    document.getElementById('appView').style.display = 'none';

    // Clear Auth Inputs
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('authError').innerText = '';

    // Clear History & Memory
    document.getElementById('historyList').innerHTML = '';
    activeChatHistory = [];

    // Clear Profile
    document.getElementById('userNameDisp').innerText = 'User';
    document.getElementById('userInitial').innerText = 'U';

    // Reset Chat Feed
    document.getElementById('chatArea').innerHTML = '';
    appendMessage('Hello! I am DocuMind. Upload an SOP document to begin chatting.', false, null);

    // Reset Doc Name & Status
    document.getElementById('activeDocName').innerText = "DocuMind Enterprise";
    const statusEl = document.getElementById('uploadStatus');
    statusEl.innerText = "Ready";
    statusEl.className = "status-ready";
    document.getElementById('statusHighlightBtn').style.display = "inline-flex";
}

function toggleAuthMode() {
    isSignupMode = !isSignupMode;
    document.getElementById('authTitle').innerText = isSignupMode ? 'DocuMind Signup' : 'DocuMind Login';
    const btn = document.getElementById('authBtn');
    btn.innerText = isSignupMode ? 'Sign Up' : 'Login';
    document.querySelector('.auth-toggle').innerText = isSignupMode ? 'Already have an account? Login' : 'New account? Sign up';
    document.getElementById('authError').innerText = '';
}

async function handleAuth() {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const btn = document.getElementById('authBtn');
    if (!u || !p) return;

    btn.disabled = true;
    const originalText = isSignupMode ? 'Sign Up' : 'Login';
    btn.innerHTML = '<span class="spinner"></span> Authenticating...';

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

    try {
        if (isSignupMode) {
            const res = await fetch('/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                document.getElementById('authError').style.color = 'var(--accent-emerald)';
                document.getElementById('authError').innerText = "Account created! Switching to login...";
                setTimeout(() => {
                    toggleAuthMode();
                    document.getElementById('authError').style.color = 'var(--accent-rose)';
                    document.getElementById('authError').innerText = '';
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }, 1500);
            } else {
                const err = await res.json();
                document.getElementById('authError').innerText = err.detail || 'Signup failed';
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        } else {
            const fd = new URLSearchParams();
            fd.append('username', u);
            fd.append('password', p);
            const res = await fetch('/login', {
                method: 'POST',
                body: fd,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                const d = await res.json();
                sessionStorage.setItem('token', d.access_token);
                btn.innerHTML = '✓ Welcome!';
                setTimeout(() => checkAuth(), 300);
            } else {
                document.getElementById('authError').innerText = 'Access Denied: Invalid Credentials';
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            document.getElementById('authError').innerText = 'Connection timeout (15s). Check server and try again.';
        } else {
            document.getElementById('authError').innerText = 'Connection error. Is the server running?';
        }
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function logout() {
    sessionStorage.removeItem('token');
    activeChatHistory = []; // Clear conversational memory
    newChat();
    checkAuth();
}

// --- API WRAPPER ---
async function authFetch(url, options = {}) {
    const token = sessionStorage.getItem('token');
    if (!options.headers) options.headers = {};
    if (token) options.headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(url, options);
    if (res.status === 401) { logout(); throw new Error("Session Expired"); }
    return res;
}

// --- CORE ---
function appendMessage(text, isUser = false, sources = null) {
    const container = document.getElementById('chatArea');
    const wrapper = document.createElement('div');
    wrapper.className = 'message-container';

    let sourcesHtml = '';
    if (!isUser && sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-container" style="display:block">
                <div class="sources-title">
                    <svg class="icon" style="width:14px; height:14px; vertical-align:middle; margin-right:6px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                    Verified Context
                </div>
                ${sources.map(s => `<span class="source-tag">${s}</span>`).join('')}
            </div>
        `;
    }

    let buttonHtml = '';
    // Share button removed - use Share Session button in header instead

    wrapper.innerHTML = `
        <div class="message ${isUser ? 'user' : 'bot'}">
            <div class="message-avatar">${isUser ? 'U' : 'AI'}</div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                ${sourcesHtml}
            </div>
        </div>
    `;
    container.appendChild(wrapper);
    
    setTimeout(() => {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }, 100);
}

function newChat() {
    activeChatHistory = []; // Reset conversational memory
    document.getElementById('chatArea').innerHTML = '';
    appendMessage('New Session Started. Upload an SOP document to begin chatting.', false, null);
    document.getElementById('activeDocName').innerText = "DocuMind Enterprise";
    const statusEl = document.getElementById('uploadStatus')
    statusEl.innerText = "Ready";
    statusEl.className = "status-ready";
    document.getElementById('statusHighlightBtn').style.display = "inline-flex";
    document.getElementById('shareSessionBtn').style.display = 'none';
}

async function loadHistory() {
    try {
        const res = await authFetch('/history');
        const data = await res.json();
        const list = document.getElementById('historyList');
        list.innerHTML = '';
        
        data.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.style.animation = `messageEnter 0.4s var(--transition-smooth) ${index * 0.05}s both`;
            div.innerText = item.question;
            div.onclick = () => { 
                newChat(); // Clear and show this session
                appendMessage(item.question, true); 
                appendMessage(item.answer, false); 
            };
            list.prepend(div);
        });
    } catch(e) { console.error("History load error:", e); }
}

async function uploadDocument() {
    const fileInput = document.getElementById('pdfFile');
    const f = fileInput.files[0];
    if(!f) return;
    
    const fd = new FormData(); fd.append('file', f);
    const statusEl = document.getElementById('uploadStatus');
    statusEl.innerText = "Indexing...";
    statusEl.className = "status-indexing";
    document.getElementById('statusHighlightBtn').style.display = "none";
    
    try {
        const res = await authFetch('/ingest', { method: 'POST', body: fd });
        if (res.ok) {
            statusEl.innerText = "Ready ✔";
            statusEl.className = "status-ready";
            document.getElementById('statusHighlightBtn').style.display = "inline-flex";
            document.getElementById('activeDocName').innerText = f.name;
            document.getElementById('shareSessionBtn').style.display = 'inline-flex';
            appendMessage(`Successfully indexed: ${f.name}. You can now start asking questions.`, false);
        } else {
            const err = await res.json();
            statusEl.innerText = "Upload Error";
            statusEl.className = "status-error";
            document.getElementById('statusHighlightBtn').style.display = "none";
            appendMessage("Error during ingestion: " + (err.detail || "Unknown error"), false);
        }
    } catch(e) { 
        statusEl.innerText = "Connection Error";
        statusEl.className = "status-error";
        document.getElementById('statusHighlightBtn').style.display = "none";
    } finally {
        fileInput.value = ''; 
    }
}

async function askQuestion() {
    const input = document.getElementById('questionInput');
    const rawText = input.value.trim();
    if(!rawText) return;

    // Split into separate questions based on newlines
    const questions = rawText.split('\n').map(q => q.trim()).filter(q => q.length > 0);
    if (questions.length === 0) return;

    // UI Reset
    input.value = '';
    input.style.height = 'auto'; // Reset textarea height
    appendMessage(rawText, true); // Display original input in chat bubble
    
    const chatArea = document.getElementById('chatArea');
    const typingWrapper = document.createElement('div');
    typingWrapper.className = 'message-container';
    typingWrapper.id = 'typingIndicator';
    typingWrapper.innerHTML = `
        <div class="message bot">
            <div class="message-avatar">AI</div>
            <div class="typing">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>
    `;
    chatArea.appendChild(typingWrapper);
    chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });

    try {
        let res, data;
        
        if (questions.length === 1) {
            // SINGLE QUESTION MODE
            res = await authFetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: questions[0],
                    chat_history: activeChatHistory
                })
            });
            data = await res.json();
            
            if(document.getElementById('typingIndicator')) document.getElementById('typingIndicator').remove();

            if(res.ok) { 
                lastQuestion = questions[0];
                lastSources = data.sources || [];
                appendMessage(data.answer, false, data.sources || null); 
                activeChatHistory.push({ role: "user", content: questions[0] });
                activeChatHistory.push({ role: "assistant", content: data.answer });
            } else {
                appendMessage("Error: " + (data.detail || "Server error"), false);
            }
        } else {
            // BATCH QUESTIONS MODE
            res = await authFetch('/batch-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    questions: questions,
                    chat_history: activeChatHistory
                })
            });
            data = await res.json();

            if(document.getElementById('typingIndicator')) document.getElementById('typingIndicator').remove();

            if(res.ok) {
                renderBatchResponse(data.results);
                // Add all to history
                data.results.forEach(r => {
                    activeChatHistory.push({ role: "user", content: r.question });
                    activeChatHistory.push({ role: "assistant", content: r.answer });
                });
            } else {
                appendMessage("Batch processing error: " + (data.detail || "Server error"), false);
            }
        }

        // Keep history lean (last 10 exchanges = 20 messages)
        if (activeChatHistory.length > 20) activeChatHistory = activeChatHistory.slice(-20);
        loadHistory(); 

    } catch(e) { 
        if(document.getElementById('typingIndicator')) document.getElementById('typingIndicator').remove();
        appendMessage("Server unreachable. Please check your connection.", false); 
    }
}

function renderBatchResponse(results) {
    const chatArea = document.getElementById('chatArea');
    const container = document.createElement('div');
    container.className = 'message-container';
    
    let html = `
        <div class="message bot">
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="message-text" style="margin-bottom:20px; font-weight:600; color:var(--accent-indigo);">Batch Analysis Complete:</div>
                <div class="batch-container">
    `;

    results.forEach((item, index) => {
        const sourceHtml = item.sources && item.sources.length > 0 ? 
            `<div class="sources-container" style="display:block; margin-top:16px; border-left-width:2px; padding:12px;">
                <div class="sources-title" style="font-size:0.7rem;">Sources</div>
                ${item.sources.map(s => `<span class="source-tag" style="font-size:0.75rem; padding:2px 8px;">${s}</span>`).join('')}
            </div>` : '';

        html += `
            <div class="batch-item">
                <div class="batch-question">
                    <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    Question ${index+1}
                </div>
                <div class="batch-answer">${item.answer}</div>
                ${sourceHtml}
            </div>
        `;
    });

    html += `</div></div></div></div>`;
    container.innerHTML = html;
    chatArea.appendChild(container);
    chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });
}

// Initialize
window.onload = () => {
    checkAuth();
    // Default class for status
    const statusEl = document.getElementById('uploadStatus');
    if(statusEl) {
        statusEl.className = "status-ready";
        document.getElementById('statusHighlightBtn').style.display = "inline-flex";
    }
};

// Highlight Ready Status Function
function highlightReady() {
    const btn = document.getElementById('statusHighlightBtn');
    btn.style.animation = 'none';
    setTimeout(() => {
        btn.style.animation = 'pulse 0.6s ease-out';
    }, 10);
}

// --- SHARE FUNCTIONS ---
async function shareEntireSession() {
    const docName = document.getElementById('activeDocName').innerText || 'SOP';
    const chatArea = document.getElementById('chatArea');
    const messages = chatArea.querySelectorAll('.message-container');
    
    // Extract all Q&A pairs from the chat
    const sessionMessages = [];
    messages.forEach((msgContainer, index) => {
        const messageDiv = msgContainer.querySelector('.message');
        const isUser = messageDiv.classList.contains('user');
        const text = msgContainer.querySelector('.message-text').textContent;
        sessionMessages.push({
            role: isUser ? 'user' : 'assistant',
            content: text
        });
    });

    if (sessionMessages.length === 0) {
        alert('No messages to share yet!');
        return;
    }

    const modal = document.getElementById('shareModal');
    
    try {
        // Call backend to create session share link
        const response = await authFetch('/share-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_messages: sessionMessages,
                document_name: docName
            })
        });

        if (response.ok) {
            const data = await response.json();
            const fullUrl = window.location.origin + data.share_url;
            
            document.getElementById('shareUrlInput').value = fullUrl;
            document.getElementById('shareTextInput').value = `Share this DocuMind session: ${fullUrl}`;
            modal.style.display = 'flex';
            modal.style.animation = 'modalPop 0.3s ease-out';
        } else {
            alert('Failed to create share link');
        }
    } catch (e) {
        console.error('Share error:', e);
        alert('Error sharing session: ' + e.message);
    }
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    element.select();
    document.execCommand('copy');
    
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✓ Copied!';
    btn.style.background = 'var(--accent-emerald)';
    
    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.style.background = '';
    }, 2000);
}