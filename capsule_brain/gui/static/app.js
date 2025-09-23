/**
 * Modern Capsule Brain GUI Application
 * Enhanced with modern JavaScript features, better UX, and advanced functionality
 * Version 4.0 - PWA Ready with Advanced Features
 */

class CapsuleBrainApp {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.currentPanel = 'chat';
    this.theme = this.getStoredTheme();
    this.settings = this.loadSettings();
    this.charts = {};
    this.notifications = [];
    this.fileList = [];
    this.messageHistory = [];
    this.keyboardShortcuts = new Map();
    this.modalStack = [];
    this.voiceRecognition = null;
    this.emojiPicker = null;
    this.isFullscreen = false;
    this.isSidebarCollapsed = false;
    this.connectionRetryCount = 0;
    this.maxRetries = 5;
    this.retryDelay = 1000;
    
    this.init();
  }

  init() {
    console.log('🚀 Initializing Capsule Brain App...');
    this.setupEventListeners();
    this.initializeTheme();
    
    // Initialize WebSocket asynchronously to not block the UI
    setTimeout(() => {
      this.initializeWebSocket();
    }, 100);
    
    this.initializeCharts();
    
    // Load system data asynchronously
    setTimeout(() => {
      this.loadSystemData();
    }, 200);
    
    this.hideLoadingScreen();
    console.log('✅ Capsule Brain App initialized successfully');
  }

  // Theme Management
  initializeTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateThemeIcon();
  }

  getStoredTheme() {
    const stored = localStorage.getItem('capsule-brain-theme');
    if (stored) return stored;
    
    // Auto-detect system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }

  toggleTheme() {
    this.theme = this.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', this.theme);
    localStorage.setItem('capsule-brain-theme', this.theme);
    this.updateThemeIcon();
    this.showNotification('Theme changed', 'success');
  }

  updateThemeIcon() {
    const icon = document.querySelector('.theme-icon');
    if (icon) {
      icon.textContent = this.theme === 'dark' ? '☀️' : '🌙';
    }
  }

  // Settings Management
  loadSettings() {
    const defaultSettings = {
      autoScroll: true,
      showTimestamps: false,
      refreshInterval: 5,
      fontSize: 14
    };
    
    const stored = localStorage.getItem('capsule-brain-settings');
    return stored ? { ...defaultSettings, ...JSON.parse(stored) } : defaultSettings;
  }

  saveSettings() {
    localStorage.setItem('capsule-brain-settings', JSON.stringify(this.settings));
  }

  updateSetting(key, value) {
    this.settings[key] = value;
    this.saveSettings();
    
    // Apply setting immediately
    if (key === 'fontSize') {
      document.documentElement.style.fontSize = `${value}px`;
    }
  }

  // WebSocket Management
  initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      this.isConnected = true;
      this.updateConnectionStatus('Connected', 'online');
      this.showNotification('Connected to Capsule Brain', 'success');
    };
    
    this.ws.onclose = () => {
      console.log('🔌 WebSocket connection closed');
      this.isConnected = false;
      this.updateConnectionStatus('Disconnected', 'offline');
      this.showNotification('Connection lost', 'warning');
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => this.initializeWebSocket(), 3000);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.updateConnectionStatus('Error', 'offline');
      this.showNotification('Connection error', 'error');
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleWebSocketMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }

  handleWebSocketMessage(message) {
    switch (message.type) {
      case 'phi_update':
        this.updateSystemMetrics(message.payload);
        // Also update thinking panel if it's active
        if (this.currentPanel === 'thinking') {
          this.loadThinkingData();
        }
        break;
      case 'wiring_proposal':
        this.showNotification('New self-wiring proposal received', 'info');
        // Update thinking panel with new proposal
        if (this.currentPanel === 'thinking') {
          this.loadThinkingData();
        }
        break;
      case 'agi_response':
        this.appendMessage(message.payload.answer, 'assistant');
        break;
      case 'overseer_action':
        this.showNotification(`Overseer: ${message.payload.description}`, 'info');
        // Update thinking panel with overseer action
        if (this.currentPanel === 'thinking') {
          this.loadThinkingData();
        }
        break;
      case 'belief_state_update':
        // Update thinking panel with new belief state
        if (this.currentPanel === 'thinking') {
          this.updateThinkingData(message.payload);
        }
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  // UI Management
  setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const panel = e.currentTarget.dataset.panel;
        this.switchPanel(panel);
      });
    });

    // Theme toggle
    document.getElementById('themeToggle')?.addEventListener('click', () => {
      this.toggleTheme();
    });

    // Chat functionality
    this.setupChatListeners();
    
    // System panel
    this.setupSystemListeners();
    
    // Thinking panel
    this.setupThinkingListeners();
    
    // Settings
    this.setupSettingsListeners();
    
    // File upload
    this.setupFileUpload();
  }

  setupChatListeners() {
  const chatInput = document.getElementById('chatInput');
  const sendButton = document.getElementById('sendButton');
    const clearChat = document.getElementById('clearChat');
    const exportChat = document.getElementById('exportChat');

    // Send message
    sendButton?.addEventListener('click', () => this.sendMessage());
    
    // Enter key handling
    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Character counter
    chatInput?.addEventListener('input', (e) => {
      this.updateCharacterCounter(e.target.value.length);
      this.updateSendButton(e.target.value.trim().length > 0);
    });

    // Clear chat
    clearChat?.addEventListener('click', () => {
      if (confirm('Are you sure you want to clear the conversation?')) {
        this.clearChat();
      }
    });

    // Export chat
    exportChat?.addEventListener('click', () => {
      this.exportChat();
    });
  }

  setupSystemListeners() {
    const refreshSystem = document.getElementById('refreshSystem');
    
    refreshSystem?.addEventListener('click', () => {
      this.loadSystemData();
      this.showNotification('System data refreshed', 'success');
    });

    // Overseer controls
    const enableOverseer = document.getElementById('enableOverseer');
    const disableOverseer = document.getElementById('disableOverseer');
    
    enableOverseer?.addEventListener('click', () => {
      this.enableOverseer();
    });
    
    disableOverseer?.addEventListener('click', () => {
      this.disableOverseer();
    });
  }

  setupThinkingListeners() {
    const refreshThinking = document.getElementById('refreshThinking');
    
    refreshThinking?.addEventListener('click', () => {
      this.loadThinkingData();
      this.showNotification('Thinking data refreshed', 'success');
    });
  }

  setupSettingsListeners() {
    // Theme selector
    const themeSelect = document.getElementById('themeSelect');
    themeSelect?.addEventListener('change', (e) => {
      this.theme = e.target.value === 'auto' ? 
        (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : 
        e.target.value;
      this.initializeTheme();
    });

    // Font size
    const fontSize = document.getElementById('fontSize');
    const fontSizeValue = document.getElementById('fontSizeValue');
    fontSize?.addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      this.updateSetting('fontSize', value);
      fontSizeValue.textContent = `${value}px`;
    });

    // Auto scroll
    const autoScroll = document.getElementById('autoScroll');
    autoScroll?.addEventListener('change', (e) => {
      this.updateSetting('autoScroll', e.target.checked);
    });

    // Show timestamps
    const showTimestamps = document.getElementById('showTimestamps');
    showTimestamps?.addEventListener('change', (e) => {
      this.updateSetting('showTimestamps', e.target.checked);
    });

    // Refresh interval
    const refreshInterval = document.getElementById('refreshInterval');
    refreshInterval?.addEventListener('change', (e) => {
      this.updateSetting('refreshInterval', parseInt(e.target.value));
    });
  }

  setupFileUpload() {
    const fileUpload = document.getElementById('fileUpload');
    const fileList = document.getElementById('fileList');

    fileUpload?.addEventListener('change', (e) => {
      this.handleFileSelection(Array.from(e.target.files));
    });
  }

  // Panel Management
  switchPanel(panelName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    document.querySelector(`[data-panel="${panelName}"]`)?.classList.add('active');

    // Update panels
    document.querySelectorAll('.panel').forEach(panel => {
      panel.classList.remove('active');
    });
    
    // Map panel names to actual IDs
    const panelIdMap = {
      'chat': 'chatPanel',
      'system': 'systemPanel',
      'thinking': 'thinkingPanel',
      'analytics': 'analyticsPanel',
      'settings': 'settingsPanel'
    };
    
    const panelId = panelIdMap[panelName];
    if (panelId) {
      document.getElementById(panelId)?.classList.add('active');
    }

    this.currentPanel = panelName;

    // Load panel-specific data
    if (panelName === 'system') {
      this.loadSystemData();
    } else if (panelName === 'thinking') {
      this.loadThinkingData();
    } else if (panelName === 'analytics') {
      this.loadAnalyticsData();
    }
  }

  // Chat Management
  async sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput?.value.trim();
    const files = this.fileList;

    if (!message && files.length === 0) return;

    // Add user message
    if (message) {
      this.appendMessage(message, 'user');
    }

    // Show thinking indicator
    this.showThinkingIndicator();
    
    // Show file processing indicator if files are attached
    if (files.length > 0) {
      this.showNotification(`Processing ${files.length} file(s)...`, 'info');
    }

    // Clear input
    chatInput.value = '';
    this.updateCharacterCounter(0);
    this.updateSendButton(false);

    try {
      let response;
      
      if (files.length > 0) {
        // Send with files
        const formData = new FormData();
        formData.append('q', message || 'Document question');
        files.forEach(file => {
          formData.append('file', file);
        });

        response = await fetch('/ask_with_document', {
          method: 'POST',
          body: formData
        });
      } else {
        // Send text only
        response = await fetch('/ask', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ q: message })
        });
      }

      const data = await response.json();
      
      // Hide thinking indicator
      this.hideThinkingIndicator();
      
      // Show file processing results if available
      if (data.file_processed) {
        const fileInfo = data.file_processed;
        this.showNotification(
          `File processed: ${fileInfo.filename} (${fileInfo.type}, ${fileInfo.size} bytes, ${fileInfo.extracted_length} chars extracted)`,
          'success'
        );
        
        // Add file processing info to chat
        this.appendMessage(
          `📄 **File Processed Successfully**\n` +
          `**Filename:** ${fileInfo.filename}\n` +
          `**Type:** ${fileInfo.type}\n` +
          `**Size:** ${fileInfo.size} bytes\n` +
          `**Content Extracted:** ${fileInfo.extracted_length} characters\n\n` +
          `**Content Preview:**\n${fileInfo.preview}`,
          'system'
        );
      }
      
      if (data.error) {
        this.appendMessage(`❌ **File Processing Error:** ${data.error}`, 'system');
      }
      
      if (data.llm_response?.text) {
        this.appendMessage(data.llm_response.text, 'assistant');
      } else {
        this.appendMessage('No response received', 'system');
      }

      // Clear files
      this.clearFiles();

    } catch (error) {
      console.error('Error sending message:', error);
      this.hideThinkingIndicator();
      this.appendMessage('Error: Request failed', 'system');
      this.showNotification('Failed to send message', 'error');
    }
  }

  showThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
      indicator.classList.remove('hidden');
    }
  }

  hideThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
      indicator.classList.add('hidden');
    }
  }

  appendMessage(content, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
      welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = window.marked?.parse(content) || content;

    messageDiv.appendChild(messageContent);

    // Add timestamp if enabled
    if (this.settings.showTimestamps) {
      const timestamp = document.createElement('div');
      timestamp.className = 'message-time';
      timestamp.textContent = new Date().toLocaleTimeString();
      messageDiv.appendChild(timestamp);
    }

    chatMessages.appendChild(messageDiv);

    // Auto-scroll if enabled
    if (this.settings.autoScroll) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Store in history
    this.messageHistory.push({
      content,
      sender,
      timestamp: new Date().toISOString()
    });
  }

  clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    chatMessages.innerHTML = `
      <div class="welcome-message">
        <div class="welcome-content">
          <div class="welcome-icon">🤖</div>
          <h3>Welcome to Capsule Brain Supreme AGI</h3>
          <p>I'm your advanced AI assistant. How can I help you today?</p>
        </div>
      </div>
    `;

    this.messageHistory = [];
    this.showNotification('Chat cleared', 'success');
  }

  exportChat() {
    if (this.messageHistory.length === 0) {
      this.showNotification('No messages to export', 'warning');
      return;
    }

    const exportData = {
      timestamp: new Date().toISOString(),
      messages: this.messageHistory
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `capsule-brain-chat-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    this.showNotification('Chat exported successfully', 'success');
  }

  // File Management
  handleFileSelection(files) {
    this.fileList = [...this.fileList, ...files];
    this.updateFileList();
  }

  updateFileList() {
    const fileList = document.getElementById('fileList');
    if (!fileList) return;

    fileList.innerHTML = '';

    this.fileList.forEach((file, index) => {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <span>${file.name}</span>
        <span class="file-remove" data-index="${index}">×</span>
      `;

      fileItem.querySelector('.file-remove').addEventListener('click', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.removeFile(index);
      });

      fileList.appendChild(fileItem);
    });
  }

  removeFile(index) {
    this.fileList.splice(index, 1);
    this.updateFileList();
  }

  clearFiles() {
    this.fileList = [];
    this.updateFileList();
    document.getElementById('fileUpload').value = '';
  }

  // System Data Management
  async loadSystemData() {
    try {
      const response = await fetch('/state/summary');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.updateSystemMetrics(data.self_awareness_metrics);
      this.updateSystemDetails(data);
      
      // Check system health
      this.checkSystemHealth(data);
    } catch (error) {
      console.error('Error loading system data:', error);
      this.showNotification(`Failed to load system data: ${error.message}`, 'error');
      this.updateConnectionStatus('Error', 'offline');
    }
  }

  checkSystemHealth(data) {
    const issues = [];
    
    // Check memory usage
    if (data.memory_size > 4000) {
      issues.push('High memory usage');
    }
    
    // Check uptime
    if (data.uptime_s < 60) {
      issues.push('System recently restarted');
    }
    
    // Check overseer status
    if (!data.overseer_enabled) {
      issues.push('AI Overseer disabled');
    }
    
    // Check graph health
    if (data.graph.nodes < 10) {
      issues.push('Knowledge graph underdeveloped');
    }
    
    if (issues.length > 0) {
      this.showNotification(`System warnings: ${issues.join(', ')}`, 'warning', 8000);
    } else {
      this.updateConnectionStatus('Healthy', 'online');
    }
  }

  // Thinking Data Management
  async loadThinkingData() {
    try {
      const response = await fetch('/state/summary');
        const data = await response.json();
      this.updateThinkingData(data);
    } catch (error) {
      console.error('Error loading thinking data:', error);
      this.showNotification('Failed to load thinking data', 'error');
    }
  }

  updateThinkingData(data) {
    // Update current query
    this.updateCurrentQuery(data.belief_state);
    
    // Update retrieved knowledge
    this.updateRetrievedKnowledge(data.belief_state);
    
    // Update current plan
    this.updateCurrentPlan(data.belief_state);
    
    // Update recent memories
    this.updateRecentMemories(data.recent_memories);
    
    // Update neural activity
    this.updateNeuralActivity(data.thinking_process);
  }

  updateCurrentQuery(beliefState) {
    const queryText = document.querySelector('#currentQuery .query-text');
    const queryTimestamp = document.getElementById('queryTimestamp');
    
    if (beliefState?.current_query) {
      queryText.textContent = beliefState.current_query;
      queryTimestamp.textContent = `Last updated: ${new Date(beliefState.last_update * 1000).toLocaleString()}`;
    } else {
      queryText.textContent = 'No active query';
      queryTimestamp.textContent = '';
    }
  }

  updateRetrievedKnowledge(beliefState) {
    const knowledgeList = document.getElementById('retrievedKnowledge');
    
    if (beliefState?.retrieved_knowledge && beliefState.retrieved_knowledge.length > 0) {
      knowledgeList.innerHTML = '';
      beliefState.retrieved_knowledge.forEach((knowledge, index) => {
        const item = document.createElement('div');
        item.className = 'knowledge-item';
        item.textContent = `${index + 1}. ${knowledge}`;
        knowledgeList.appendChild(item);
      });
    } else {
      knowledgeList.innerHTML = '<div class="knowledge-item">No knowledge retrieved</div>';
    }
  }

  updateCurrentPlan(beliefState) {
    const planDisplay = document.getElementById('currentPlan');
    
    if (beliefState?.current_plan && Object.keys(beliefState.current_plan).length > 0) {
      planDisplay.innerHTML = '';
      Object.entries(beliefState.current_plan).forEach(([key, value]) => {
        const item = document.createElement('div');
        item.className = 'plan-item';
        item.innerHTML = `<strong>${key}:</strong> ${JSON.stringify(value)}`;
        planDisplay.appendChild(item);
      });
    } else {
      planDisplay.innerHTML = '<div class="plan-item">No active plan</div>';
    }
  }

  updateRecentMemories(memories) {
    const memoriesList = document.getElementById('recentMemories');
    
    if (memories && memories.length > 0) {
      memoriesList.innerHTML = '';
      memories.forEach(memory => {
        const item = document.createElement('div');
        item.className = 'memory-item';
        
        const role = document.createElement('div');
        role.className = 'memory-role';
        role.textContent = memory.role || 'unknown';
        
        const content = document.createElement('div');
        content.className = 'memory-content';
        content.textContent = memory.content || 'No content';
        
        const timestamp = document.createElement('div');
        timestamp.className = 'memory-timestamp';
        timestamp.textContent = new Date(memory.ts * 1000).toLocaleString();
        
        item.appendChild(role);
        item.appendChild(content);
        item.appendChild(timestamp);
        memoriesList.appendChild(item);
      });
    } else {
      memoriesList.innerHTML = '<div class="memory-item">No memories available</div>';
    }
  }

  updateNeuralActivity(thinkingProcess) {
    const neuralPhi = document.getElementById('neuralPhi');
    const neuralGlyphs = document.getElementById('neuralGlyphs');
    const graphActivity = document.getElementById('graphActivity');
    
    if (thinkingProcess) {
      // Update Phi level
      if (neuralPhi && thinkingProcess.current_phi !== undefined) {
        neuralPhi.textContent = thinkingProcess.current_phi.toFixed(4);
      }
      
      // Update glyphs
      if (neuralGlyphs && thinkingProcess.neural_glyphs) {
        neuralGlyphs.textContent = thinkingProcess.neural_glyphs.join(' ') || '∅';
      }
      
      // Update graph activity
      if (graphActivity && thinkingProcess.graph_activity) {
        const activity = thinkingProcess.graph_activity;
        graphActivity.textContent = `${activity.recent_additions} recent additions`;
      }
    }
  }

  updateSystemMetrics(metrics) {
    if (!metrics) return;

    // Update Phi value
    const phiValue = document.getElementById('phiValue');
    if (phiValue && metrics.phi !== undefined) {
      phiValue.textContent = (+metrics.phi).toFixed(4);
    }

    // Update glyphs
    const glyphsValue = document.getElementById('glyphsValue');
    if (glyphsValue && metrics.glyphs) {
      glyphsValue.textContent = (metrics.glyphs || []).join(' ') || '∅';
    }

    // Update memory usage
    const memoryValue = document.getElementById('memoryValue');
    const memoryProgress = document.getElementById('memoryProgress');
    if (memoryValue && metrics.memory_size !== undefined) {
      memoryValue.textContent = metrics.memory_size;
      if (memoryProgress) {
        const percentage = Math.min((metrics.memory_size / 5000) * 100, 100);
        memoryProgress.style.width = `${percentage}%`;
      }
    }

    // Update uptime
    const uptimeValue = document.getElementById('uptimeValue');
    if (uptimeValue && metrics.uptime_s !== undefined) {
      uptimeValue.textContent = this.formatUptime(metrics.uptime_s);
    }
  }

  updateSystemDetails(data) {
    // Update graph details
    const graphNodes = document.getElementById('graphNodes');
    const graphEdges = document.getElementById('graphEdges');
    if (graphNodes && data.graph?.nodes !== undefined) {
      graphNodes.textContent = data.graph.nodes;
    }
    if (graphEdges && data.graph?.edges !== undefined) {
      graphEdges.textContent = data.graph.edges;
    }

    // Update principles
    const principlesList = document.getElementById('principlesList');
    if (principlesList && data.principles) {
      principlesList.innerHTML = '';
      data.principles.forEach(principle => {
        const item = document.createElement('div');
        item.className = 'principle-item';
        item.textContent = principle;
        principlesList.appendChild(item);
      });
    }

    // Update overseer status
    this.updateOverseerStatus(data.overseer_enabled);
  }

  updateOverseerStatus(enabled) {
    const overseerStatus = document.getElementById('overseerStatus');
    if (overseerStatus) {
      overseerStatus.textContent = enabled ? 'Enabled' : 'Disabled';
      overseerStatus.className = `status-value ${enabled ? 'enabled' : 'disabled'}`;
    }
  }

  async enableOverseer() {
    try {
      console.log('Attempting to enable overseer...');
      const response = await fetch('/overseer/enable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-admin-token': 'cb_admin_bfd38aaa245bdfcc3a756221be8e36ee'
        }
      });
      
      console.log('Overseer enable response:', response.status, response.statusText);
      
      if (response.ok) {
        this.showNotification('AI Overseer enabled', 'success');
        this.loadSystemData(); // Refresh to get updated status
      } else {
        const errorData = await response.json();
        console.error('Overseer enable error:', errorData);
        this.showNotification(`Error enabling overseer: ${errorData.detail || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error('Error enabling overseer:', error);
      this.showNotification('Error enabling overseer', 'error');
    }
  }

  async disableOverseer() {
    try {
      console.log('Attempting to disable overseer...');
      const response = await fetch('/overseer/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-admin-token': 'cb_admin_bfd38aaa245bdfcc3a756221be8e36ee'
        }
      });
      
      console.log('Overseer disable response:', response.status, response.statusText);
      
      if (response.ok) {
        this.showNotification('AI Overseer disabled', 'success');
        this.loadSystemData(); // Refresh to get updated status
      } else {
        const errorData = await response.json();
        console.error('Overseer disable error:', errorData);
        this.showNotification(`Error disabling overseer: ${errorData.detail || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error('Error disabling overseer:', error);
      this.showNotification('Error disabling overseer', 'error');
    }
  }

  formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  // Analytics
  initializeCharts() {
    // Initialize Chart.js charts
    this.initializePhiChart();
    this.initializeTokenChart();
  }

  initializePhiChart() {
    const ctx = document.getElementById('phiChart')?.getContext('2d');
    if (!ctx) return;

    this.charts.phi = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Phi (Consciousness Level)',
          data: [],
          borderColor: '#0ea5e9',
          backgroundColor: 'rgba(14, 165, 233, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          },
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          }
        },
        plugins: {
          legend: {
            labels: {
              color: '#e2e8f0'
            }
          }
        }
      }
    });
  }

  initializeTokenChart() {
    const ctx = document.getElementById('tokenChart')?.getContext('2d');
    if (!ctx) return;

    this.charts.tokens = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Prompt', 'Completion', 'Total'],
        datasets: [{
          label: 'Token Usage',
          data: [0, 0, 0],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(14, 165, 233, 0.8)'
          ],
          borderColor: [
            '#22c55e',
            '#a855f7',
            '#0ea5e9'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          },
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          }
        },
        plugins: {
          legend: {
            labels: {
              color: '#e2e8f0'
            }
          }
        }
      }
    });
  }

  loadAnalyticsData() {
    // Load analytics data from metrics endpoint
    fetch('/metrics')
      .then(response => response.text())
      .then(data => {
        // Parse Prometheus metrics and update charts
        this.parseMetricsData(data);
      })
      .catch(error => {
        console.error('Error loading analytics data:', error);
      });
  }

  parseMetricsData(metricsText) {
    // Simple Prometheus metrics parser
    const lines = metricsText.split('\n');
    const tokenData = { prompt: 0, completion: 0, total: 0 };

    lines.forEach(line => {
      if (line.includes('cb_tokens_total') && !line.startsWith('#')) {
        const match = line.match(/cb_tokens_total\{.*type="(\w+)".*\} (\d+)/);
        if (match) {
          const type = match[1];
          const value = parseInt(match[2]);
          if (type === 'prompt') tokenData.prompt = value;
          else if (type === 'completion') tokenData.completion = value;
          else if (type === 'total') tokenData.total = value;
        }
      }
    });

    // Update token chart
    if (this.charts.tokens) {
      this.charts.tokens.data.datasets[0].data = [
        tokenData.prompt,
        tokenData.completion,
        tokenData.total
      ];
      this.charts.tokens.update();
    }
  }

  // Utility Functions
  updateConnectionStatus(text, status) {
    const statusText = document.getElementById('statusText');
    const statusDot = document.querySelector('.status-dot');
    
    if (statusText) statusText.textContent = text;
    if (statusDot) {
      statusDot.className = `status-dot ${status}`;
    }
  }

  updateCharacterCounter(count) {
    const charCount = document.getElementById('charCount');
    if (charCount) {
      charCount.textContent = count;
      charCount.style.color = count > 3500 ? '#ef4444' : '#94a3b8';
    }
  }

  updateSendButton(enabled) {
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
      sendButton.disabled = !enabled;
    }
  }

  showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div>${message}</div>
      <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;

    // Add animation classes
    notification.style.animation = 'slideInRight 0.3s ease-out';
    
    container.appendChild(notification);

    // Auto-remove after specified duration
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
          if (notification.parentElement) {
            notification.remove();
          }
        }, 300);
      }
    }, duration);
  }

  hideLoadingScreen() {
    console.log('🔄 Attempting to hide loading screen...');
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
      console.log('✅ Loading screen element found');
      console.log('📊 Current loading screen state:', {
        classList: Array.from(loadingScreen.classList),
        display: loadingScreen.style.display,
        visibility: window.getComputedStyle(loadingScreen).visibility,
        opacity: window.getComputedStyle(loadingScreen).opacity
      });
      
      setTimeout(() => {
        console.log('🔄 Adding hidden class...');
        loadingScreen.classList.add('hidden');
        console.log('📊 After adding hidden class:', {
          classList: Array.from(loadingScreen.classList),
          display: window.getComputedStyle(loadingScreen).display
        });
        
        setTimeout(() => {
          console.log('🔄 Setting display to none...');
          loadingScreen.style.display = 'none';
          console.log('✅ Loading screen hidden successfully');
        }, 500);
      }, 1000);
    } else {
      console.error('❌ Loading screen element not found!');
    }
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 DOM Content Loaded - Starting initialization...');
  console.log('📊 DOM State:', {
    readyState: document.readyState,
    bodyExists: !!document.body,
    loadingScreenExists: !!document.getElementById('loadingScreen'),
    appContainerExists: !!document.getElementById('app')
  });
  
  try {
    console.log('🔄 Creating CapsuleBrainApp instance...');
    window.capsuleBrainApp = new CapsuleBrainApp();
    console.log('✅ CapsuleBrainApp created successfully');
  } catch (error) {
    console.error('❌ Error initializing Capsule Brain App:', error);
    console.error('❌ Error stack:', error.stack);
    
    // Fallback: hide loading screen even if there's an error
    console.log('🔄 Fallback: Hiding loading screen due to error...');
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
      loadingScreen.style.display = 'none';
      console.log('✅ Loading screen hidden via fallback');
    } else {
      console.error('❌ Loading screen not found for fallback');
    }
  }
});

