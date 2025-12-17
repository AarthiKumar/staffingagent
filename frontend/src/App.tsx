import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Search } from './routes/Search';
import CandidateDetail from './routes/CandidateDetail';
import Candidates from './routes/Candidates';
import { Availability } from './routes/Availability';
import { UploadCV } from './routes/UploadCV';
import { AgentSwitcher } from './components/AgentSwitcher';
import { DEFAULT_AGENT_ID } from './lib/config';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [currentAgent, setCurrentAgent] = useState(DEFAULT_AGENT_ID);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white border-b border-gray-200">
            <div className="container mx-auto px-4 py-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-8">
                  <Link to="/" className="text-xl font-bold text-gray-900">
                    Staffing Agent
                  </Link>
                  <div className="flex space-x-4">
                    <Link
                      to="/"
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Search
                    </Link>
                    <Link
                      to="/candidates"
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Candidates
                    </Link>
                    <Link
                      to="/upload"
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Upload CVs
                    </Link>
                    <Link
                      to="/availability"
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Availability
                    </Link>
                  </div>
                </div>
                <AgentSwitcher
                  currentAgent={currentAgent}
                  onAgentChange={setCurrentAgent}
                />
              </div>
            </div>
          </nav>

          <Routes>
            <Route path="/" element={<Search />} />
            <Route path="/candidates" element={<Candidates />} />
            <Route path="/candidates/:id" element={<CandidateDetail />} />
            <Route path="/upload" element={<UploadCV />} />
            <Route path="/candidate/:id" element={<CandidateDetail />} />
            <Route path="/availability" element={<Availability />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
