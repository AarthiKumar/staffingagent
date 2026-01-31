import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Auth0ProviderWithConfig, RequireAuth } from './lib/auth';
import { Search } from './routes/Search';
import CandidateDetail from './routes/CandidateDetail';
import Candidates from './routes/Candidates';
import { Availability } from './routes/Availability';
import { UploadCV } from './routes/UploadCV';
import { Callback } from './routes/Callback';
import { AgentSwitcher } from './components/AgentSwitcher';
import { UserMenu } from './components/UserMenu';
import { DEFAULT_AGENT_ID } from './lib/config';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const [currentAgent, setCurrentAgent] = useState(DEFAULT_AGENT_ID);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Modern Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-10">
              {/* Logo/Brand */}
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">SA</span>
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Staffing Agent
                </span>
              </Link>

              {/* Navigation Links */}
              <div className="flex space-x-1">
                <Link
                  to="/"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Search
                </Link>
                <Link
                  to="/candidates"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Candidates
                </Link>
                <Link
                  to="/upload"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Upload CVs
                </Link>
                <Link
                  to="/availability"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Availability
                </Link>
              </div>
            </div>

            {/* Right side - Agent Switcher and User Menu */}
            <div className="flex items-center space-x-4">
              <AgentSwitcher
                currentAgent={currentAgent}
                onAgentChange={setCurrentAgent}
              />
              <UserMenu />
            </div>
          </div>
        </div>
      </nav>

      <Routes>
        {/* Public route - Auth0 callback */}
        <Route path="/callback" element={<Callback />} />

        {/* Protected routes - require authentication */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Search />
            </RequireAuth>
          }
        />
        <Route
          path="/candidates"
          element={
            <RequireAuth>
              <Candidates />
            </RequireAuth>
          }
        />
        <Route
          path="/candidates/:id"
          element={
            <RequireAuth>
              <CandidateDetail />
            </RequireAuth>
          }
        />
        <Route
          path="/upload"
          element={
            <RequireAuth>
              <UploadCV />
            </RequireAuth>
          }
        />
        <Route
          path="/candidate/:id"
          element={
            <RequireAuth>
              <CandidateDetail />
            </RequireAuth>
          }
        />
        <Route
          path="/availability"
          element={
            <RequireAuth>
              <Availability />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Auth0ProviderWithConfig>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </QueryClientProvider>
    </Auth0ProviderWithConfig>
  );
}

export default App;