// Fallback: hide loading screen after 3 seconds regardless
setTimeout(() => {
  const loadingScreen = document.getElementById('loadingScreen');
  if (loadingScreen && !loadingScreen.classList.contains('hidden')) {
    console.log('⚠️ Fallback: Hiding loading screen after timeout');
    loadingScreen.classList.add('hidden');
    setTimeout(() => {
      loadingScreen.style.display = 'none';
    }, 500);
  }
}, 3000);

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && window.capsuleBrainApp) {
    window.capsuleBrainApp.loadSystemData();
  }
});

// Handle window resize for responsive charts
window.addEventListener('resize', () => {
  if (window.capsuleBrainApp?.charts) {
    Object.values(window.capsuleBrainApp.charts).forEach(chart => {
      if (chart && typeof chart.resize === 'function') {
        chart.resize();
      }
    });
  }
});

// ===== MODERN GUI ENHANCEMENTS =====

// Enhanced Keyboard Shortcuts
CapsuleBrainApp.prototype.setupKeyboardShortcuts = function() {
  this.keyboardShortcuts.set('ctrl+enter', () => this.sendMessage());
  this.keyboardShortcuts.set('ctrl+k', () => this.focusSearch());
  this.keyboardShortcuts.set('ctrl+/', () => this.showKeyboardShortcuts());
  this.keyboardShortcuts.set('ctrl+d', () => this.toggleTheme());
  this.keyboardShortcuts.set('ctrl+f', () => this.focusInput());
  this.keyboardShortcuts.set('escape', () => this.closeModals());
  this.keyboardShortcuts.set('ctrl+1', () => this.switchPanel('chat'));
  this.keyboardShortcuts.set('ctrl+2', () => this.switchPanel('system'));
  this.keyboardShortcuts.set('ctrl+3', () => this.switchPanel('thinking'));
  this.keyboardShortcuts.set('ctrl+4', () => this.switchPanel('analytics'));
  this.keyboardShortcuts.set('ctrl+5', () => this.switchPanel('settings'));
  this.keyboardShortcuts.set('ctrl+shift+h', () => this.toggleSidebar());
  this.keyboardShortcuts.set('f11', () => this.toggleFullscreen());
};

