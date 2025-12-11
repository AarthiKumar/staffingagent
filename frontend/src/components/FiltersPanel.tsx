import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { SearchFilters } from '@/lib/types';

interface FiltersPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onClear: () => void;
}

export function FiltersPanel({ filters, onChange, onClear }: FiltersPanelProps) {
  const handleSkillsChange = (value: string) => {
    const skills = value.split(',').map(s => s.trim()).filter(Boolean);
    onChange({ ...filters, required_skills: skills });
  };

  const handleCertsChange = (value: string) => {
    const certs = value.split(',').map(s => s.trim()).filter(Boolean);
    onChange({ ...filters, required_certs: certs });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="skills">Required Skills (comma-separated)</Label>
          <Input
            id="skills"
            placeholder="e.g., python, kubernetes, terraform"
            value={filters.required_skills?.join(', ') || ''}
            onChange={(e) => handleSkillsChange(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="certs">Required Certifications (comma-separated)</Label>
          <Input
            id="certs"
            placeholder="e.g., AWS DevOps Professional"
            value={filters.required_certs?.join(', ') || ''}
            onChange={(e) => handleCertsChange(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="location">Location</Label>
          <Input
            id="location"
            placeholder="e.g., San Francisco, CA"
            value={filters.location || ''}
            onChange={(e) => onChange({ ...filters, location: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="availability">Available From (YYYY-MM-DD)</Label>
          <Input
            id="availability"
            type="date"
            value={filters.availability_from || ''}
            onChange={(e) => onChange({ ...filters, availability_from: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="capacity">Min Capacity %</Label>
          <Input
            id="capacity"
            type="number"
            min="0"
            max="100"
            value={filters.capacity_pct_min || ''}
            onChange={(e) => onChange({ ...filters, capacity_pct_min: parseInt(e.target.value) || undefined })}
          />
        </div>

        <Button variant="outline" onClick={onClear} className="w-full">
          Clear Filters
        </Button>
      </CardContent>
    </Card>
  );
}
