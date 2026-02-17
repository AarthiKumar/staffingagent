import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth0 } from '@auth0/auth0-react';
import { Search } from './routes/Search';
import CandidateDetail from './routes/CandidateDetail';
import Candidates from './routes/Candidates';
import { Availability } from './routes/Availability';
import { UploadCVAsync } from './routes/UploadCVAsync';
import { AgentSwitcher } from './components/AgentSwitcher';
import { DEFAULT_AGENT_ID } from './lib/config';
import { useApiAuth } from './lib/useApiAuth';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AuthCallback() {
  const { isLoading } = useAuth0();
  if (isLoading) return <div className="flex items-center justify-center h-screen text-gray-500">Logging in...</div>;
  return <Navigate to="/" replace />;
}

function LoginPage() {
  const { loginWithRedirect } = useAuth0();
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="bg-white rounded-2xl shadow-lg p-10 flex flex-col items-center gap-6 max-w-sm w-full">
        <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
          <span className="text-white font-bold text-xl">SA</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-800">Staffing Agent</h1>
        <p className="text-gray-500 text-sm text-center">Sign in to continue</p>
        <button
          onClick={() => loginWithRedirect()}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors"
        >
          Sign In
        </button>
      </div>
    </div>
  );
}

function AppContent() {
  const { isAuthenticated, isLoading, user, logout } = useAuth0();
  const [currentAgent, setCurrentAgent] = useState(DEFAULT_AGENT_ID);
  useApiAuth();

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen text-gray-500">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const roles: string[] = (user as any)?.['https://aal.yookthi.ai/roles'] ?? [];
  const isSuperuser = roles.includes('superuser') || roles.includes('staff');
  const isProjectManager = roles.includes('project_manager');
  const isCandidate = roles.includes('candidate');

  // Debug: Log user object and roles
  console.log('User object:', user);
  console.log('Roles from token:', roles);
  console.log('isSuperuser:', isSuperuser, 'isProjectManager:', isProjectManager, 'isCandidate:', isCandidate);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-10">
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">SA</span>
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Staffing Agent
                </span>
              </Link>

              <div className="flex space-x-1">
                {(isSuperuser || isProjectManager) && (
                  <Link to="/" className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    Search
                  </Link>
                )}
                {(isSuperuser || isProjectManager) && (
                  <Link to="/candidates" className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    Candidates
                  </Link>
                )}
                {(isSuperuser || isCandidate) && (
                  <Link to="/upload" className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    Upload CVs
                  </Link>
                )}
                {(isSuperuser || isProjectManager || isCandidate) && (
                  <Link to="/availability" className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    Availability
                  </Link>
                )}
                {isSuperuser && (
                  <Link to="/users" className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    Users
                  </Link>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <AgentSwitcher currentAgent={currentAgent} onAgentChange={setCurrentAgent} />
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">{user?.email}</span>
                {roles.length > 0 && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium capitalize">
                    {roles[0].replace('_', ' ')}
                  </span>
                )}
                <button
                  onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  className="text-sm text-gray-500 hover:text-red-600 transition-colors"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <Routes>
        {(isSuperuser || isProjectManager) && <Route path="/" element={<Search />} />}
        {(isSuperuser || isProjectManager) && <Route path="/candidates" element={<Candidates />} />}
        {(isSuperuser || isProjectManager) && <Route path="/candidates/:id" element={<CandidateDetail />} />}
        {(isSuperuser || isCandidate) && <Route path="/upload" element={<UploadCVAsync />} />}
        {(isSuperuser || isProjectManager || isCandidate) && <Route path="/availability" element={<Availability />} />}
        {isSuperuser && <Route path="/users" element={<UsersPage />} />}
        <Route path="/candidate/:id" element={<CandidateDetail />} />
        <Route
          path="*"
          element={
            isCandidate && !isSuperuser && !isProjectManager
              ? <Navigate to="/upload" replace />
              : <Navigate to="/" replace />
          }
        />
      </Routes>
    </div>
  );
}

function UsersPage() {
  return (
    <div className="container mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">User Management</h1>
      <p className="text-gray-500">Manage user roles and candidate links.</p>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/callback" element={<AuthCallback />} />
          <Route path="*" element={<AppContent />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