// Enhanced Event Listeners
CapsuleBrainApp.prototype.setupEnhancedEventListeners = function() {
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => this.handleKeyboardShortcut(e));
  
  // Enhanced file upload
  const fileUploadArea = document.getElementById('fileUploadArea');
  if (fileUploadArea) {
    fileUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
    fileUploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
    fileUploadArea.addEventListener('click', () => this.triggerFileUpload());
  }
  
  // Voice input
  const voiceInput = document.getElementById('voiceInput');
  if (voiceInput) {
    voiceInput.addEventListener('click', () => this.toggleVoiceInput());
  }
  
  // Emoji picker
  const emojiPicker = document.getElementById('emojiPicker');
  if (emojiPicker) {
    emojiPicker.addEventListener('click', () => this.toggleEmojiPicker());
  }
  
  // Sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => this.toggleSidebar());
  }
  
  // Fullscreen toggle
  const fullscreenToggle = document.getElementById('fullscreenToggle');
  if (fullscreenToggle) {
    fullscreenToggle.addEventListener('click', () => this.toggleFullscreen());
  }
  
  // Help toggle
  const helpToggle = document.getElementById('helpToggle');
  if (helpToggle) {
    helpToggle.addEventListener('click', () => this.showKeyboardShortcuts());
  }
  
  // Character count
  const messageInput = document.getElementById('messageInput');
  if (messageInput) {
    messageInput.addEventListener('input', () => this.updateCharacterCount());
  }
  
  // Message actions
  document.addEventListener('click', (e) => this.handleMessageAction(e));
  
  // Panel actions
  document.addEventListener('click', (e) => this.handlePanelAction(e));
};

