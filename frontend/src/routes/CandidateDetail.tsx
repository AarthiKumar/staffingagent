import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';

export function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => apiClient.getCandidateDetail(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return <div className="container mx-auto py-8 px-4">Loading...</div>;
  }

  if (error || !data) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error loading candidate: {(error as Error)?.message || 'Not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <Button variant="outline" onClick={() => navigate(-1)} className="mb-4">
        ← Back to Search
      </Button>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{data.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.email && (
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">Email:</span>
                <span className="text-sm text-gray-600">{data.email}</span>
              </div>
            )}
            {data.location && (
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">Location:</span>
                <span className="text-sm text-gray-600">{data.location}</span>
              </div>
            )}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Last Updated:</span>
              <span className="text-sm text-gray-600">
                {new Date(data.updated).toLocaleDateString()}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.top_skills.map((skill) => (
                <Badge key={skill} variant="default">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {data.certifications.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Certifications</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1">
                {data.certifications.map((cert, idx) => (
                  <li key={idx} className="text-sm text-gray-700">
                    {cert}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {data.availability.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Availability</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.availability.map((avail, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <div className="text-sm font-medium">
                        From: {new Date(avail.from).toLocaleDateString()}
                      </div>
                      {avail.notes && (
                        <div className="text-xs text-gray-600">{avail.notes}</div>
                      )}
                    </div>
                    <Badge variant="success">{avail.capacity_pct}%</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {data.sections.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Experience & Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.sections.map((section, idx) => (
                  <div key={idx}>
                    <div className="text-sm font-medium mb-1 capitalize">{section.type}</div>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {section.text}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
