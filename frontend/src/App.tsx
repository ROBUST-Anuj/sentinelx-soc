import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { LoginPage } from './components/LoginPage';
import { OverviewPage } from './pages/OverviewPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { AttackGraphPage } from './pages/AttackGraphPage';
import { DetectionLabPage } from './pages/DetectionLabPage';
import { TelemetryPage } from './pages/TelemetryPage';
import { ThreatIntelPage } from './pages/ThreatIntelPage';
import { ResponseCenterPage } from './pages/ResponseCenterPage';
import { api } from './services/api';

export default function App() {
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Auto-authenticate with stored token or default admin for seamless access
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = api.getToken();
      if (storedToken) {
        setUser({ username: 'admin', role: 'admin' });
      } else {
        // Attempt automatic background seed login for presentation convenience
        try {
          const res = await api.login('admin', 'Admin@SentinelX2026');
          setUser({ username: res.username, role: res.role });
        } catch (e) {
          console.warn('Auto-login unavailable, showing login screen');
        }
      }
    };
    initAuth();
  }, []);

  const handleLogout = () => {
    api.logout();
    setUser(null);
  };

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    setRefreshKey((k) => k + 1);
    setTimeout(() => setIsRefreshing(false), 600);
  };

  if (!user) {
    return (
      <LoginPage
        onLoginSuccess={(userData) => setUser(userData)}
        onLoginApi={(u, p) => api.login(u, p)}
      />
    );
  }

  const getPageMeta = () => {
    switch (activeTab) {
      case 'overview':
        return {
          title: 'Security Operations Center Command Deck',
          subtitle: 'Real-time telemetry ingestion, correlation pipelines, and health monitors',
        };
      case 'incidents':
        return {
          title: 'Incident Queue & Evidence Triage',
          subtitle: 'Attack clusters synthesized through rule, ML anomaly, and graph evidence',
        };
      case 'graph':
        return {
          title: 'Topological Attack-Graph Reasoning',
          subtitle: 'Multi-hop entity traversal linking compromised hosts, processes, and network egress',
        };
      case 'telemetry':
        return {
          title: 'Unified Telemetry & Normalized Log Stream',
          subtitle: 'Canonical schema normalization for Windows events, Linux syslog, and NetFlow',
        };
      case 'benchmark':
        return {
          title: 'Detection Lab & Empirical Evaluation',
          subtitle: 'Rigorous comparative benchmarks across deterministic rules, supervised ML, and hybrid graphs',
        };
      case 'threat_intel':
        return {
          title: 'Threat Intelligence & IOC Correlation Feed',
          subtitle: 'Active Indicators of Compromise (IP, domains, hashes) matched against live telemetry',
        };
      case 'response':
        return {
          title: 'Incident Response & Guardrail Playbooks',
          subtitle: 'Controlled defensive actions equipped with allowlisting and cryptographic audit trails',
        };
      default:
        return {
          title: 'SentinelX SOC',
          subtitle: 'Autonomous Cyber Defense Platform',
        };
    }
  };

  const meta = getPageMeta();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-primary)] text-slate-100 antialiased selection:bg-cyan-500 selection:text-slate-950 font-sans">
      {/* Collapsible Left Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        userRole={user.role}
        username={user.username}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <Navbar
          title={meta.title}
          subtitle={meta.subtitle}
          onRefresh={handleManualRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          <div key={refreshKey} className="max-w-7xl mx-auto space-y-6">
            {activeTab === 'overview' && (
              <OverviewPage onNavigateToTab={(tab) => setActiveTab(tab)} />
            )}
            {activeTab === 'incidents' && <IncidentsPage />}
            {activeTab === 'graph' && <AttackGraphPage />}
            {activeTab === 'telemetry' && <TelemetryPage />}
            {activeTab === 'benchmark' && <DetectionLabPage />}
            {activeTab === 'threat_intel' && <ThreatIntelPage />}
            {activeTab === 'response' && <ResponseCenterPage />}
          </div>
        </main>
      </div>
    </div>
  );
}