// Keyboard Shortcut Handler
CapsuleBrainApp.prototype.handleKeyboardShortcut = function(e) {
  const key = this.getKeyboardShortcutKey(e);
  const handler = this.keyboardShortcuts.get(key);
  
  if (handler) {
    e.preventDefault();
    handler();
  }
};

// Get Keyboard Shortcut Key
CapsuleBrainApp.prototype.getKeyboardShortcutKey = function(e) {
  const keys = [];
  if (e.ctrlKey) keys.push('ctrl');
  if (e.shiftKey) keys.push('shift');
  if (e.altKey) keys.push('alt');
  if (e.metaKey) keys.push('meta');
  
  const key = e.key.toLowerCase();
  if (key === ' ') keys.push('space');
  else if (key === 'escape') keys.push('escape');
  else if (key === 'enter') keys.push('enter');
  else if (key === 'tab') keys.push('tab');
  else if (key === 'backspace') keys.push('backspace');
  else if (key === 'delete') keys.push('delete');
  else if (key === 'arrowup') keys.push('arrowup');
  else if (key === 'arrowdown') keys.push('arrowdown');
  else if (key === 'arrowleft') keys.push('arrowleft');
  else if (key === 'arrowright') keys.push('arrowright');
  else if (key.length === 1) keys.push(key);
  else keys.push(key);
  
  return keys.join('+');
};

