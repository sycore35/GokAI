import React, { useState, useEffect, useRef } from 'react';
import {
  api,
  HealthData,
  ProjectData,
  TaskData,
  AgentData,
  SkillData,
  MemoryData,
  ActivityLogData,
  SettingsData,
  ProviderStatusItem,
  ConversationData,
  ChatMessageData,
  AttachmentItem,
  DiagnosticsData,
} from './lib/api';
import { ThemeMode, getInitialTheme, resolveColors } from './lib/theme';
import { Language, getInitialLanguage, translations } from './lib/i18n';

type TabType = 'dashboard' | 'chat' | 'projects' | 'tasks' | 'agents' | 'skills' | 'memory' | 'activity' | 'settings' | 'developer';

export function App() {
  // Theme & Language
  const [themeMode, setThemeMode] = useState<ThemeMode>(getInitialTheme());
  const [lang, setLang] = useState<Language>(getInitialLanguage());
  const t = translations[lang];
  const c = resolveColors(themeMode);

  // Navigation
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  // Core Data
  const [health, setHealth] = useState<HealthData | null>(null);
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  // Dashboard Task Prompt
  const [prompt, setPrompt] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeTask, setActiveTask] = useState<TaskData | null>(null);
  const [events, setEvents] = useState<Array<{ time: string; text: string; type?: string }>>([]);

  // Tasks Tab
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskData | null>(null);

  // Agents & Skills
  const [agents, setAgents] = useState<AgentData[]>([]);
  const [skills, setSkills] = useState<SkillData[]>([]);
  const [skillSearch, setSkillSearch] = useState<string>('');

  // Memory & Activity
  const [memoryEntries, setMemoryEntries] = useState<MemoryData[]>([]);
  const [activities, setActivities] = useState<ActivityLogData[]>([]);

  // Settings & Providers
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [providers, setProviders] = useState<ProviderStatusItem[]>([]);
  const [providerInputs, setProviderInputs] = useState<Record<string, { key: string; model: string }>>({});
  const [providerTestResults, setProviderTestResults] = useState<Record<string, { testing?: boolean; success?: boolean; message?: string; latency?: number }>>({});

  // Chat Tab
  const [conversations, setConversations] = useState<ConversationData[]>([]);
  const [activeConvId, setActiveConvId] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessageData[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [chatSending, setChatSending] = useState<boolean>(false);
  const [chatAttachments, setChatAttachments] = useState<AttachmentItem[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File Explorer Tab
  const [projectFiles, setProjectFiles] = useState<Array<{ path: string; is_dir: boolean; size_bytes: number }>>([]);
  const [selectedFileContent, setSelectedFileContent] = useState<{ path: string; content: string } | null>(null);

  // Diagnostics Tab
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [diagActionMsg, setDiagActionMsg] = useState<string>('');

  // Modals
  const [showNewProjModal, setShowNewProjModal] = useState<boolean>(false);
  const [newProjName, setNewProjName] = useState<string>('');
  const [newProjDesc, setNewProjDesc] = useState<string>('');
  const [newProjStack, setNewProjStack] = useState<string>('python');

  const [showSkillModal, setShowSkillModal] = useState<boolean>(false);
  const [editingSkillName, setEditingSkillName] = useState<string | null>(null);
  const [skillForm, setSkillForm] = useState({ name: '', description: '', when_to_use: '', tags: '', instructions: '' });

  const [newMemKey, setNewMemKey] = useState<string>('');
  const [newMemVal, setNewMemVal] = useState<string>('');
  const [newMemTier, setNewMemTier] = useState<number>(1);

  // Initialize
  useEffect(() => {
    loadHealth();
    loadProjects();
    loadAgents();
    loadSkills();
    loadSettings();
    loadProviders();
    loadConversations();
    const interval = setInterval(loadHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut 'D' for Diagnostics
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.key === 'd' || e.key === 'D') {
        setActiveTab('developer');
        loadDiagnostics();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Update project-dependent data
  useEffect(() => {
    if (selectedProjectId) {
      loadFileTree(selectedProjectId);
      loadTasks(selectedProjectId);
      loadMemory(selectedProjectId);
      loadActivity(selectedProjectId);
      loadConversations(selectedProjectId);
    }
  }, [selectedProjectId]);

  // Scroll chat to bottom
  useEffect(() => {
    if (activeTab === 'chat') {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, activeTab]);

  // Load functions
  const loadHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  };

  const loadProjects = async () => {
    try {
      const projs = await api.listProjects();
      setProjects(projs);
      if (projs.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projs[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadTasks = async (projId?: string) => {
    try {
      const data = await api.listTasks(projId);
      setTasks(data);
      if (data.length > 0 && !selectedTask) {
        setSelectedTask(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await api.listAgents();
      setAgents(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSkills = async () => {
    try {
      const data = await api.listSkills();
      setSkills(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadMemory = async (projId: string) => {
    try {
      const data = await api.listMemory(projId);
      setMemoryEntries(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadActivity = async (projId?: string) => {
    try {
      const data = await api.listActivity(projId);
      setActivities(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadProviders = async () => {
    try {
      const items = await api.listProviders();
      setProviders(items);
      const inputs: Record<string, { key: string; model: string }> = {};
      items.forEach((p) => {
        inputs[p.provider] = { key: '', model: p.active_model || (p.models[0] || '') };
      });
      setProviderInputs(inputs);
    } catch (err) {
      console.error(err);
    }
  };

  const loadFileTree = async (projId: string) => {
    try {
      const files = await api.getProjectFiles(projId);
      setProjectFiles(files.filter((f) => !f.is_dir));
    } catch (err) {
      console.error(err);
    }
  };

  const viewFile = async (path: string) => {
    if (!selectedProjectId) return;
    try {
      const data = await api.getFileContent(selectedProjectId, path);
      setSelectedFileContent(data);
    } catch {
      alert('Failed to read file content');
    }
  };

  const loadConversations = async (projId?: string) => {
    try {
      const list = await api.listConversations(projId);
      setConversations(list);
      if (list.length > 0 && !activeConvId) {
        selectConversation(list[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    try {
      const msgs = await api.getConversationMessages(convId);
      setChatMessages(msgs);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const title = lang === 'tr' ? 'Yeni Sohbet' : 'New Conversation';
      const created = await api.createConversation(title, selectedProjectId || undefined);
      setConversations([created, ...conversations]);
      setActiveConvId(created.id);
      setChatMessages([]);
    } catch (err: any) {
      alert(`Error creating conversation: ${err.message}`);
    }
  };

  const handleDeleteConversation = async (convId: string) => {
    try {
      await api.deleteConversation(convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (remaining.length > 0) {
        selectConversation(remaining[0].id);
      } else {
        setActiveConvId('');
        setChatMessages([]);
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleSendChatMessage = async () => {
    if (!chatInput.trim() && chatAttachments.length === 0) return;

    let targetConvId = activeConvId;
    if (!targetConvId) {
      try {
        const title = chatInput.slice(0, 30) || (lang === 'tr' ? 'Yeni Sohbet' : 'New Conversation');
        const created = await api.createConversation(title, selectedProjectId || undefined);
        setConversations([created, ...conversations]);
        targetConvId = created.id;
        setActiveConvId(created.id);
      } catch {
        alert('Failed to initialize conversation');
        return;
      }
    }

    const currentAttachments = [...chatAttachments];
    const text = chatInput.trim();
    setChatInput('');
    setChatAttachments([]);
    setChatSending(true);

    // Optimistic user message update
    const optMsg: ChatMessageData = {
      id: `temp_${Date.now()}`,
      conversation_id: targetConvId,
      role: 'user',
      content: text,
      attachments: currentAttachments,
      created_at: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, optMsg]);

    try {
      const aiReply = await api.sendChatMessage(targetConvId, text, currentAttachments);
      setChatMessages((prev) => [...prev, aiReply]);
      loadConversations(selectedProjectId);
    } catch (err: any) {
      alert(`Chat error: ${err.message}`);
    } finally {
      setChatSending(false);
    }
  };

  // Attachment handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    processUploadedFiles(Array.from(files));
  };

  const processUploadedFiles = (files: File[]) => {
    files.forEach((file) => {
      if (file.size > 5 * 1024 * 1024) {
        alert(`File ${file.name} exceeds 5MB limit.`);
        return;
      }

      const isImg = file.type.startsWith('image/');
      const reader = new FileReader();

      if (isImg) {
        reader.onload = () => {
          setChatAttachments((prev) => [
            ...prev,
            { name: file.name, type: 'image', size_bytes: file.size, content: reader.result as string },
          ]);
        };
        reader.readAsDataURL(file);
      } else {
        reader.onload = () => {
          setChatAttachments((prev) => [
            ...prev,
            { name: file.name, type: 'code', size_bytes: file.size, content: reader.result as string },
          ]);
        };
        reader.readAsText(file);
      }
    });
  };

  // Drag & drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processUploadedFiles(Array.from(e.dataTransfer.files));
    }
  };

  // Diagnostics
  const loadDiagnostics = async () => {
    try {
      const diag = await api.getDiagnostics();
      setDiagnostics(diag);
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearCache = async () => {
    try {
      const res = await api.clearCache();
      setDiagActionMsg(res.message);
      loadSkills();
      loadDiagnostics();
      setTimeout(() => setDiagActionMsg(''), 4000);
    } catch (err: any) {
      alert(`Clear cache failed: ${err.message}`);
    }
  };

  const handleReloadConfig = async () => {
    try {
      const res = await api.reloadConfig();
      setDiagActionMsg(res.message);
      loadSettings();
      loadProviders();
      loadDiagnostics();
      setTimeout(() => setDiagActionMsg(''), 4000);
    } catch (err: any) {
      alert(`Reload config failed: ${err.message}`);
    }
  };

  // Provider config actions
  const handleTestProvider = async (provId: string) => {
    const input = providerInputs[provId];
    setProviderTestResults((prev) => ({ ...prev, [provId]: { testing: true } }));
    try {
      const res = await api.testProviderConnection(provId, input?.key || undefined, input?.model || undefined);
      setProviderTestResults((prev) => ({
        ...prev,
        [provId]: { testing: false, success: res.success, message: res.message, latency: res.latency_ms },
      }));
    } catch (err: any) {
      setProviderTestResults((prev) => ({
        ...prev,
        [provId]: { testing: false, success: false, message: err.message },
      }));
    }
  };

  const handleSaveProvider = async (provId: string) => {
    const input = providerInputs[provId];
    try {
      await api.saveProviderConfig(provId, input?.key || undefined, input?.model || undefined);
      await loadSettings();
      await loadProviders();
      await loadHealth();
      alert(`Provider ${provId} saved successfully.`);
    } catch (err: any) {
      alert(`Failed to save provider: ${err.message}`);
    }
  };

  const handleRemoveProvider = async (provId: string) => {
    if (!window.confirm(`Are you sure you want to remove credentials for ${provId}?`)) return;
    try {
      await api.removeProviderKey(provId);
      await loadSettings();
      await loadProviders();
      await loadHealth();
      alert(`Credentials removed for ${provId}.`);
    } catch (err: any) {
      alert(`Failed to remove key: ${err.message}`);
    }
  };

  // Skill management actions
  const handleSaveSkill = async () => {
    if (!skillForm.name.trim() || !skillForm.description.trim()) return;
    try {
      const tagsArray = skillForm.tags.split(',').map((s) => s.trim()).filter(Boolean);
      if (editingSkillName) {
        await api.updateSkill(editingSkillName, {
          description: skillForm.description,
          when_to_use: skillForm.when_to_use,
          tags: tagsArray,
          instructions: skillForm.instructions,
        });
      } else {
        await api.createSkill({
          name: skillForm.name,
          description: skillForm.description,
          when_to_use: skillForm.when_to_use,
          tags: tagsArray,
          instructions: skillForm.instructions,
        });
      }
      setShowSkillModal(false);
      setEditingSkillName(null);
      setSkillForm({ name: '', description: '', when_to_use: '', tags: '', instructions: '' });
      loadSkills();
    } catch (err: any) {
      alert(`Skill save error: ${err.message}`);
    }
  };

  const handleDeleteSkill = async (skillName: string) => {
    if (!window.confirm(`Delete skill "${skillName}"?`)) return;
    try {
      await api.deleteSkill(skillName);
      loadSkills();
    } catch (err: any) {
      alert(`Delete skill failed: ${err.message}`);
    }
  };

  const handleToggleSkill = async (skillName: string) => {
    try {
      await api.toggleSkill(skillName);
      loadSkills();
    } catch (err: any) {
      alert(`Toggle failed: ${err.message}`);
    }
  };

  // Project creation & deletion
  const handleCreateProject = async () => {
    if (!newProjName.trim()) return;
    try {
      const created = await api.createProject(newProjName.trim(), newProjDesc.trim(), newProjStack);
      setProjects([created, ...projects]);
      setSelectedProjectId(created.id);
      setShowNewProjModal(false);
      setNewProjName('');
      setNewProjDesc('');
    } catch (err: any) {
      alert(`Failed to create project: ${err.message}`);
    }
  };

  const handleDeleteProject = async (projId: string) => {
    if (!window.confirm(t.deleteProjectConfirm)) return;
    try {
      await api.deleteProject(projId);
      const remaining = projects.filter((p) => p.id !== projId);
      setProjects(remaining);
      setSelectedProjectId(remaining.length > 0 ? remaining[0].id : '');
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  // Task creation & execution
  const handleCreateTask = async () => {
    if (!prompt.trim()) return;

    let targetProjId = selectedProjectId;
    if (!targetProjId) {
      try {
        const newProj = await api.createProject('My Engineering Workspace', 'Autonomous Workspace');
        setProjects([newProj]);
        targetProjId = newProj.id;
        setSelectedProjectId(newProj.id);
      } catch {
        alert('Failed to initialize project workspace');
        return;
      }
    }

    setIsSubmitting(true);
    setEvents((prev) => [
      { time: new Date().toLocaleTimeString(), text: `Dispatching objective: "${prompt}"`, type: 'info' },
      ...prev,
    ]);

    try {
      const task = await api.createTask(targetProjId, prompt);
      setActiveTask(task);
      setSelectedTask(task);
      subscribeToTaskStream(task.id);
      setPrompt('');
      loadTasks(targetProjId);
    } catch (err: any) {
      alert(`Error submitting task: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await api.cancelTask(taskId);
      loadTasks(selectedProjectId);
    } catch (err: any) {
      alert(`Cancel failed: ${err.message}`);
    }
  };

  const handleRetryTask = async (taskId: string) => {
    try {
      const retried = await api.retryTask(taskId);
      setActiveTask(retried);
      setSelectedTask(retried);
      subscribeToTaskStream(retried.id);
      loadTasks(selectedProjectId);
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    }
  };

  const handleAddMemory = async () => {
    if (!selectedProjectId || !newMemKey.trim() || !newMemVal.trim()) return;
    try {
      await api.addMemory(selectedProjectId, newMemTier, newMemKey.trim(), newMemVal.trim());
      setNewMemKey('');
      setNewMemVal('');
      loadMemory(selectedProjectId);
    } catch (err: any) {
      alert(`Failed to add memory: ${err.message}`);
    }
  };

  const subscribeToTaskStream = (taskId: string) => {
    const eventSource = new EventSource(`/api/tasks/${taskId}/stream`);

    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const eventData = payload.data || {};
        const msg = eventData.message || payload.type;

        setEvents((prev) => [
          { time: new Date().toLocaleTimeString(), text: msg, type: payload.type },
          ...prev,
        ]);

        if (eventData.status) {
          setActiveTask((prev) => (prev ? { ...prev, status: eventData.status } : null));
        }

        if (['task_finished', 'task_failed', 'task_cancelled'].includes(payload.type)) {
          eventSource.close();
          loadProjects();
          if (selectedProjectId) {
            loadFileTree(selectedProjectId);
            loadTasks(selectedProjectId);
            loadMemory(selectedProjectId);
            loadActivity(selectedProjectId);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };
  };

  // Theme & Language switchers
  const toggleTheme = () => {
    const next: ThemeMode = themeMode === 'dark' ? 'light' : themeMode === 'light' ? 'system' : 'dark';
    setThemeMode(next);
    localStorage.setItem('gokai_theme', next);
  };

  const toggleLanguage = () => {
    const next: Language = lang === 'tr' ? 'en' : 'tr';
    setLang(next);
    localStorage.setItem('gokai_lang', next);
  };

  const filteredSkills = skills.filter((s) => {
    const query = skillSearch.toLowerCase();
    return s.name.toLowerCase().includes(query) || s.description.toLowerCase().includes(query) || s.tags.some((tg) => tg.toLowerCase().includes(query));
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: c.bgApp, color: c.textMain, fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
      {/* TOP BAR / HEADER */}
      <header style={{
        height: '60px',
        borderBottom: `1px solid ${c.border}`,
        backgroundColor: c.bgHeader,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            color: '#fff',
            fontSize: '17px',
            boxShadow: '0 0 15px rgba(6,182,212,0.4)',
          }}>
            G
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 800, letterSpacing: '0.05em' }}>
              {t.brandTitle} <span style={{ fontSize: '11px', fontWeight: 700, color: c.accent, marginLeft: '6px' }}>{t.brandSubtitle}</span>
            </div>
            <div style={{ fontSize: '10px', color: c.textSubtle, letterSpacing: '0.08em' }}>{t.orgName}</div>
          </div>
        </div>

        {/* Workspace Quick Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: c.textMuted }}>{t.activeWorkspace}</span>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            style={{
              backgroundColor: c.bgInput,
              color: c.accent,
              border: `1px solid ${c.borderLight}`,
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 700,
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.default_stack})
              </option>
            ))}
          </select>
        </div>

        {/* System Telemetry Badges & Preferences */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: c.textMuted }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: health?.database === 'connected' ? c.success : c.error }} />
            <span>{t.dbStatus}: {health?.database || t.connecting}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: c.textMuted }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: health?.active_providers?.length ? c.success : c.warning }} />
            <span>{t.aiStatus}: {health?.active_providers?.join(', ') || 'Mock'}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: c.textMuted }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: health?.docker_available ? c.success : c.accent }} />
            <span>{t.sandboxStatus}: {health?.docker_available ? t.dockerJail : t.processJail}</span>
          </div>

          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            style={{
              backgroundColor: c.bgSubtle,
              color: c.textMain,
              border: `1px solid ${c.border}`,
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
            title="Toggle theme (Dark / Light / System)"
          >
            {themeMode === 'dark' ? '🌙 Dark' : themeMode === 'light' ? '☀️ Light' : '💻 System'}
          </button>

          {/* Language Switcher */}
          <button
            onClick={toggleLanguage}
            style={{
              backgroundColor: c.bgSubtle,
              color: c.accent,
              border: `1px solid ${c.border}`,
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
            title="Toggle Language"
          >
            {lang.toUpperCase()}
          </button>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* SIDEBAR NAVIGATION */}
        <aside style={{
          width: '230px',
          borderRight: `1px solid ${c.border}`,
          backgroundColor: c.bgSidebar,
          padding: '16px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}>
          {[
            { id: 'dashboard', label: t.tabDashboard, icon: '⚡' },
            { id: 'chat', label: t.tabChat, icon: '💬' },
            { id: 'projects', label: t.tabProjects, icon: '📁' },
            { id: 'tasks', label: t.tabTasks, icon: '📋' },
            { id: 'agents', label: t.tabAgents, icon: '🤖' },
            { id: 'skills', label: t.tabSkills, icon: '🧠' },
            { id: 'memory', label: t.tabMemory, icon: '💾' },
            { id: 'activity', label: t.tabActivity, icon: '⏱️' },
            { id: 'settings', label: t.tabSettings, icon: '⚙️' },
            { id: 'developer', label: t.tabDev, icon: '🩺' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                const tab = item.id as TabType;
                setActiveTab(tab);
                if (tab === 'tasks') loadTasks(selectedProjectId);
                if (tab === 'projects' && selectedProjectId) loadFileTree(selectedProjectId);
                if (tab === 'memory' && selectedProjectId) loadMemory(selectedProjectId);
                if (tab === 'activity') loadActivity(selectedProjectId);
                if (tab === 'settings') { loadSettings(); loadProviders(); }
                if (tab === 'developer') loadDiagnostics();
                if (tab === 'chat') loadConversations(selectedProjectId);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: activeTab === item.id ? c.accentSubtle : 'transparent',
                color: activeTab === item.id ? c.accent : c.textMuted,
                fontWeight: activeTab === item.id ? 700 : 500,
                fontSize: '13px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </aside>

        {/* CONTENT AREA */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <>
              {/* Task Creation Prompt Banner */}
              <div style={{
                backgroundColor: c.bgCard,
                border: `1px solid ${c.border}`,
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
              }}>
                <div style={{ fontSize: '18px', fontWeight: 800, color: c.textMain, marginBottom: '6px' }}>
                  {t.dashboardTitle}
                </div>
                <div style={{ fontSize: '13px', color: c.textMuted, marginBottom: '16px' }}>
                  {t.dashboardSubtitle}
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateTask()}
                    placeholder={t.promptPlaceholder}
                    style={{
                      flex: 1,
                      backgroundColor: c.bgInput,
                      border: `1px solid ${c.borderLight}`,
                      borderRadius: '8px',
                      padding: '12px 16px',
                      color: c.textMain,
                      fontSize: '14px',
                      outline: 'none',
                    }}
                  />
                  <button
                    onClick={handleCreateTask}
                    disabled={isSubmitting || !prompt.trim()}
                    style={{
                      backgroundColor: c.accent,
                      color: '#090D16',
                      fontWeight: 800,
                      fontSize: '14px',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '0 26px',
                      cursor: isSubmitting || !prompt.trim() ? 'not-allowed' : 'pointer',
                      opacity: isSubmitting || !prompt.trim() ? 0.6 : 1,
                    }}
                  >
                    {isSubmitting ? t.dispatching : t.dispatchTask}
                  </button>
                </div>
              </div>

              {/* Active Task Banner */}
              {activeTask && (
                <div style={{
                  backgroundColor: c.bgCard,
                  border: `1px solid ${c.border}`,
                  borderRadius: '12px',
                  padding: '18px 22px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontSize: '11px', color: c.textSubtle, fontWeight: 700, textTransform: 'uppercase' }}>{t.activeTaskBanner}</div>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: c.accent, marginTop: '2px' }}>{activeTask.user_prompt}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 700,
                      backgroundColor: activeTask.status === 'COMPLETED' ? c.successBg : c.accentSubtle,
                      color: activeTask.status === 'COMPLETED' ? c.success : c.accent,
                    }}>
                      {activeTask.status}
                    </span>
                    {!['COMPLETED', 'FAILED', 'CANCELLED'].includes(activeTask.status) && (
                      <button
                        onClick={() => handleCancelTask(activeTask.id)}
                        style={{
                          backgroundColor: c.error,
                          color: '#fff',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '6px 12px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {t.cancel}
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Real-time Multi-Agent Execution Stream */}
              <div style={{
                backgroundColor: c.bgCard,
                border: `1px solid ${c.border}`,
                borderRadius: '12px',
                padding: '20px',
                flex: 1,
                minHeight: '280px',
                display: 'flex',
                flexDirection: 'column',
              }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMuted, marginBottom: '12px' }}>
                  {t.liveStreamTitle}
                </div>
                <div style={{
                  flex: 1,
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  fontSize: '13px',
                  fontFamily: 'Consolas, monospace',
                }}>
                  {events.length === 0 ? (
                    <div style={{ color: c.textSubtle, fontStyle: 'italic' }}>{t.liveStreamEmpty}</div>
                  ) : (
                    events.map((ev, i) => (
                      <div key={i} style={{ display: 'flex', gap: '12px', color: c.textMain, lineHeight: '1.4' }}>
                        <span style={{ color: c.textSubtle }}>[{ev.time}]</span>
                        <span style={{ color: ev.type?.includes('fail') ? c.error : (ev.type?.includes('finish') ? c.success : c.accent) }}>
                          {ev.text}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}

          {/* TAB 2: AI CHAT (Dedicated Interactive View) */}
          {activeTab === 'chat' && (
            <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
              {/* Conversations Sidebar */}
              <div style={{
                width: '260px',
                backgroundColor: c.bgCard,
                border: `1px solid ${c.border}`,
                borderRadius: '12px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}>
                <button
                  onClick={handleCreateConversation}
                  style={{
                    backgroundColor: c.accent,
                    color: '#090D16',
                    fontWeight: 700,
                    fontSize: '13px',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '10px',
                    cursor: 'pointer',
                  }}
                >
                  {t.newChat}
                </button>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', flex: 1 }}>
                  {conversations.length === 0 ? (
                    <div style={{ fontSize: '12px', color: c.textSubtle, textAlign: 'center', marginTop: '20px' }}>
                      {t.noChats}
                    </div>
                  ) : (
                    conversations.map((conv) => (
                      <div
                        key={conv.id}
                        onClick={() => selectConversation(conv.id)}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '8px',
                          backgroundColor: activeConvId === conv.id ? c.bgSubtle : 'transparent',
                          color: activeConvId === conv.id ? c.accent : c.textMuted,
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '13px',
                        }}
                      >
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                          {conv.title}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteConversation(conv.id);
                          }}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: c.error,
                            cursor: 'pointer',
                            fontSize: '14px',
                          }}
                          title="Delete"
                        >
                          ×
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Chat Thread Container */}
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                style={{
                  flex: 1,
                  backgroundColor: c.bgCard,
                  border: `1px solid ${c.border}`,
                  borderRadius: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                }}
              >
                {/* Chat Top Info */}
                <div style={{
                  padding: '14px 20px',
                  borderBottom: `1px solid ${c.border}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>
                    {t.chatTitle}
                  </div>
                  <div style={{ fontSize: '12px', color: c.accent, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: c.accent }} />
                    <span>{selectedProjectId ? t.projectAware : t.generalContext}</span>
                  </div>
                </div>

                {/* Messages List */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ margin: 'auto', textAlign: 'center', color: c.textSubtle, maxWidth: '400px' }}>
                      <div style={{ fontSize: '32px', marginBottom: '10px' }}>💬</div>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: c.textMain, marginBottom: '6px' }}>
                        {t.chatTitle}
                      </div>
                      <div style={{ fontSize: '13px' }}>{t.chatPlaceholder}</div>
                    </div>
                  ) : (
                    chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        style={{
                          alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                          maxWidth: '75%',
                          backgroundColor: msg.role === 'user' ? c.accent : c.bgSubtle,
                          color: msg.role === 'user' ? '#090D16' : c.textMain,
                          borderRadius: '10px',
                          padding: '14px 18px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                        }}
                      >
                        {/* Attachments preview if present */}
                        {msg.attachments && msg.attachments.length > 0 && (
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '4px' }}>
                            {msg.attachments.map((att, idx) => (
                              <span
                                key={idx}
                                style={{
                                  fontSize: '11px',
                                  padding: '3px 8px',
                                  borderRadius: '4px',
                                  backgroundColor: msg.role === 'user' ? 'rgba(0,0,0,0.15)' : c.bgCard,
                                  color: msg.role === 'user' ? '#090D16' : c.accent,
                                  fontWeight: 600,
                                }}
                              >
                                📎 {att.name}
                              </span>
                            ))}
                          </div>
                        )}

                        <div style={{ fontSize: '13px', lineHeight: '1.6', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {msg.content}
                        </div>

                        {/* Model & Timestamp Badge */}
                        <div style={{
                          fontSize: '10px',
                          color: msg.role === 'user' ? 'rgba(0,0,0,0.6)' : c.textSubtle,
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: '2px',
                        }}>
                          <span>{msg.provider ? `${msg.provider}:${msg.model}` : ''}</span>
                          <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    ))
                  )}
                  {chatSending && (
                    <div style={{ alignSelf: 'flex-start', color: c.accent, fontSize: '13px', fontStyle: 'italic' }}>
                      {lang === 'tr' ? 'GökAI düşünüyor...' : 'GökAI is generating response...'}
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                {/* Attachments Staging Bar */}
                {chatAttachments.length > 0 && (
                  <div style={{ padding: '8px 20px', borderTop: `1px solid ${c.border}`, display: 'flex', gap: '8px', flexWrap: 'wrap', backgroundColor: c.bgInput }}>
                    {chatAttachments.map((att, i) => (
                      <span key={i} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', backgroundColor: c.bgSubtle, color: c.accent, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>📎 {att.name} ({Math.round(att.size_bytes / 1024)}KB)</span>
                        <button
                          onClick={() => setChatAttachments((prev) => prev.filter((_, idx) => idx !== i))}
                          style={{ background: 'none', border: 'none', color: c.error, cursor: 'pointer', fontWeight: 700 }}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Input Bar */}
                <div style={{ padding: '16px 20px', borderTop: `1px solid ${c.border}`, display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    multiple
                    style={{ display: 'none' }}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                      backgroundColor: c.bgSubtle,
                      border: `1px solid ${c.borderLight}`,
                      color: c.textMuted,
                      borderRadius: '8px',
                      padding: '10px 14px',
                      cursor: 'pointer',
                      fontSize: '14px',
                    }}
                    title={t.attachFile}
                  >
                    📎
                  </button>

                  <textarea
                    rows={2}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendChatMessage();
                      }
                    }}
                    placeholder={t.chatPlaceholder}
                    style={{
                      flex: 1,
                      backgroundColor: c.bgInput,
                      border: `1px solid ${c.borderLight}`,
                      borderRadius: '8px',
                      padding: '10px 14px',
                      color: c.textMain,
                      fontSize: '13px',
                      outline: 'none',
                      resize: 'none',
                    }}
                  />

                  <button
                    onClick={handleSendChatMessage}
                    disabled={chatSending || (!chatInput.trim() && chatAttachments.length === 0)}
                    style={{
                      backgroundColor: c.accent,
                      color: '#090D16',
                      fontWeight: 800,
                      border: 'none',
                      borderRadius: '8px',
                      padding: '0 22px',
                      height: '46px',
                      cursor: chatSending ? 'not-allowed' : 'pointer',
                      opacity: chatSending || (!chatInput.trim() && chatAttachments.length === 0) ? 0.6 : 1,
                    }}
                  >
                    {t.send}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PROJECTS & FILE EXPLORER */}
          {activeTab === 'projects' && (
            <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
              {/* Project Workspaces List */}
              <div style={{ width: '280px', backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{t.workspaces}</div>
                  <button
                    onClick={() => setShowNewProjModal(true)}
                    style={{
                      backgroundColor: c.accent,
                      color: '#090D16',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '4px 10px',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {t.newWorkspace}
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', flex: 1 }}>
                  {projects.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => {
                        setSelectedProjectId(p.id);
                        loadFileTree(p.id);
                      }}
                      style={{
                        padding: '10px 12px',
                        borderRadius: '6px',
                        backgroundColor: selectedProjectId === p.id ? c.bgSubtle : 'transparent',
                        cursor: 'pointer',
                        color: selectedProjectId === p.id ? c.accent : c.textMuted,
                        fontSize: '13px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600 }}>{p.name}</div>
                        <div style={{ fontSize: '11px', color: c.textSubtle }}>Stack: {p.default_stack}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteProject(p.id);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: c.error,
                          cursor: 'pointer',
                          fontSize: '13px',
                        }}
                        title="Delete project"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Files & Content Preview */}
              <div style={{ flex: 1, backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{t.filesAndDiffs}</div>
                  {selectedProjectId && (
                    <a
                      href={`/api/projects/${selectedProjectId}/export`}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        backgroundColor: c.bgSubtle,
                        color: c.accent,
                        fontSize: '12px',
                        padding: '6px 14px',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontWeight: 700,
                        border: `1px solid ${c.borderLight}`,
                      }}
                    >
                      {t.exportZip}
                    </a>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '16px', flex: 1, overflow: 'hidden' }}>
                  {/* File List */}
                  <div style={{ width: '240px', borderRight: `1px solid ${c.border}`, paddingRight: '12px', overflowY: 'auto' }}>
                    {projectFiles.length === 0 ? (
                      <div style={{ fontSize: '12px', color: c.textSubtle }}>{t.noFilesYet}</div>
                    ) : (
                      projectFiles.map((f) => (
                        <div
                          key={f.path}
                          onClick={() => viewFile(f.path)}
                          style={{
                            padding: '6px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            cursor: 'pointer',
                            color: selectedFileContent?.path === f.path ? c.accent : c.textMuted,
                            backgroundColor: selectedFileContent?.path === f.path ? c.bgSubtle : 'transparent',
                            fontFamily: 'Consolas, monospace',
                            display: 'flex',
                            justifyContent: 'space-between',
                          }}
                        >
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.path}</span>
                          <span style={{ fontSize: '10px', color: c.textSubtle }}>{f.size_bytes}B</span>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Content Preview */}
                  <div style={{ flex: 1, overflowY: 'auto', backgroundColor: c.bgInput, borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column' }}>
                    {selectedFileContent ? (
                      <div>
                        <div style={{ fontSize: '12px', color: c.accent, marginBottom: '10px', fontFamily: 'Consolas, monospace', fontWeight: 600 }}>
                          {t.viewingFile} {selectedFileContent.path}
                        </div>
                        <pre style={{ fontSize: '12px', color: c.textMain, overflowX: 'auto', lineHeight: '1.5', fontFamily: 'Consolas, monospace' }}>
                          {selectedFileContent.content}
                        </pre>
                      </div>
                    ) : (
                      <div style={{ color: c.textSubtle, fontSize: '13px', fontStyle: 'italic', margin: 'auto' }}>
                        {t.selectFileHint}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: TASKS & DAG INSPECTOR */}
          {activeTab === 'tasks' && (
            <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
              {/* Task List */}
              <div style={{ width: '320px', backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{t.allTasks}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
                  {tasks.length === 0 ? (
                    <div style={{ fontSize: '12px', color: c.textSubtle }}>{t.noTasks}</div>
                  ) : (
                    tasks.map((task) => (
                      <div
                        key={task.id}
                        onClick={() => setSelectedTask(task)}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          backgroundColor: selectedTask?.id === task.id ? c.bgSubtle : c.bgInput,
                          border: `1px solid ${c.border}`,
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{
                            fontSize: '10px',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            backgroundColor: task.status === 'COMPLETED' ? c.successBg : (task.status === 'FAILED' ? c.errorBg : c.accentSubtle),
                            color: task.status === 'COMPLETED' ? c.success : (task.status === 'FAILED' ? c.error : c.accent),
                          }}>
                            {task.status}
                          </span>
                          <span style={{ fontSize: '11px', color: c.textSubtle }}>
                            {new Date(task.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: c.textMain, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {task.user_prompt}
                        </div>
                        <div style={{ fontSize: '11px', color: c.textMuted, display: 'flex', justifyContent: 'space-between' }}>
                          <span>Cost: ${task.estimated_cost_usd?.toFixed(4) || '0.0000'}</span>
                          <span>Tokens: {task.total_tokens || 0}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Task Details Inspector */}
              <div style={{ flex: 1, backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {selectedTask ? (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: '12px', color: c.textSubtle, fontWeight: 600 }}>{t.taskId} {selectedTask.id}</div>
                        <div style={{ fontSize: '18px', fontWeight: 800, color: c.accent, marginTop: '4px' }}>{selectedTask.user_prompt}</div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => handleRetryTask(selectedTask.id)}
                          style={{
                            backgroundColor: '#3B82F6',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '6px 14px',
                            fontSize: '12px',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          {t.retryTask}
                        </button>
                        {!['COMPLETED', 'FAILED', 'CANCELLED'].includes(selectedTask.status) && (
                          <button
                            onClick={() => handleCancelTask(selectedTask.id)}
                            style={{
                              backgroundColor: c.error,
                              color: '#fff',
                              border: 'none',
                              borderRadius: '6px',
                              padding: '6px 14px',
                              fontSize: '12px',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            {t.cancel}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Metrics Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                      <div style={{ backgroundColor: c.bgInput, padding: '12px', borderRadius: '8px', border: `1px solid ${c.border}` }}>
                        <div style={{ fontSize: '11px', color: c.textSubtle }}>{t.status}</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: selectedTask.status === 'COMPLETED' ? c.success : c.accent }}>{selectedTask.status}</div>
                      </div>
                      <div style={{ backgroundColor: c.bgInput, padding: '12px', borderRadius: '8px', border: `1px solid ${c.border}` }}>
                        <div style={{ fontSize: '11px', color: c.textSubtle }}>{t.estimatedCost}</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>${selectedTask.estimated_cost_usd?.toFixed(4) || '0.0000'}</div>
                      </div>
                      <div style={{ backgroundColor: c.bgInput, padding: '12px', borderRadius: '8px', border: `1px solid ${c.border}` }}>
                        <div style={{ fontSize: '11px', color: c.textSubtle }}>{t.debugCycles}</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{selectedTask.debug_cycles || 0} / 5</div>
                      </div>
                      <div style={{ backgroundColor: c.bgInput, padding: '12px', borderRadius: '8px', border: `1px solid ${c.border}` }}>
                        <div style={{ fontSize: '11px', color: c.textSubtle }}>{t.tokensConsumed}</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{selectedTask.total_tokens || 0}</div>
                      </div>
                    </div>

                    {/* Deliverables */}
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain, marginBottom: '8px' }}>{t.deliverables}</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {selectedTask.artifacts && selectedTask.artifacts.length > 0 ? (
                          selectedTask.artifacts.map((art) => (
                            <div
                              key={art.id}
                              onClick={() => {
                                setActiveTab('projects');
                                viewFile(art.path);
                              }}
                              style={{
                                padding: '8px 12px',
                                backgroundColor: c.bgInput,
                                border: `1px solid ${c.border}`,
                                borderRadius: '6px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                cursor: 'pointer',
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', backgroundColor: c.bgSubtle, color: c.accent }}>
                                  {art.type}
                                </span>
                                <span style={{ fontSize: '13px', fontWeight: 600, color: c.textMain }}>{art.name}</span>
                              </div>
                              <span style={{ fontSize: '11px', color: c.textSubtle }}>by {art.created_by}</span>
                            </div>
                          ))
                        ) : (
                          <div style={{ fontSize: '12px', color: c.textSubtle, fontStyle: 'italic' }}>{t.noArtifacts}</div>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div style={{ color: c.textSubtle, fontStyle: 'italic', margin: 'auto' }}>Select a task to view execution details.</div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: SPECIALIST AGENTS */}
          {activeTab === 'agents' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ fontSize: '16px', fontWeight: 800, color: c.textMain }}>{t.agentsTitle}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                {agents.map((agent) => (
                  <div
                    key={agent.name}
                    style={{
                      backgroundColor: c.bgCard,
                      border: `1px solid ${c.border}`,
                      borderRadius: '10px',
                      padding: '18px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <div style={{ fontSize: '15px', fontWeight: 700, color: c.textMain }}>{agent.title}</div>
                        <span style={{ fontSize: '10px', color: c.success, backgroundColor: c.successBg, padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                          {agent.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: c.accent, marginBottom: '8px', fontWeight: 600 }}>{t.role} {agent.role}</div>
                      <div style={{ fontSize: '12px', color: c.textMuted, marginBottom: '14px', lineHeight: '1.4' }}>{agent.description}</div>
                    </div>
                    <div style={{ fontSize: '11px', color: c.textSubtle, borderTop: `1px solid ${c.border}`, paddingTop: '8px' }}>
                      {t.tools} {agent.allowed_tools.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: SKILLS MANAGEMENT (Full UI) */}
          {activeTab === 'skills' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: 800, color: c.textMain }}>{t.skillsTitle}</div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    value={skillSearch}
                    onChange={(e) => setSkillSearch(e.target.value)}
                    placeholder={t.searchSkills}
                    style={{
                      backgroundColor: c.bgInput,
                      border: `1px solid ${c.borderLight}`,
                      borderRadius: '6px',
                      padding: '6px 14px',
                      fontSize: '12px',
                      color: c.textMain,
                      width: '240px',
                      outline: 'none',
                    }}
                  />
                  <button
                    onClick={() => {
                      setEditingSkillName(null);
                      setSkillForm({ name: '', description: '', when_to_use: '', tags: '', instructions: '' });
                      setShowSkillModal(true);
                    }}
                    style={{
                      backgroundColor: c.accent,
                      color: '#090D16',
                      fontWeight: 700,
                      fontSize: '12px',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '6px 14px',
                      cursor: 'pointer',
                    }}
                  >
                    {t.createSkill}
                  </button>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
                {filteredSkills.map((s) => (
                  <div key={s.name} style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '14px', fontWeight: 700, color: c.accent }}>{s.name}</span>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{
                          fontSize: '10px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: s.is_builtin ? c.bgSubtle : c.accentSubtle,
                          color: s.is_builtin ? c.textMuted : c.accent,
                          fontWeight: 700,
                        }}>
                          {s.is_builtin ? t.builtinBadge : t.customBadge}
                        </span>
                        <button
                          onClick={() => handleToggleSkill(s.name)}
                          style={{
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            border: 'none',
                            cursor: 'pointer',
                            backgroundColor: s.enabled ? c.successBg : c.errorBg,
                            color: s.enabled ? c.success : c.error,
                            fontWeight: 700,
                          }}
                        >
                          {s.enabled ? t.enabledBadge : t.disabledBadge}
                        </button>
                      </div>
                    </div>

                    <div style={{ fontSize: '12px', color: c.textMuted }}>{s.description}</div>
                    {s.when_to_use && (
                      <div style={{ fontSize: '11px', color: c.textSubtle }}>{t.whenToUse} {s.when_to_use}</div>
                    )}

                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {s.tags.map((tg) => (
                        <span key={tg} style={{ fontSize: '10px', backgroundColor: c.bgInput, color: c.textMuted, padding: '2px 6px', borderRadius: '4px' }}>
                          #{tg}
                        </span>
                      ))}
                    </div>

                    {!s.is_builtin && (
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: `1px solid ${c.border}`, paddingTop: '8px' }}>
                        <button
                          onClick={() => {
                            setEditingSkillName(s.name);
                            setSkillForm({
                              name: s.name,
                              description: s.description,
                              when_to_use: s.when_to_use,
                              tags: s.tags.join(', '),
                              instructions: s.instructions || '',
                            });
                            setShowSkillModal(true);
                          }}
                          style={{ background: 'none', border: 'none', color: c.accent, fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}
                        >
                          {t.editSkill}
                        </button>
                        <button
                          onClick={() => handleDeleteSkill(s.name)}
                          style={{ background: 'none', border: 'none', color: c.error, fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}
                        >
                          {t.deleteSkill}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: PROJECT MEMORY */}
          {activeTab === 'memory' && (
            <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
              {/* Add Memory Form */}
              <div style={{ width: '320px', backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ fontSize: '15px', fontWeight: 700, color: c.textMain }}>{t.memoryTitle}</div>
                <div>
                  <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.memoryTier}</label>
                  <select
                    value={newMemTier}
                    onChange={(e) => setNewMemTier(Number(e.target.value))}
                    style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px' }}
                  >
                    <option value={1}>Tier 1: Fact (Ports & Truths)</option>
                    <option value={2}>Tier 2: Architectural Decision</option>
                    <option value={3}>Tier 3: Evolution Milestone</option>
                    <option value={4}>Tier 4: Task Summary</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.keyTitle}</label>
                  <input
                    type="text"
                    value={newMemKey}
                    onChange={(e) => setNewMemKey(e.target.value)}
                    placeholder="e.g. database_backend"
                    style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.contentValue}</label>
                  <textarea
                    rows={3}
                    value={newMemVal}
                    onChange={(e) => setNewMemVal(e.target.value)}
                    placeholder="e.g. SQLite local, PostgreSQL production"
                    style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px', outline: 'none' }}
                  />
                </div>
                <button
                  onClick={handleAddMemory}
                  disabled={!newMemKey.trim() || !newMemVal.trim()}
                  style={{
                    backgroundColor: c.accent,
                    color: '#090D16',
                    fontWeight: 700,
                    border: 'none',
                    borderRadius: '6px',
                    padding: '10px',
                    cursor: 'pointer',
                  }}
                >
                  {t.saveToMemory}
                </button>
              </div>

              {/* Memory Knowledge Base List */}
              <div style={{ flex: 1, backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '18px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '15px', fontWeight: 700, color: c.textMain }}>{t.memoryKnowledgeBase}</div>
                {memoryEntries.length === 0 ? (
                  <div style={{ color: c.textSubtle, fontStyle: 'italic' }}>{t.noMemory}</div>
                ) : (
                  memoryEntries.map((m) => (
                    <div key={m.id} style={{ backgroundColor: c.bgInput, border: `1px solid ${c.border}`, borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '11px', color: c.accent, fontWeight: 700 }}>
                          {m.tier === 1 ? 'TIER 1: FACT' : (m.tier === 2 ? 'TIER 2: DECISION' : (m.tier === 3 ? 'TIER 3: MILESTONE' : 'TIER 4: SUMMARY'))}
                        </span>
                        <span style={{ fontSize: '11px', color: c.textSubtle }}>{new Date(m.created_at).toLocaleDateString()}</span>
                      </div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: c.textMain }}>{m.key}</div>
                      <div style={{ fontSize: '12px', color: c.textMuted }}>{m.content}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 8: ACTIVITY TIMELINE */}
          {activeTab === 'activity' && (
            <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '20px', flex: 1, overflowY: 'auto' }}>
              <div style={{ fontSize: '16px', fontWeight: 700, color: c.textMain, marginBottom: '14px' }}>{t.activityTitle}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {activities.length === 0 ? (
                  <div style={{ color: c.textSubtle, fontStyle: 'italic' }}>{t.noActivity}</div>
                ) : (
                  activities.map((act) => (
                    <div
                      key={act.id}
                      style={{
                        padding: '10px 14px',
                        backgroundColor: c.bgInput,
                        border: `1px solid ${c.border}`,
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: act.level === 'SUCCESS' ? c.successBg : (act.level === 'ERROR' ? c.errorBg : c.accentSubtle),
                          color: act.level === 'SUCCESS' ? c.success : (act.level === 'ERROR' ? c.error : c.accent),
                        }}>
                          {act.action}
                        </span>
                        <span style={{ fontSize: '13px', color: c.textMain }}>{act.message}</span>
                      </div>
                      <span style={{ fontSize: '11px', color: c.textSubtle, fontFamily: 'monospace' }}>
                        {new Date(act.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 9: SETTINGS & PROVIDER GOVERNANCE */}
          {activeTab === 'settings' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '800px' }}>
              {/* Providers Card */}
              <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ fontSize: '17px', fontWeight: 800, color: c.textMain }}>{t.providersTitle}</div>
                <div style={{ fontSize: '12px', color: c.textMuted }}>{t.settingsNotice}</div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {providers.map((prov) => {
                    const testResult = providerTestResults[prov.provider];
                    return (
                      <div
                        key={prov.provider}
                        style={{
                          backgroundColor: c.bgInput,
                          border: `1px solid ${c.borderLight}`,
                          borderRadius: '8px',
                          padding: '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '15px', fontWeight: 700, color: c.textMain }}>{prov.display_name}</span>
                            {prov.provider === settings?.default_provider && (
                              <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', backgroundColor: c.accentSubtle, color: c.accent, fontWeight: 700 }}>
                                ACTIVE PRIMARY
                              </span>
                            )}
                          </div>
                          <span style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: prov.status === 'configured' ? c.successBg : c.errorBg,
                            color: prov.status === 'configured' ? c.success : c.error,
                          }}>
                            {prov.status === 'configured' ? t.statusConfigured : t.statusNotConfigured}
                          </span>
                        </div>

                        {prov.provider !== 'mock' && (
                          <div>
                            <label style={{ fontSize: '11px', color: c.textSubtle, display: 'block', marginBottom: '4px' }}>
                              {t.apiKeyLabel} {prov.masked_key && `(Current: ${prov.masked_key})`}
                            </label>
                            <input
                              type="password"
                              value={providerInputs[prov.provider]?.key || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setProviderInputs((prev) => ({
                                  ...prev,
                                  [prov.provider]: { ...prev[prov.provider], key: val },
                                }));
                              }}
                              placeholder={prov.has_key ? '••••••••••••••••' : 'Enter API key...'}
                              style={{
                                width: '100%',
                                backgroundColor: c.bgCard,
                                border: `1px solid ${c.border}`,
                                borderRadius: '6px',
                                padding: '8px 12px',
                                color: c.textMain,
                                fontSize: '13px',
                                outline: 'none',
                              }}
                            />
                          </div>
                        )}

                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          <div style={{ flex: 1 }}>
                            <label style={{ fontSize: '11px', color: c.textSubtle, display: 'block', marginBottom: '4px' }}>{t.defaultModelLabel}</label>
                            <select
                              value={providerInputs[prov.provider]?.model || prov.active_model}
                              onChange={(e) => {
                                const val = e.target.value;
                                setProviderInputs((prev) => ({
                                  ...prev,
                                  [prov.provider]: { ...prev[prov.provider], model: val },
                                }));
                              }}
                              style={{
                                width: '100%',
                                backgroundColor: c.bgCard,
                                border: `1px solid ${c.border}`,
                                borderRadius: '6px',
                                padding: '8px',
                                color: c.textMain,
                                fontSize: '12px',
                              }}
                            >
                              {prov.models.map((m) => (
                                <option key={m} value={m}>{m}</option>
                              ))}
                            </select>
                          </div>

                          <div style={{ display: 'flex', gap: '8px', marginTop: '18px' }}>
                            <button
                              onClick={() => handleTestProvider(prov.provider)}
                              disabled={testResult?.testing}
                              style={{
                                backgroundColor: c.bgSubtle,
                                color: c.accent,
                                border: `1px solid ${c.borderLight}`,
                                borderRadius: '6px',
                                padding: '8px 14px',
                                fontSize: '12px',
                                fontWeight: 700,
                                cursor: 'pointer',
                              }}
                            >
                              {testResult?.testing ? 'Testing...' : t.testConnection}
                            </button>

                            <button
                              onClick={() => handleSaveProvider(prov.provider)}
                              style={{
                                backgroundColor: c.accent,
                                color: '#090D16',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '8px 16px',
                                fontSize: '12px',
                                fontWeight: 800,
                                cursor: 'pointer',
                              }}
                            >
                              {t.saveConfig}
                            </button>

                            {prov.has_key && prov.provider !== 'mock' && (
                              <button
                                onClick={() => handleRemoveProvider(prov.provider)}
                                style={{
                                  backgroundColor: c.errorBg,
                                  color: c.error,
                                  border: 'none',
                                  borderRadius: '6px',
                                  padding: '8px 12px',
                                  fontSize: '12px',
                                  fontWeight: 700,
                                  cursor: 'pointer',
                                }}
                              >
                                {t.removeKey}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Test Status Banner */}
                        {testResult && !testResult.testing && (
                          <div style={{
                            fontSize: '11px',
                            padding: '6px 10px',
                            borderRadius: '4px',
                            backgroundColor: testResult.success ? c.successBg : c.errorBg,
                            color: testResult.success ? c.success : c.error,
                            fontWeight: 600,
                          }}>
                            {testResult.message} {testResult.latency ? `(${testResult.latency.toFixed(0)}ms)` : ''}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Runtime Governance Card */}
              <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ fontSize: '17px', fontWeight: 800, color: c.textMain }}>{t.runtimeSafetyTitle}</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.autonomyLevel}</label>
                    <select
                      value={settings?.autonomy_level || 'balanced'}
                      onChange={async (e) => {
                        await api.updateSettings({ autonomy_level: e.target.value });
                        loadSettings();
                      }}
                      style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px' }}
                    >
                      <option value="low">Low (Conservative approval checks)</option>
                      <option value="balanced">Balanced (Standard autonomous engineering)</option>
                      <option value="high">High (Maximum autonomy)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.maxCycles}</label>
                    <select
                      value={settings?.max_debug_cycles || 5}
                      onChange={async (e) => {
                        await api.updateSettings({ max_debug_cycles: Number(e.target.value) });
                        loadSettings();
                      }}
                      style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px' }}
                    >
                      {[1, 2, 3, 5, 8, 10].map((n) => (
                        <option key={n} value={n}>{n} cycles limit</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: DEVELOPER DIAGNOSTICS ("D") */}
          {activeTab === 'developer' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: c.textMain }}>{t.devTitle}</div>
                  <div style={{ fontSize: '12px', color: c.textSubtle }}>Shortcut: Press 'D' anywhere in the platform to access this view.</div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={handleClearCache}
                    style={{
                      backgroundColor: c.bgSubtle,
                      color: c.accent,
                      border: `1px solid ${c.borderLight}`,
                      borderRadius: '6px',
                      padding: '8px 14px',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {t.clearCacheBtn}
                  </button>
                  <button
                    onClick={handleReloadConfig}
                    style={{
                      backgroundColor: c.accent,
                      color: '#090D16',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '8px 14px',
                      fontSize: '12px',
                      fontWeight: 800,
                      cursor: 'pointer',
                    }}
                  >
                    {t.reloadConfigBtn}
                  </button>
                </div>
              </div>

              {diagActionMsg && (
                <div style={{ padding: '10px 14px', borderRadius: '6px', backgroundColor: c.successBg, color: c.success, fontSize: '12px', fontWeight: 700 }}>
                  {diagActionMsg}
                </div>
              )}

              {/* Diagnostics Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.accent }}>{t.sysInfo}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Platform: {diagnostics?.system?.os_platform} {diagnostics?.system?.os_release}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Python: {diagnostics?.system?.python_version}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Process PID: {diagnostics?.system?.process_id}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Uptime: {diagnostics?.system?.uptime_formatted}</div>
                </div>

                <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.accent }}>{t.backendTelemetry}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Database: {diagnostics?.backend?.database_type} ({diagnostics?.backend?.database_status})</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Total Workspaces: {diagnostics?.backend?.total_projects}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Total Tasks: {diagnostics?.backend?.total_tasks}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Port: {diagnostics?.backend?.port}</div>
                </div>

                <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: c.accent }}>{t.sandboxTelemetry}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Execution Mode: {diagnostics?.sandbox?.execution_mode}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Timeout: {diagnostics?.sandbox?.timeout_seconds}s</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Max Debug Cycles: {diagnostics?.sandbox?.max_debug_cycles}</div>
                  <div style={{ fontSize: '12px', color: c.textMuted }}>Docker Available: {diagnostics?.sandbox?.docker_available ? 'Yes' : 'No'}</div>
                </div>
              </div>

              {/* Log Tail */}
              <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', flex: 1, minHeight: '260px' }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: c.textMain }}>{t.recentLogs}</div>
                <div style={{
                  flex: 1,
                  overflowY: 'auto',
                  backgroundColor: c.bgInput,
                  borderRadius: '6px',
                  padding: '12px',
                  fontFamily: 'Consolas, monospace',
                  fontSize: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}>
                  {diagnostics?.recent_logs && diagnostics.recent_logs.length > 0 ? (
                    diagnostics.recent_logs.map((log) => (
                      <div key={log.id} style={{ display: 'flex', gap: '10px' }}>
                        <span style={{ color: c.textSubtle }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                        <span style={{ color: c.accent, fontWeight: 600 }}>[{log.actor}]</span>
                        <span style={{ color: log.level === 'SUCCESS' ? c.success : (log.level === 'ERROR' ? c.error : c.textMain) }}>
                          {log.message}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: c.textSubtle, fontStyle: 'italic' }}>No logs recorded.</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* CREATE WORKSPACE MODAL */}
      {showNewProjModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
        }}>
          <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '24px', width: '420px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '16px', fontWeight: 800, color: c.textMain }}>{t.newWorkspace}</div>
            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Workspace Name</label>
              <input
                type="text"
                value={newProjName}
                onChange={(e) => setNewProjName(e.target.value)}
                placeholder="e.g. Finance Analytics API"
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Tech Stack</label>
              <select
                value={newProjStack}
                onChange={(e) => setNewProjStack(e.target.value)}
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
              >
                <option value="python">Python 3.11+</option>
                <option value="fastapi">FastAPI REST</option>
                <option value="react">React / Vite</option>
                <option value="nodejs">Node.js</option>
              </select>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button
                onClick={() => setShowNewProjModal(false)}
                style={{ backgroundColor: 'transparent', border: `1px solid ${c.borderLight}`, color: c.textMuted, borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}
              >
                {t.cancel}
              </button>
              <button
                onClick={handleCreateProject}
                style={{ backgroundColor: c.accent, color: '#090D16', fontWeight: 800, border: 'none', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE / EDIT SKILL MODAL */}
      {showSkillModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
        }}>
          <div style={{ backgroundColor: c.bgCard, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '24px', width: '500px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '16px', fontWeight: 800, color: c.textMain }}>
              {editingSkillName ? `${t.editSkill}: ${editingSkillName}` : t.createSkill}
            </div>

            {!editingSkillName && (
              <div>
                <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Skill Identifier</label>
                <input
                  type="text"
                  value={skillForm.name}
                  onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                  placeholder="e.g. postgresql-migrations"
                  style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
                />
              </div>
            )}

            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Description</label>
              <input
                type="text"
                value={skillForm.description}
                onChange={(e) => setSkillForm({ ...skillForm, description: e.target.value })}
                placeholder="e.g. Best practices for Alembic & PostgreSQL migrations"
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>{t.whenToUse}</label>
              <input
                type="text"
                value={skillForm.when_to_use}
                onChange={(e) => setSkillForm({ ...skillForm, when_to_use: e.target.value })}
                placeholder="e.g. Use when writing database migration scripts"
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Tags (comma-separated)</label>
              <input
                type="text"
                value={skillForm.tags}
                onChange={(e) => setSkillForm({ ...skillForm, tags: e.target.value })}
                placeholder="e.g. postgres, sql, database, alembic"
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '13px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: c.textMuted, display: 'block', marginBottom: '4px' }}>Instructions & Guidelines (Markdown)</label>
              <textarea
                rows={4}
                value={skillForm.instructions}
                onChange={(e) => setSkillForm({ ...skillForm, instructions: e.target.value })}
                placeholder="# Guidelines..."
                style={{ width: '100%', backgroundColor: c.bgInput, border: `1px solid ${c.borderLight}`, borderRadius: '6px', padding: '8px', color: c.textMain, fontSize: '12px', outline: 'none' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
              <button
                onClick={() => setShowSkillModal(false)}
                style={{ backgroundColor: 'transparent', border: `1px solid ${c.borderLight}`, color: c.textMuted, borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}
              >
                {t.cancel}
              </button>
              <button
                onClick={handleSaveSkill}
                style={{ backgroundColor: c.accent, color: '#090D16', fontWeight: 800, border: 'none', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}
              >
                {t.saveConfig}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
