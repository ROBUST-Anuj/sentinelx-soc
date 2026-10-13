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
import { api, isDemoMode } from './services/api';

export default function App() {
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Auto-authenticate with stored token or demo profile for seamless access
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = api.getToken();
      if (storedToken) {
        setUser({ username: isDemoMode ? 'demo_admin' : 'admin', role: 'admin' });
      } else if (isDemoMode) {
        // In demo mode, automatically log in as demo_admin for instant inspection
        const res = await api.login('demo_admin', 'demo_passphrase');
        setUser({ username: res.username, role: res.role });
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

        {/* Interactive Demo Mode Notice Banner */}
        {isDemoMode && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center justify-between text-xs text-amber-300">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="font-semibold tracking-wide">STATIC DEMONSTRATION MODE:</span>
              <span className="text-amber-200/80">
                Operating with synthetic academic datasets. All incident updates, responses, and metrics are simulated locally in-browser without live backend dependencies.
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-amber-200">
              No Backend / Zero Secrets
            </span>
          </div>
        )}

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