// Enhanced File Upload
CapsuleBrainApp.prototype.handleDragOver = function(e) {
  e.preventDefault();
  e.currentTarget.classList.add('drag-over');
};

CapsuleBrainApp.prototype.handleFileDrop = function(e) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  
  const files = Array.from(e.dataTransfer.files);
  this.handleFiles(files);
};

CapsuleBrainApp.prototype.triggerFileUpload = function() {
  const fileInput = document.getElementById('fileInput');
  if (fileInput) {
    fileInput.click();
  }
};

CapsuleBrainApp.prototype.handleFiles = function(files) {
  files.forEach(file => {
    if (this.validateFile(file)) {
      this.addFileToList(file);
    } else {
      this.showNotification(`Invalid file: ${file.name}`, 'error');
    }
  });
};

CapsuleBrainApp.prototype.validateFile = function(file) {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'application/zip',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown'
  ];
  
  return file.size <= maxSize && allowedTypes.includes(file.type);
};

CapsuleBrainApp.prototype.addFileToList = function(file) {
  const fileList = document.getElementById('fileList');
  if (!fileList) return;
  
  fileList.style.display = 'block';
  
  const fileItem = document.createElement('div');
  fileItem.className = 'file-item';
  fileItem.innerHTML = `
    <span class="file-name">${file.name}</span>
    <span class="file-size">${this.formatFileSize(file.size)}</span>
    <button class="file-remove" data-file="${file.name}">×</button>
  `;
  
  fileList.appendChild(fileItem);
  this.fileList.push(file);
  
  // Add remove functionality
  const removeBtn = fileItem.querySelector('.file-remove');
  removeBtn.addEventListener('click', () => this.removeFile(file.name));
};

