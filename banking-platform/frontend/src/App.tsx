import React, { useState, useEffect } from 'react';
import { Navbar, AppTab } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { TransferPage } from './pages/TransferPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { ProfilePage } from './pages/ProfilePage';
import { VerificationModal } from './components/VerificationModal';
import { ReceiptModal } from './components/ReceiptModal';
import { DemoLabModal } from './components/DemoLabModal';
import { TransferResult, UserSession } from './types';
import { api } from './services/api';
import { telemetry } from './services/telemetry';

export const App: React.FC = () => {
  const [session, setSession] = useState<UserSession | null>(null);
  
  // Resolve initial tab based on browser pathname
  const getInitialTab = (): AppTab => {
    const path = window.location.pathname.replace(/^\/+/, '').toLowerCase();
    if (path === 'transfer') return 'transfer';
    if (path === 'transactions') return 'transactions';
    if (path === 'accounts') return 'accounts';
    if (path === 'profile') return 'profile';
    return 'dashboard';
  };

  const [currentTab, setCurrentTab] = useState<AppTab>(getInitialTab);

  // Modal states
  const [activeReceipt, setActiveReceipt] = useState<TransferResult | null>(null);
  const [verificationPendingTx, setVerificationPendingTx] = useState<TransferResult | null>(null);
  const [demoLabOpen, setDemoLabOpen] = useState<boolean>(false);

  useEffect(() => {
    telemetry.init();
    const token = localStorage.getItem('nexabank_token');
    const user = localStorage.getItem('nexabank_user');
    const role = localStorage.getItem('nexabank_role');
    if (token && user) {
      setSession({
        token,
        username: user,
        role: role || 'customer',
      });
    }

    const handlePopState = () => {
      const path = window.location.pathname.replace(/^\/+/, '').toLowerCase();
      if (path === 'transfer' || path === 'transactions' || path === 'accounts' || path === 'profile' || path === 'dashboard') {
        setCurrentTab(path as AppTab);
      } else {
        setCurrentTab('dashboard');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleTabChange = (tab: AppTab) => {
    setCurrentTab(tab);
    if (window.location.pathname !== `/${tab}`) {
      window.history.pushState(null, '', `/${tab}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('nexabank_token');
    localStorage.removeItem('nexabank_user');
    localStorage.removeItem('nexabank_role');
    setSession(null);
    window.history.pushState(null, '', '/login');
  };

  const handleLoginSuccess = (userSession: UserSession) => {
    setSession(userSession);
    const initial = getInitialTab();
    window.history.pushState(null, '', `/${initial}`);
    setCurrentTab(initial);
  };

  const handleTransferComplete = (res: TransferResult) => {
    setActiveReceipt(res);
  };

  const handleRequestVerification = (res: TransferResult) => {
    setVerificationPendingTx(res);
  };

  const handleVerificationSubmit = async (code: string) => {
    if (!verificationPendingTx) return;
    const finalResult = await api.submitVerification(verificationPendingTx.id, code);
    setVerificationPendingTx(null);
    setActiveReceipt(finalResult);
  };

  if (!session) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={handleTabChange}
        username={session.username}
        onLogout={handleLogout}
        onOpenDemoLab={() => setDemoLabOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {(currentTab === 'dashboard' || currentTab === 'accounts') && (
          <DashboardPage
            onNavigateTransfer={() => handleTabChange('transfer')}
            onNavigateTransactions={() => handleTabChange('transactions')}
          />
        )}

        {currentTab === 'transfer' && (
          <TransferPage
            onTransferComplete={handleTransferComplete}
            onRequestVerification={handleRequestVerification}
          />
        )}

        {currentTab === 'transactions' && (
          <TransactionsPage
            onSelectReceipt={(tx) => setActiveReceipt(tx)}
          />
        )}

        {currentTab === 'profile' && (
          <ProfilePage
            session={session}
            onNavigateTab={handleTabChange}
            onOpenDemoLab={() => setDemoLabOpen(true)}
          />
        )}
      </main>

      {/* Verification Step-up Modal */}
      <VerificationModal
        isOpen={!!verificationPendingTx}
        onClose={() => setVerificationPendingTx(null)}
        onSubmit={handleVerificationSubmit}
        transferId={verificationPendingTx?.id || ''}
        mockCode={verificationPendingTx?.mock_challenge_code}
      />

      {/* Confirmation Receipt Modal */}
      <ReceiptModal
        transfer={activeReceipt}
        onClose={() => {
          setActiveReceipt(null);
          handleTabChange('dashboard');
        }}
      />

      {/* Security Demonstration Mode Lab Modal */}
      <DemoLabModal
        isOpen={demoLabOpen}
        onClose={() => setDemoLabOpen(false)}
      />

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        <p>&copy; {new Date().getFullYear()} NexaBank Financial Group. All deposits protected by multi-layer AI security backend.</p>
      </footer>
    </div>
  );
};

export default App;
