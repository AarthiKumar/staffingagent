import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { WhyInfo } from '@/lib/types';

interface WhyCardProps {
  why: WhyInfo;
}

export function WhyCard({ why }: WhyCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Why This Match</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {why.skills.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Matched Skills</div>
            <div className="flex flex-wrap gap-2">
              {why.skills.map((skill) => (
                <Badge key={skill} variant="success">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {why.certs.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Matched Certifications</div>
            <div className="flex flex-wrap gap-2">
              {why.certs.map((cert) => (
                <Badge key={cert} variant="warning">
                  {cert}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {why.snippets.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Relevant Experience</div>
            <div className="space-y-2">
              {why.snippets.map((snippet, idx) => (
                <div key={idx} className="text-sm p-3 bg-gray-50 rounded-md">
                  <div className="text-xs text-gray-500 mb-1">{snippet.section}</div>
                  <div className="text-gray-700">{snippet.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
