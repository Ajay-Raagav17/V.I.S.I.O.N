/**
 * DashboardLayout Component
 * Premium clean dashboard with modern Linear/Stripe-inspired UI
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import LectureHistory from './LectureHistory';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const getUserInitial = () => {
    return user?.email?.charAt(0).toUpperCase() || 'U';
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'history':
        return <LectureHistory />;
      case 'home':
      default:
        return (
          <div className="dashboard-home">
            <div className="dashboard-welcome">
              <h1 className="welcome-title">Welcome to VISION</h1>
              <p className="welcome-subtitle">
                Turn speech into structured intelligence.
              </p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">📚</div>
                <p className="stat-value">0</p>
                <p className="stat-label">Total Lectures</p>
              </div>
              <div className="stat-card">
                <div className="stat-icon purple">📝</div>
                <p className="stat-value">0</p>
                <p className="stat-label">Study Notes</p>
              </div>
              <div className="stat-card">
                <div className="stat-icon green">⏱️</div>
                <p className="stat-value">0h</p>
                <p className="stat-label">Hours Transcribed</p>
              </div>
              <div className="stat-card">
                <div className="stat-icon orange">📄</div>
                <p className="stat-value">0</p>
                <p className="stat-label">PDFs Generated</p>
              </div>
            </div>

            {/* Feature Cards */}
            <h2 className="section-title">Quick Actions</h2>
            <div className="feature-cards">
              <Link to="/live" className="feature-card" data-testid="feature-card-speech">
                <div className="feature-icon-wrapper live">🎤</div>
                <h3>Speech to Text</h3>
                <p>Convert live audio into accurate real-time text.</p>
                <span className="feature-action">
                  Start Session
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </span>
              </Link>

              <Link to="/upload" className="feature-card" data-testid="feature-card-summary">
                <div className="feature-icon-wrapper upload">📁</div>
                <h3>AI Summary</h3>
                <p>Automatically extract key points and insights.</p>
                <span className="feature-action">
                  Upload File
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </span>
              </Link>

              <button
                onClick={() => setActiveTab('history')}
                className="feature-card feature-card-button"
                data-testid="feature-card-pdf"
              >
                <div className="feature-icon-wrapper history">📄</div>
                <h3>PDF Export</h3>
                <p>Download your sessions as clean, structured PDFs.</p>
                <span className="feature-action">
                  View History
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </span>
              </button>

              <Link to="/live" className="feature-card" data-testid="feature-card-nodes">
                <div className="feature-icon-wrapper nodes">🔗</div>
                <h3>Node Generation</h3>
                <p>Transform content into connected knowledge nodes.</p>
                <span className="feature-action">
                  Explore
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </span>
              </Link>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-left">
          <button
            className="mobile-menu-button"
            onClick={toggleMobileMenu}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="24" height="24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
          <h1>VISION</h1>
        </div>

        <nav className={`dashboard-nav ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <button
            onClick={() => { setActiveTab('home'); setMobileMenuOpen(false); }}
            className={`nav-button ${activeTab === 'home' ? 'active' : ''}`}
            aria-current={activeTab === 'home' ? 'page' : undefined}
          >
            Home
          </button>
          <button
            onClick={() => { setActiveTab('history'); setMobileMenuOpen(false); }}
            className={`nav-button ${activeTab === 'history' ? 'active' : ''}`}
            aria-current={activeTab === 'history' ? 'page' : undefined}
          >
            My Lectures
          </button>
        </nav>

        <div className="user-info">
          <div className="user-avatar">{getUserInitial()}</div>
          <div className="user-details">
            <span className="user-email">{user?.email}</span>
            <span className="user-role">Student</span>
          </div>
          <button onClick={handleLogout} className="logout-button" aria-label="Log out">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {activeTab !== 'home' && (
          <button
            onClick={() => setActiveTab('home')}
            className="back-link"
            aria-label="Back to home"
          >
            ← Back to Home
          </button>
        )}
        {renderContent()}
      </main>
    </div>
  );
};

export default DashboardLayout;
