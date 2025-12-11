import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from './ui/table';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { SearchResult } from '@/lib/types';

interface ResultsTableProps {
  results: SearchResult[];
}

export function ResultsTable({ results }: ResultsTableProps) {
  const navigate = useNavigate();

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No candidates found. Try adjusting your filters.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Candidate</TableHead>
          <TableHead>Top Skills</TableHead>
          <TableHead>Availability</TableHead>
          <TableHead>Score</TableHead>
          <TableHead>Why</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {results.map((result) => (
          <TableRow key={result.candidate_id}>
            <TableCell>
              <div className="font-medium">{result.name}</div>
              <div className="text-xs text-gray-500">Updated: {new Date(result.updated).toLocaleDateString()}</div>
            </TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {result.why.skills.slice(0, 5).map((skill) => (
                  <Badge key={skill} variant="default">
                    {skill}
                  </Badge>
                ))}
              </div>
            </TableCell>
            <TableCell>
              {result.availability ? (
                <div>
                  <div className="text-sm">{new Date(result.availability.from_date).toLocaleDateString()}</div>
                  <Badge variant="success">{result.availability.capacity_pct}%</Badge>
                </div>
              ) : (
                <span className="text-gray-400">Not set</span>
              )}
            </TableCell>
            <TableCell>
              <span className="font-mono font-semibold">{result.score.toFixed(2)}</span>
            </TableCell>
            <TableCell className="max-w-xs">
              {result.why.snippets.length > 0 && (
                <div className="text-xs text-gray-600 truncate">
                  {result.why.snippets[0].text.substring(0, 80)}...
                </div>
              )}
            </TableCell>
            <TableCell>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/candidate/${result.candidate_id}`)}
              >
                View
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
