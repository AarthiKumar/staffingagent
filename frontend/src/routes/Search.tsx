import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FiltersPanel } from '@/components/FiltersPanel';
import { ResultsTable } from '@/components/ResultsTable';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { SearchFilters, SearchRequest } from '@/lib/types';
import { DEFAULT_AGENT_ID } from '@/lib/config';

export function Search() {
  const [filters, setFilters] = useState<SearchFilters>({});
  const [queryText, setQueryText] = useState('');
  const [useLLMRerank, setUseLLMRerank] = useState(false);
  const [searchTrigger, setSearchTrigger] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', filters, queryText, useLLMRerank, searchTrigger],
    queryFn: async () => {
      const request: SearchRequest = {
        agent_id: DEFAULT_AGENT_ID,
        filters,
        text: queryText || undefined,
        use_llm_rerank: useLLMRerank,
        top_k: 50,
      };
      return apiClient.search(request);
    },
    enabled: searchTrigger > 0,
  });

  const handleSearch = () => {
    setSearchTrigger((prev) => prev + 1);
  };

  const handleClearFilters = () => {
    setFilters({});
    setQueryText('');
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Candidate Search</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <FiltersPanel
            filters={filters}
            onChange={setFilters}
            onClear={handleClearFilters}
          />
        </div>

        <div className="lg:col-span-3 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Semantic Search</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="query">Natural Language Query</Label>
                <Textarea
                  id="query"
                  placeholder="Describe what you're looking for... e.g., 'Need a senior DevOps engineer with Kubernetes and AWS experience'"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={useLLMRerank}
                    onChange={(e) => setUseLLMRerank(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Use LLM Re-ranking</span>
                </label>

                <Button onClick={handleSearch} disabled={isLoading}>
                  {isLoading ? 'Searching...' : 'Search'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              Error: {(error as Error).message}
            </div>
          )}

          {data && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm text-gray-600">
                  Found {data.results.length} candidates
                  {data.flags.reranked && ' (LLM re-ranked)'}
                </div>
              </div>
              <ResultsTable results={data.results} />
            </div>
          )}

          {searchTrigger === 0 && (
            <div className="text-center py-12 text-gray-500">
              Configure your search criteria and click Search to find candidates
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
