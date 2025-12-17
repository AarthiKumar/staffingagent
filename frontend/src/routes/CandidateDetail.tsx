import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  ArrowLeft,
  Edit,
  Save,
  X,
  User,
  Mail,
  MapPin,
  FileText,
  Calendar,
  Briefcase,
} from 'lucide-react';

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({
    name: '',
    email: '',
    location: '',
  });

  const { data: candidate, isLoading, error } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => apiClient.getCandidateFull(id!),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; email?: string; location?: string }) =>
      apiClient.updateCandidate(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      setIsEditing(false);
    },
  });

  const handleEdit = () => {
    if (candidate) {
      setEditedData({
        name: candidate.name,
        email: candidate.email || '',
        location: candidate.location || '',
      });
      setIsEditing(true);
    }
  };

  const handleSave = () => {
    const updates: { name?: string; email?: string; location?: string } = {};

    if (editedData.name !== candidate?.name) {
      updates.name = editedData.name;
    }
    if (editedData.email !== (candidate?.email || '')) {
      updates.email = editedData.email || undefined;
    }
    if (editedData.location !== (candidate?.location || '')) {
      updates.location = editedData.location || undefined;
    }

    if (Object.keys(updates).length > 0) {
      updateMutation.mutate(updates);
    } else {
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading candidate details...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error loading candidate: {error?.message || 'Candidate not found'}
        </div>
        <Button onClick={() => navigate('/candidates')} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Candidates
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/candidates')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Candidates
        </Button>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">
              {isEditing ? 'Edit Candidate' : 'Candidate Details'}
            </h1>
            <p className="text-gray-600">
              Last updated: {new Date(candidate.updated_at).toLocaleString()}
            </p>
          </div>
          <div className="flex gap-2">
            {!isEditing ? (
              <Button onClick={handleEdit}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            ) : (
              <>
                <Button onClick={handleSave} disabled={updateMutation.isPending}>
                  <Save className="h-4 w-4 mr-2" />
                  {updateMutation.isPending ? 'Saving...' : 'Save'}
                </Button>
                <Button variant="outline" onClick={handleCancel}>
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Update Error */}
      {updateMutation.isError && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error updating candidate: {updateMutation.error.message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Basic Info */}
        <div className="lg:col-span-1 space-y-6">
          {/* Basic Information Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Basic Information</h2>

            <div className="space-y-4">
              {/* Name */}
              <div>
                <Label htmlFor="name" className="flex items-center mb-2">
                  <User className="h-4 w-4 mr-2 text-gray-500" />
                  Name
                </Label>
                {isEditing ? (
                  <Input
                    id="name"
                    value={editedData.name}
                    onChange={(e) =>
                      setEditedData({ ...editedData, name: e.target.value })
                    }
                    placeholder="Full name"
                  />
                ) : (
                  <p className="text-gray-900">{candidate.name}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <Label htmlFor="email" className="flex items-center mb-2">
                  <Mail className="h-4 w-4 mr-2 text-gray-500" />
                  Email
                </Label>
                {isEditing ? (
                  <Input
                    id="email"
                    type="email"
                    value={editedData.email}
                    onChange={(e) =>
                      setEditedData({ ...editedData, email: e.target.value })
                    }
                    placeholder="email@example.com"
                  />
                ) : (
                  <p className="text-gray-900">{candidate.email || '-'}</p>
                )}
              </div>

              {/* Location */}
              <div>
                <Label htmlFor="location" className="flex items-center mb-2">
                  <MapPin className="h-4 w-4 mr-2 text-gray-500" />
                  Location
                </Label>
                {isEditing ? (
                  <Input
                    id="location"
                    value={editedData.location}
                    onChange={(e) =>
                      setEditedData({ ...editedData, location: e.target.value })
                    }
                    placeholder="City, Country"
                  />
                ) : (
                  <p className="text-gray-900">{candidate.location || '-'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Document Info Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Document
            </h2>
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-medium">Filename:</span>{' '}
                {candidate.document_filename || 'N/A'}
              </p>
              <p>
                <span className="font-medium">Type:</span>{' '}
                {candidate.document_mime_type || 'N/A'}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Document ID: {candidate.document_id}
              </p>
            </div>
          </div>

          {/* Availability Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              Availability
            </h2>
            {candidate.availability.length > 0 ? (
              <div className="space-y-3">
                {candidate.availability.map((avail) => (
                  <div
                    key={avail.id}
                    className="border border-gray-200 rounded p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {new Date(avail.available_from).toLocaleDateString()}
                      </span>
                      <span className="text-sm text-gray-600">
                        {avail.capacity_pct}% capacity
                      </span>
                    </div>
                    {avail.notes && (
                      <p className="text-xs text-gray-500 mt-1">{avail.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No availability data</p>
            )}
            <Button
              variant="outline"
              size="sm"
              className="mt-4 w-full"
              onClick={() => navigate('/availability')}
            >
              Manage Availability
            </Button>
          </div>
        </div>

        {/* Right Column - CV Sections */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Briefcase className="h-5 w-5 mr-2" />
              CV Sections
            </h2>

            {candidate.sections.length > 0 ? (
              <div className="space-y-6">
                {candidate.sections.map((section) => (
                  <div key={section.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                    <h3 className="text-lg font-medium text-gray-900 mb-2 capitalize">
                      {section.type.replace('_', ' ')}
                    </h3>
                    <div className="bg-gray-50 rounded p-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                        {section.text}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No CV sections available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