CapsuleBrainApp.prototype.removeFile = function(fileName) {
  this.fileList = this.fileList.filter(file => file.name !== fileName);
  
  const fileItems = document.querySelectorAll('.file-item');
  fileItems.forEach(item => {
    if (item.querySelector(`[data-file="${fileName}"]`)) {
      item.remove();
    }
  });
  
  const fileList = document.getElementById('fileList');
  if (fileList && this.fileList.length === 0) {
    fileList.style.display = 'none';
  }
};

CapsuleBrainApp.prototype.formatFileSize = function(bytes) {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

// Voice Input
CapsuleBrainApp.prototype.toggleVoiceInput = function() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    this.showNotification('Voice input not supported in this browser', 'warning');
    return;
  }
  
  if (this.voiceRecognition) {
    this.stopVoiceInput();
  } else {
    this.startVoiceInput();
  }
};

CapsuleBrainApp.prototype.startVoiceInput = function() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  this.voiceRecognition = new SpeechRecognition();
  
  this.voiceRecognition.continuous = false;
  this.voiceRecognition.interimResults = false;
  this.voiceRecognition.lang = 'en-US';
  
  this.voiceRecognition.onstart = () => {
    this.showNotification('Listening...', 'info');
    document.getElementById('voiceInput').classList.add('recording');
  };
  
  this.voiceRecognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
      messageInput.value = transcript;
      this.updateCharacterCount();
    }
  };
  
  this.voiceRecognition.onend = () => {
    document.getElementById('voiceInput').classList.remove('recording');
  };
  
  this.voiceRecognition.onerror = (e) => {
    this.showNotification('Voice input error: ' + e.error, 'error');
    document.getElementById('voiceInput').classList.remove('recording');
  };
  
  this.voiceRecognition.start();
};

