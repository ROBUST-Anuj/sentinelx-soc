import React from 'react';
import { RefreshCw } from 'lucide-react';

import { isDemoMode } from '../services/api';

interface NavbarProps {
  title: string;
  subtitle: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  title,
  subtitle,
  onRefresh,
  isRefreshing = false
}) => {
  return (
    <header style={{
      height: '64px',
      backgroundColor: '#0c1322',
      borderBottom: '1px solid #1a273f',
      padding: '0 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 30
    }}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
          {title}
        </h1>
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          {subtitle}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* System Health / Demo Status Indicator */}
        {isDemoMode ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderRadius: '20px',
            border: '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#f59e0b',
              boxShadow: '0 0 8px #f59e0b'
            }} />
            <span style={{ fontSize: '12px', color: '#fbbf24', fontWeight: 600 }}>
              Interactive Demo Mode (Sample Telemetry)
            </span>
          </div>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            backgroundColor: '#0f1d2e',
            borderRadius: '20px',
            border: '1px solid #1e3a5f'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 8px #10b981'
            }} />
            <span style={{ fontSize: '12px', color: '#38bdf8', fontWeight: 500 }}>
              API Core Active
            </span>
          </div>
        )}

        {/* Refresh Action Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh Data"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              backgroundColor: '#162238',
              border: '1px solid #233554',
              borderRadius: '6px',
              color: '#e2e8f0',
              cursor: isRefreshing ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 500,
              transition: 'background-color 0.15s ease'
            }}
          >
            <RefreshCw size={14} style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
