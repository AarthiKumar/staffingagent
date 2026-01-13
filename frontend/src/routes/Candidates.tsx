import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Search, User, Calendar, FileText } from 'lucide-react';

export default function Candidates() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const pageSize = 50;

  const { data, isLoading, error } = useQuery({
    queryKey: ['candidates', page, search],
    queryFn: () => apiClient.listCandidates(page, pageSize, search || undefined),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
          Candidate Management
        </h1>
        <p className="text-gray-600">View and manage all candidate CVs</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 h-5 w-5" />
            <Input
              type="text"
              placeholder="Search by name or email..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6">
            Search
          </Button>
          {search && (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearch('');
                setSearchInput('');
                setPage(1);
              }}
              className="border-gray-300 hover:bg-gray-50"
            >
              Clear
            </Button>
          )}
        </div>
      </form>

      {/* Results Summary */}
      {data && (
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm text-gray-600 font-medium">
            Showing <span className="text-blue-600">{(page - 1) * pageSize + 1}</span>-
            <span className="text-blue-600">{Math.min(page * pageSize, data.total)}</span> of <span className="text-blue-600">{data.total}</span> candidates
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error loading candidates: {error.message}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-200 border-t-blue-600"></div>
          <p className="mt-3 text-gray-600 font-medium">Loading candidates...</p>
        </div>
      )}

      {/* Candidates Table */}
      {data && data.candidates.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gradient-to-r from-blue-50 to-indigo-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Availability
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Updated
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {data.candidates.map((candidate) => (
                <tr
                  key={candidate.id}
                  className="hover:bg-blue-50/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/candidates/${candidate.id}`)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                        <User className="h-5 w-5 text-white" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-semibold text-gray-900">
                          {candidate.name}
                        </div>
                        {candidate.document_filename && (
                          <div className="text-xs text-gray-500 flex items-center mt-0.5">
                            <FileText className="h-3 w-3 mr-1 text-blue-400" />
                            {candidate.document_filename}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {candidate.email || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {candidate.location || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {candidate.availability_from ? (
                      <div className="flex items-center text-sm">
                        <Calendar className="h-4 w-4 mr-1.5 text-blue-500" />
                        <span className="text-gray-900 font-medium">
                          {new Date(candidate.availability_from).toLocaleDateString()}
                        </span>
                        {candidate.capacity_pct && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            {candidate.capacity_pct}%
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {new Date(candidate.updated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/candidates/${candidate.id}`);
                      }}
                      className="border-blue-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300 font-medium"
                    >
                      View/Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {data && data.candidates.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="w-16 h-16 mx-auto bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center">
            <User className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-semibold text-gray-900">No candidates found</h3>
          <p className="mt-2 text-sm text-gray-500 max-w-sm mx-auto">
            {search
              ? 'Try adjusting your search query or clearing filters'
              : 'Get started by uploading candidate CVs to build your talent pool'}
          </p>
          {!search && (
            <div className="mt-6">
              <Button
                onClick={() => navigate('/upload')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2"
              >
                Upload CVs
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between bg-white px-6 py-4 rounded-xl shadow-sm border border-gray-200">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </Button>
          <span className="text-sm font-medium text-gray-700">
            Page <span className="text-blue-600">{page}</span> of <span className="text-blue-600">{totalPages}</span>
          </span>
          <Button
            variant="outline"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