CapsuleBrainApp.prototype.stopVoiceInput = function() {
  if (this.voiceRecognition) {
    this.voiceRecognition.stop();
    this.voiceRecognition = null;
  }
};

// Emoji Picker
CapsuleBrainApp.prototype.toggleEmojiPicker = function() {
  // Simple emoji picker implementation
  const emojis = ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈', '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '☠️', '👽', '👾', '🤖', '🎃', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾'];
  
  const picker = document.createElement('div');
  picker.className = 'emoji-picker';
  picker.innerHTML = `
    <div class="emoji-grid">
      ${emojis.map(emoji => `<span class="emoji-option" data-emoji="${emoji}">${emoji}</span>`).join('')}
    </div>
  `;
  
  // Position picker
  const button = document.getElementById('emojiPicker');
  const rect = button.getBoundingClientRect();
  picker.style.position = 'fixed';
  picker.style.top = (rect.bottom + 5) + 'px';
  picker.style.left = rect.left + 'px';
  picker.style.zIndex = '1000';
  
  document.body.appendChild(picker);
  
  // Add click handlers
  picker.addEventListener('click', (e) => {
    if (e.target.classList.contains('emoji-option')) {
      const emoji = e.target.dataset.emoji;
      const messageInput = document.getElementById('messageInput');
      if (messageInput) {
        messageInput.value += emoji;
        this.updateCharacterCount();
      }
      picker.remove();
    }
  });
  
  // Close on outside click
  setTimeout(() => {
    document.addEventListener('click', () => picker.remove(), { once: true });
  }, 0);
};

// Sidebar Management
CapsuleBrainApp.prototype.toggleSidebar = function() {
  this.isSidebarCollapsed = !this.isSidebarCollapsed;
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  
  if (sidebar && toggle) {
    sidebar.setAttribute('aria-expanded', !this.isSidebarCollapsed);
    toggle.setAttribute('aria-expanded', !this.isSidebarCollapsed);
    
    if (this.isSidebarCollapsed) {
      sidebar.classList.add('collapsed');
    } else {
      sidebar.classList.remove('collapsed');
    }
  }
};

// Fullscreen Management
CapsuleBrainApp.prototype.toggleFullscreen = function() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().then(() => {
      this.isFullscreen = true;
      this.showNotification('Entered fullscreen mode', 'info');
    });
  } else {
    document.exitFullscreen().then(() => {
      this.isFullscreen = false;
      this.showNotification('Exited fullscreen mode', 'info');
    });
  }
};

