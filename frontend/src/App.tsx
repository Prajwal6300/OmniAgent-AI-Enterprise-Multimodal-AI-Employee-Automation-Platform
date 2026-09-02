import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';

// Pages
import LandingPage from './pages/Landing';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DashboardPage from './pages/Dashboard';
import ChatPage from './pages/Chat';
import DocumentsPage from './pages/Documents';
import ImageAnalysisPage from './pages/ImageAnalysis';
import VoicePage from './pages/Voice';
import VideoPage from './pages/Video';
import KnowledgeBasePage from './pages/KnowledgeBase';
import AgentsPage from './pages/Agents';
import WorkflowsPage from './pages/Workflows';
import TasksPage from './pages/Tasks';
import ApprovalsPage from './pages/Approvals';
import AgentRunsPage from './pages/AgentRuns';
import AnalyticsPage from './pages/Analytics';
import IntegrationsPage from './pages/Integrations';
import NotificationsPage from './pages/Notifications';
import SettingsPage from './pages/Settings';
import AdminPage from './pages/Admin';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Main Authenticated Dashboard Shell */}
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/image-analysis" element={<ImageAnalysisPage />} />
        <Route path="/voice" element={<VoicePage />} />
        <Route path="/video" element={<VideoPage />} />
        <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/workflows" element={<WorkflowsPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/agent-runs" element={<AgentRunsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
