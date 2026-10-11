/**
 * script.js
 * Advanced Frontend for Oli AI Agent.
 * Features:
 * - Multi-Step Thought Process Accordion
 * - Voice Input (Speech-to-Text)
 * - Read Aloud (Text-to-Speech)
 * - Copy to Clipboard
 * - Theme Switcher (Dark/Light)
 * - Chat Transcript Export (Markdown)
 * - Category Chip Filtering
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const body = document.body;
  const chatForm = document.getElementById('chatForm');
  const messageInput = document.getElementById('messageInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const messagesList = document.getElementById('messagesList');
  const chatContainer = document.getElementById('chatContainer');
  const welcomeCard = document.getElementById('welcomeCard');
  const typingIndicator = document.getElementById('typingIndicator');
  const resetBtn = document.getElementById('resetBtn');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const exportBtn = document.getElementById('exportBtn');
  const errorBanner = document.getElementById('errorBanner');
  const errorMessage = document.getElementById('errorMessage');
  const dismissError = document.getElementById('dismissError');
  const categoryTabs = document.querySelectorAll('.cat-tab');
  const chipButtons = document.querySelectorAll('.chip-btn');

  // Track full chat history for export
  const fullTranscript = [];

  // Theme Management
  const savedTheme = localStorage.getItem('oli_theme') || 'light';
  body.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  themeToggleBtn.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('oli_theme', newTheme);
    updateThemeIcon(newTheme);
  });

  function updateThemeIcon(theme) {
    themeToggleBtn.querySelector('.theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  // Session ID for memory
  let sessionId = localStorage.getItem('oli_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    localStorage.setItem('oli_session_id', sessionId);
  }

  messageInput.focus();

  function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove('hidden');
    setTimeout(() => errorBanner.classList.add('hidden'), 6000);
  }

  dismissError.addEventListener('click', () => {
    errorBanner.classList.add('hidden');
  });

  // Category Tab Filtering
  categoryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      categoryTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const category = tab.getAttribute('data-cat');

      chipButtons.forEach(chip => {
        const chipCat = chip.getAttribute('data-cat');
        if (category === 'all' || chipCat === category || chipCat === 'all') {
          chip.style.display = 'inline-flex';
        } else {
          chip.style.display = 'none';
        }
      });
    });
  });

  // Suggestion chips
  chipButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) sendMessage(prompt);
    });
  });

  // Voice Input (Speech Recognition)
  let recognition = null;
  let isListening = false;

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('listening');
      micBtn.title = 'Listening... Click to stop';
    };

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      messageInput.value = transcript;
      sendMessage(transcript);
    };

    recognition.onerror = (e) => {
      console.warn('Speech error:', e.error);
      micBtn.classList.remove('listening');
      isListening = false;
    };

    recognition.onend = () => {
      micBtn.classList.remove('listening');
      isListening = false;
    };

    micBtn.addEventListener('click', () => {
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  } else {
    micBtn.style.display = 'none'; // Not supported
  }

  // Text to Speech
  function speakText(text) {
    if (!('speechSynthesis' in window)) return;
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      return;
    }
    // Clean markdown symbols for cleaner voice
    const cleanText = text.replace(/[*_#`\[\]]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }

  // Markdown renderer
  function renderMarkdown(text) {
    if (!text) return '';
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Link [text](url)
    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    const lines = escaped.split('\n');
    let inList = false;
    let formattedLines = [];

    for (let line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
        if (!inList) {
          formattedLines.push('<ul>');
          inList = true;
        }
        formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
      } else {
        if (inList) {
          formattedLines.push('</ul>');
          inList = false;
        }
        if (trimmed.length > 0) {
          formattedLines.push(`<p>${line}</p>`);
        }
      }
    }
    if (inList) formattedLines.push('</ul>');

    return formattedLines.join('');
  }

  // Append message to chat
  function appendMessage(sender, text, toolUsed = null, thoughtSteps = []) {
    if (welcomeCard) welcomeCard.style.display = 'none';

    fullTranscript.push({
      sender: sender === 'user' ? 'User' : 'Oli',
      text: text,
      tool: toolUsed,
      time: new Date().toLocaleTimeString()
    });

    const row = document.createElement('div');
    row.className = `message-row ${sender === 'user' ? 'user-row' : 'oli-row'}`;

    if (sender === 'oli') {
      const avatar = document.createElement('div');
      avatar.className = 'avatar-small';
      avatar.textContent = 'O';
      row.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // 1. Render Thought Process Accordion (if available)
    if (sender === 'oli' && thoughtSteps && thoughtSteps.length > 0) {
      const thoughtBox = document.createElement('div');
      thoughtBox.className = 'thought-box';

      const thoughtHeader = document.createElement('div');
      thoughtHeader.className = 'thought-header';
      thoughtHeader.innerHTML = `<span>💭 Agent Thought Process (${thoughtSteps.length} steps)</span> <span class="toggle-icon">▾</span>`;

      const thoughtBody = document.createElement('div');
      thoughtBody.className = 'thought-body hidden';

      thoughtSteps.forEach(step => {
        const stepRow = document.createElement('div');
        stepRow.className = 'thought-step';
        stepRow.innerHTML = `
          <span class="thought-step-icon">${step.icon || '•'}</span>
          <div class="thought-step-detail">
            <span class="thought-step-title">${step.step}:</span>
            <span>${step.detail}</span>
          </div>
        `;
        thoughtBody.appendChild(stepRow);
      });

      thoughtHeader.addEventListener('click', () => {
        thoughtBody.classList.toggle('hidden');
        thoughtHeader.querySelector('.toggle-icon').textContent = thoughtBody.classList.contains('hidden') ? '▾' : '▴';
      });

      thoughtBox.appendChild(thoughtHeader);
      thoughtBox.appendChild(thoughtBody);
      bubble.appendChild(thoughtBox);
    }

    // 2. Render Tool Badge
    if (sender === 'oli' && toolUsed) {
      const toolBadge = document.createElement('div');
      toolBadge.className = 'tool-badge';
      const badges = {
        calculator: '🧮 <span>Used Calculator Tool</span>',
        datetime: '🕒 <span>Used Date/Time Tool</span>',
        unit_converter: '🔄 <span>Used Unit Converter Tool</span>',
        notes: '📝 <span>Used Notes Scratchpad Tool</span>',
        todos: '📋 <span>Used Task Manager Tool</span>',
        knowledge: '🌐 <span>Used Wikipedia Knowledge Tool</span>'
      };
      toolBadge.innerHTML = badges[toolUsed] || `🔧 <span>Used Tool: ${toolUsed}</span>`;
      bubble.appendChild(toolBadge);
    }

    // 3. Message Body
    const contentDiv = document.createElement('div');
    if (sender === 'oli') {
      contentDiv.innerHTML = renderMarkdown(text);
    } else {
      contentDiv.textContent = text;
    }
    bubble.appendChild(contentDiv);

    // 4. Action Pills (Copy & Read Aloud for Oli's messages)
    if (sender === 'oli') {
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'msg-actions';

      const copyBtn = document.createElement('button');
      copyBtn.className = 'action-pill';
      copyBtn.innerHTML = '📋 Copy';
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(text);
        copyBtn.innerHTML = '✅ Copied!';
        setTimeout(() => copyBtn.innerHTML = '📋 Copy', 2000);
      });

      const listenBtn = document.createElement('button');
      listenBtn.className = 'action-pill';
      listenBtn.innerHTML = '🔊 Listen';
      listenBtn.addEventListener('click', () => {
        speakText(text);
      });

      actionsDiv.appendChild(copyBtn);
      actionsDiv.appendChild(listenBtn);
      bubble.appendChild(actionsDiv);
    }

    row.appendChild(bubble);
    messagesList.appendChild(row);
    scrollToBottom();
  }

  // Send message
  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    appendMessage('user', trimmed);
    messageInput.value = '';

    messageInput.disabled = true;
    sendBtn.disabled = true;
    typingIndicator.classList.remove('hidden');
    scrollToBottom();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: sessionId })
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        const errText = data.error || 'Server error. Please try again.';
        showError(errText);
        appendMessage('oli', `⚠️ **Error**: ${errText}`);
      } else {
        appendMessage('oli', data.response, data.tool_used, data.thought_steps);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      const networkErrMsg = 'Unable to connect to Oli backend. Ensure server is running.';
      showError(networkErrMsg);
      appendMessage('oli', `⚠️ **Connection Error**: ${networkErrMsg}`);
    } finally {
      typingIndicator.classList.add('hidden');
      messageInput.disabled = false;
      sendBtn.disabled = false;
      messageInput.focus();
      scrollToBottom();
    }
  }

  // Form submit
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(messageInput.value);
  });

  // Reset chat
  resetBtn.addEventListener('click', async () => {
    if (!confirm('Start a new chat and reset memory?')) return;
    try {
      await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      messagesList.innerHTML = '';
      fullTranscript.length = 0;
      if (welcomeCard) welcomeCard.style.display = 'block';
      messageInput.value = '';
      messageInput.focus();
    } catch (err) {
      showError('Could not reset memory on server.');
    }
  });

  // Export Transcript
  exportBtn.addEventListener('click', () => {
    if (fullTranscript.length === 0) {
      alert('No messages to export yet.');
      return;
    }

    let md = `# Oli AI Agent - Conversation Transcript\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
    fullTranscript.forEach(item => {
      md += `### ${item.sender} (${item.time})\n${item.tool ? `*Tool Used: ${item.tool}*\n\n` : ''}${item.text}\n\n---\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `oli_chat_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
});
