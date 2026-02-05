import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Search } from './routes/Search';
import CandidateDetail from './routes/CandidateDetail';
import Candidates from './routes/Candidates';
import { Availability } from './routes/Availability';
import { UploadCVAsync } from './routes/UploadCVAsync';
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
            <Route path="/upload" element={<UploadCVAsync />} />
            <Route path="/candidate/:id" element={<CandidateDetail />} />
            <Route path="/availability" element={<Availability />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
