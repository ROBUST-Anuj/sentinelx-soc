import React from 'react';
import { 
  ShieldAlert, Activity, AlertTriangle, Terminal, Network, 
  BarChart3, Crosshair, ShieldCheck, ChevronLeft, ChevronRight, LogOut, Radio
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  userRole?: string;
  username?: string;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
  setCollapsed,
  userRole = 'analyst',
  username = 'admin',
  onLogout
}) => {
  const menuItems = [
    { id: 'overview', label: 'SOC Overview', icon: Activity, badge: null },
    { id: 'incidents', label: 'Incidents & Triage', icon: AlertTriangle, badge: 'Active' },
    { id: 'graph', label: 'Attack Graph', icon: Network, badge: 'Reasoning' },
    { id: 'telemetry', label: 'Telemetry Explorer', icon: Terminal, badge: null },
    { id: 'benchmark', label: 'Detection Lab', icon: BarChart3, badge: 'Evaluation' },
    { id: 'threat_intel', label: 'Threat Intel (TI)', icon: Crosshair, badge: null },
    { id: 'response', label: 'Response Center', icon: ShieldCheck, badge: 'Safe' },
  ];

  return (
    <aside style={{
      width: collapsed ? '72px' : '260px',
      backgroundColor: '#0c1322',
      borderRight: '1px solid #1a273f',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      position: 'relative',
      zIndex: 40,
      flexShrink: 0
    }}>
      {/* Brand Header */}
      <div style={{
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        padding: collapsed ? '0 18px' : '0 20px',
        borderBottom: '1px solid #1a273f',
        gap: '12px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          boxShadow: '0 0 15px rgba(14, 165, 233, 0.3)',
          flexShrink: 0
        }}>
          <ShieldAlert size={20} />
        </div>
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
              SentinelX <span style={{ color: '#38bdf8' }}>SOC</span>
            </span>
            <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
              AI Threat Intelligence
            </span>
          </div>
        )}
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              title={collapsed ? item.label : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: isActive ? 'rgba(14, 165, 233, 0.12)' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                borderLeft: isActive ? '3px solid #0ea5e9' : '3px solid transparent',
                cursor: 'pointer',
                textAlign: 'left',
                width: '100%',
                transition: 'all 0.15s ease',
                position: 'relative',
                boxSizing: 'border-box'
              }}
            >
              <Icon size={18} style={{ color: isActive ? '#38bdf8' : '#64748b', flexShrink: 0 }} />
              {!collapsed && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <span style={{ fontSize: '13px', fontWeight: isActive ? 600 : 400 }}>{item.label}</span>
                  {item.badge && (
                    <span style={{
                      fontSize: '9px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: isActive ? 'rgba(14, 165, 233, 0.2)' : '#162238',
                      color: isActive ? '#38bdf8' : '#64748b',
                      fontWeight: 600
                    }}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div style={{ padding: '8px 10px', borderTop: '1px solid #1a273f' }}>
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '10px',
            width: '100%',
            padding: '8px',
            backgroundColor: 'transparent',
            border: 'none',
            color: '#64748b',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span>Collapse Menu</span></>}
        </button>
      </div>

      {/* User Info / Logout Footer */}
      <div style={{
        padding: collapsed ? '14px 10px' : '14px 16px',
        borderTop: '1px solid #1a273f',
        backgroundColor: '#090e1a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between'
      }}>
        {!collapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
              fontWeight: 700,
              fontSize: '12px'
            }}>
              {username.charAt(0).toUpperCase()}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', whiteSpace: 'nowrap' }}>
                {username}
              </span>
              <span style={{ fontSize: '10px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Radio size={8} /> {userRole.toUpperCase()}
              </span>
            </div>
          </div>
        ) : null}

        <button
          onClick={onLogout}
          title="Sign out"
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};
