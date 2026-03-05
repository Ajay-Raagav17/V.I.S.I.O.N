import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useParams } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AuthPage, ProtectedRoute } from './components/auth';
import { LiveCaptionView } from './components/live';
import { DashboardLayout } from './components/dashboard';
import { UploadPage } from './components/upload';
import { NotesViewer } from './components/notes';
import './styles/auth.css';
import './styles/live.css';
import './styles/dashboard.css';
import './styles/upload.css';

/**
 * Live captioning page wrapper
 */
const LiveCaptionPage = () => {
  const handleSessionComplete = (result) => {
    console.log('Session completed:', result);
    // In future, navigate to notes view or show completion message
  };

  return (
    <div className="page-container">
      <nav className="page-nav">
        <Link to="/dashboard" className="back-link">
          ← Back to Dashboard
        </Link>
      </nav>
      <LiveCaptionView onSessionComplete={handleSessionComplete} />
    </div>
  );
};

/**
 * Upload page wrapper
 */
const UploadPageWrapper = () => {
  return (
    <div className="page-container">
      <nav className="page-nav">
        <Link to="/dashboard" className="back-link">
          ← Back to Dashboard
        </Link>
      </nav>
      <UploadPage />
    </div>
  );
};

/**
 * Notes page wrapper with data fetching
 */
const NotesPageWrapper = () => {
  const { lectureId } = useParams();
  const [notes, setNotes] = React.useState(null);
  const [lecture, setLecture] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [notesData, lectureData] = await Promise.all([
          import('./services/notesService').then(m => m.getNotes(lectureId)),
          import('./services/lectureService').then(m => m.getLecture(lectureId))
        ]);
        setNotes(notesData);
        setLecture(lectureData);
      } catch (err) {
        setError(err.message || 'Failed to load notes');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [lectureId]);

  const handleDownloadPDF = async () => {
    const { triggerPDFDownload } = await import('./services/notesService');
    await triggerPDFDownload(lectureId, `${lecture?.title || 'lecture'}-notes.pdf`);
  };

  return (
    <div className="page-container">
      <nav className="page-nav">
        <Link to="/dashboard" className="back-link">
          ← Back to Dashboard
        </Link>
      </nav>
      <NotesViewer
        notes={notes}
        lectureId={lectureId}
        lectureTitle={lecture?.title}
        onDownloadPDF={handleDownloadPDF}
        loading={loading}
        error={error}
      />
    </div>
  );
};

/**
 * Shared lecture page (public, no auth required)
 */
const SharedLecturePage = () => {
  const { shareToken } = useParams();
  const [lecture, setLecture] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const { getSharedLecture } = await import('./services/lectureService');
        const data = await getSharedLecture(shareToken);
        setLecture(data);
      } catch (err) {
        setError(err.message || 'Failed to load shared lecture');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [shareToken]);

  if (loading) {
    return (
      <div className="page-container shared-page">
        <div className="loading-spinner">Loading shared lecture...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container shared-page">
        <div className="error-message">
          <h2>Unable to load shared lecture</h2>
          <p>{error}</p>
          <Link to="/login" className="btn btn-primary">Sign in to VISION</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container shared-page">
      <header className="shared-header">
        <h1 className="text-h1">VISION</h1>
        <p className="text-body">Shared Lecture</p>
      </header>
      
      <div className="shared-content">
        <h2 className="text-h2">{lecture?.title}</h2>
        <p className="text-small">Created: {new Date(lecture?.created_at).toLocaleDateString()}</p>
        
        {lecture?.notes && (
          <>
            <section className="shared-summary">
              <h3 className="text-h3">Summary</h3>
              <p className="text-body">{lecture.notes.summary}</p>
            </section>
            
            {lecture.notes.key_points?.length > 0 && (
              <section className="shared-key-points">
                <h3 className="text-h3">Key Points</h3>
                <ul>
                  {lecture.notes.key_points.map((point, i) => (
                    <li key={i} className="text-body">{point}</li>
                  ))}
                </ul>
              </section>
            )}
            
            {lecture.notes.topics?.length > 0 && (
              <section className="shared-topics">
                <h3 className="text-h3">Topics</h3>
                {lecture.notes.topics.map((topic, i) => (
                  <div key={i} className="shared-topic">
                    <h4 className="text-h4">{topic.title}</h4>
                    <p className="text-body">{topic.content}</p>
                  </div>
                ))}
              </section>
            )}
          </>
        )}
        
        {lecture?.transcript && (
          <section className="shared-transcript">
            <h3 className="text-h3">Transcript</h3>
            <p className="text-body">{lecture.transcript}</p>
          </section>
        )}
      </div>
      
      <footer className="shared-footer">
        <p className="text-small">Powered by VISION - AI Educational Accessibility</p>
        <Link to="/register" className="btn btn-primary">Create your own account</Link>
      </footer>
    </div>
  );
};

/**
 * Main App component with routing and authentication
 */
function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<AuthPage initialMode="login" />} />
          <Route path="/register" element={<AuthPage initialMode="register" />} />
          
          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          />
          <Route
            path="/live"
            element={
              <ProtectedRoute>
                <LiveCaptionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <UploadPageWrapper />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notes/:lectureId"
            element={
              <ProtectedRoute>
                <NotesPageWrapper />
              </ProtectedRoute>
            }
          />
          
          {/* Public shared lecture route */}
          <Route path="/shared/:shareToken" element={<SharedLecturePage />} />
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