// Character Count
CapsuleBrainApp.prototype.updateCharacterCount = function() {
  const messageInput = document.getElementById('messageInput');
  const charCount = document.getElementById('charCount');
  
  if (messageInput && charCount) {
    const count = messageInput.value.length;
    const maxLength = parseInt(messageInput.getAttribute('maxlength')) || 4000;
    charCount.textContent = `${count}/${maxLength}`;
    
    if (count > maxLength * 0.9) {
      charCount.style.color = 'var(--warning)';
    } else if (count > maxLength * 0.8) {
      charCount.style.color = 'var(--accent-500)';
    } else {
      charCount.style.color = 'var(--neutral-500)';
    }
  }
};

// Message Actions
CapsuleBrainApp.prototype.handleMessageAction = function(e) {
  if (e.target.closest('.message-action')) {
    const action = e.target.closest('.message-action');
    const message = action.closest('.message');
    const actionType = action.title.toLowerCase();
    
    switch (actionType) {
      case 'copy message':
        this.copyMessage(message);
        break;
      case 'like message':
        this.likeMessage(message);
        break;
      case 'regenerate response':
        this.regenerateResponse(message);
        break;
    }
  }
};

CapsuleBrainApp.prototype.copyMessage = function(message) {
  const text = message.querySelector('.message-text').textContent;
  navigator.clipboard.writeText(text).then(() => {
    this.showNotification('Message copied to clipboard', 'success');
  });
};

CapsuleBrainApp.prototype.likeMessage = function(message) {
  const likeBtn = message.querySelector('[title="Like message"]');
  likeBtn.classList.toggle('liked');
  likeBtn.textContent = likeBtn.classList.contains('liked') ? '❤️' : '👍';
  
  this.showNotification('Message liked!', 'success');
};

CapsuleBrainApp.prototype.regenerateResponse = function(message) {
  // Implementation for regenerating AI response
  this.showNotification('Regenerating response...', 'info');
  // Add regeneration logic here
};

// Panel Actions
CapsuleBrainApp.prototype.handlePanelAction = function(e) {
  if (e.target.closest('.panel-actions button')) {
    const button = e.target.closest('.panel-actions button');
    const action = button.id;
    
    switch (action) {
      case 'clearChat':
        this.clearChat();
        break;
      case 'exportChat':
        this.exportChat();
        break;
      case 'chatSettings':
        this.showChatSettings();
        break;
    }
  }
};

CapsuleBrainApp.prototype.clearChat = function() {
  if (confirm('Are you sure you want to clear the chat history?')) {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
      chatMessages.innerHTML = `
        <div class="message assistant" role="article" aria-label="AI assistant message">
          <div class="message-avatar" role="img" aria-label="AI Assistant">AI</div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">Capsule Brain AI</span>
              <span class="message-time" id="welcomeTime" aria-label="Message timestamp"></span>
            </div>
            <div class="message-text">
              <p>Hello! I'm Capsule Brain Supreme AGI. How can I assist you today?</p>
            </div>
          </div>
        </div>
      `;
    }
    this.messageHistory = [];
    this.showNotification('Chat history cleared', 'success');
  }
};

CapsuleBrainApp.prototype.exportChat = function() {
  const chatData = {
    timestamp: new Date().toISOString(),
    messages: this.messageHistory,
    settings: this.settings
  };
  
  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `capsule-brain-chat-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  this.showNotification('Chat exported successfully', 'success');
};

CapsuleBrainApp.prototype.showChatSettings = function() {
  // Implementation for chat settings modal
  this.showNotification('Chat settings coming soon!', 'info');
};

// Keyboard Shortcuts Modal
CapsuleBrainApp.prototype.showKeyboardShortcuts = function() {
  const modal = document.getElementById('keyboardShortcuts');
  if (modal) {
    modal.setAttribute('aria-hidden', 'false');
    modal.style.display = 'flex';
    
    // Focus management
    const closeBtn = modal.querySelector('#closeShortcuts');
    if (closeBtn) {
      closeBtn.focus();
    }
  }
};

CapsuleBrainApp.prototype.closeModals = function() {
  // Close all modals
  const modals = document.querySelectorAll('[role="dialog"][aria-hidden="false"]');
  modals.forEach(modal => {
    modal.setAttribute('aria-hidden', 'true');
    modal.style.display = 'none';
  });
  
  // Focus back to main content
  const mainContent = document.getElementById('main-content');
  if (mainContent) {
    mainContent.focus();
  }
};

// Focus Management
CapsuleBrainApp.prototype.focusSearch = function() {
  // Implementation for search functionality
  this.showNotification('Search functionality coming soon!', 'info');
};

CapsuleBrainApp.prototype.focusInput = function() {
  const messageInput = document.getElementById('messageInput');
  if (messageInput) {
    messageInput.focus();
  }
};

// Enhanced Notification System
CapsuleBrainApp.prototype.showNotification = function(message, type = 'info', duration = 5000) {
  const container = document.getElementById('notificationContainer');
  if (!container) return;
  
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <span class="notification-message">${message}</span>
      <button class="notification-close" aria-label="Close notification">×</button>
    </div>
  `;
  
  container.appendChild(notification);
  
  // Auto remove
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, duration);
  
  // Manual close
  const closeBtn = notification.querySelector('.notification-close');
  closeBtn.addEventListener('click', () => notification.remove());
  
  // Store reference
  this.notifications.push(notification);
};

// Update the existing init method to include new features
const originalInit = CapsuleBrainApp.prototype.init;
CapsuleBrainApp.prototype.init = function() {
  originalInit.call(this);
  this.setupKeyboardShortcuts();
  this.setupEnhancedEventListeners();
  this.updateCharacterCount();
  console.log('✅ Enhanced Capsule Brain App initialized successfully');
};