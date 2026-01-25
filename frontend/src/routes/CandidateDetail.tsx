import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
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
  Trash2,
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
  const [editingSections, setEditingSections] = useState<Record<string, string>>({});
  const [sectionTexts, setSectionTexts] = useState<Record<string, string>>({});

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

  const updateSectionMutation = useMutation({
    mutationFn: ({ sectionId, text }: { sectionId: string; text: string }) =>
      apiClient.updateSection(sectionId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
      setEditingSections({});
      setSectionTexts({});
    },
  });

  const deleteSectionMutation = useMutation({
    mutationFn: (sectionId: string) => apiClient.deleteSection(sectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
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

  const handleEditSection = (sectionId: string, currentText: string) => {
    setEditingSections(prev => ({ ...prev, [sectionId]: 'editing' }));
    setSectionTexts(prev => ({ ...prev, [sectionId]: currentText }));
  };

  const handleSaveSection = (sectionId: string) => {
    const text = sectionTexts[sectionId];
    if (text !== undefined) {
      updateSectionMutation.mutate({ sectionId, text });
    }
  };

  const handleCancelSectionEdit = (sectionId: string) => {
    setEditingSections(prev => {
      const newState = { ...prev };
      delete newState[sectionId];
      return newState;
    });
    setSectionTexts(prev => {
      const newState = { ...prev };
      delete newState[sectionId];
      return newState;
    });
  };

  const handleDeleteSection = (sectionId: string, sectionType: string) => {
    if (confirm(`Are you sure you want to delete the "${sectionType}" section? This action cannot be undone.`)) {
      deleteSectionMutation.mutate(sectionId);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-16 bg-white rounded-xl shadow-sm">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading candidate details...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-300 text-red-700 px-6 py-4 rounded-lg shadow-sm">
          <p className="font-medium">Error loading candidate: {error?.message || 'Candidate not found'}</p>
        </div>
        <Button
          onClick={() => navigate('/candidates')}
          className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
        >
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
          className="mb-4 border-gray-300 hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Candidates
        </Button>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
              {isEditing ? 'Edit Candidate' : 'Candidate Details'}
            </h1>
            <p className="text-gray-600">
              Last updated: {new Date(candidate.updated_at).toLocaleString()}
            </p>
          </div>
          <div className="flex gap-3">
            {!isEditing ? (
              <Button
                onClick={handleEdit}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            ) : (
              <>
                <Button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateMutation.isPending ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  className="border-gray-300 hover:bg-gray-50"
                >
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
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-200">
              Basic Information
            </h2>

            <div className="space-y-5">
              {/* Name */}
              <div>
                <Label htmlFor="name" className="flex items-center mb-2 text-sm font-medium text-gray-700">
                  <User className="h-4 w-4 mr-2 text-blue-500" />
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
                    className="border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900 font-medium">{candidate.name}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <Label htmlFor="email" className="flex items-center mb-2 text-sm font-medium text-gray-700">
                  <Mail className="h-4 w-4 mr-2 text-blue-500" />
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
                    className="border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{candidate.email || '-'}</p>
                )}
              </div>

              {/* Location */}
              <div>
                <Label htmlFor="location" className="flex items-center mb-2 text-sm font-medium text-gray-700">
                  <MapPin className="h-4 w-4 mr-2 text-blue-500" />
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
                    className="border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{candidate.location || '-'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Document Info Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-200 flex items-center">
              <FileText className="h-5 w-5 mr-2 text-blue-500" />
              Document
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <span className="text-sm font-medium text-gray-600">Filename:</span>
                <span className="text-sm text-gray-900 text-right ml-2">{candidate.document_filename || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-sm font-medium text-gray-600">Type:</span>
                <span className="text-sm text-gray-900">{candidate.document_mime_type || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-sm font-medium text-gray-600">Embeddings:</span>
                <span className={`text-sm font-medium ${candidate.embeddings_count > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {candidate.embeddings_count}
                </span>
              </div>
              <div className="pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500">
                  ID: {candidate.document_id}
                </p>
              </div>
            </div>
          </div>

          {/* Availability Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-200 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-blue-500" />
              Availability
            </h2>
            {candidate.availability.length > 0 ? (
              <div className="space-y-3">
                {candidate.availability.map((avail) => (
                  <div
                    key={avail.id}
                    className="border border-blue-100 bg-blue-50/30 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-900">
                        {new Date(avail.available_from).toLocaleDateString()}
                      </span>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {avail.capacity_pct}% capacity
                      </span>
                    </div>
                    {avail.notes && (
                      <p className="text-xs text-gray-600 mt-1">{avail.notes}</p>
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
              className="mt-4 w-full border-blue-200 text-blue-600 hover:bg-blue-50"
              onClick={() => navigate('/availability')}
            >
              Manage Availability
            </Button>
          </div>
        </div>

        {/* Right Column - CV Sections */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-200 flex items-center">
              <Briefcase className="h-5 w-5 mr-2 text-blue-500" />
              CV Sections
            </h2>

            {candidate.sections.length > 0 ? (
              <div className="space-y-6">
                {candidate.sections.map((section) => {
                  const isEditingSection = editingSections[section.id] === 'editing';
                  const canEdit = !['full', 'raw_text'].includes(section.type);

                  return (
                    <div key={section.id} className="border-b border-gray-100 pb-6 last:border-b-0">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-base font-semibold text-gray-900 capitalize flex items-center">
                          <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                          {section.type.replace('_', ' ')}
                        </h3>
                        {canEdit && !isEditingSection && (
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditSection(section.id, section.text)}
                              className="border-blue-200 text-blue-600 hover:bg-blue-50"
                            >
                              <Edit className="h-3 w-3 mr-1" />
                              Edit
                            </Button>
                            {!['summary', 'skills', 'certifications'].includes(section.type) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDeleteSection(section.id, section.type)}
                                className="border-red-200 text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        )}
                        {isEditingSection && (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => handleSaveSection(section.id)}
                              disabled={updateSectionMutation.isPending}
                              className="bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                            >
                              <Save className="h-3 w-3 mr-1" />
                              {updateSectionMutation.isPending ? 'Saving...' : 'Save'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCancelSectionEdit(section.id)}
                              className="border-gray-300 hover:bg-gray-50"
                            >
                              <X className="h-3 w-3 mr-1" />
                              Cancel
                            </Button>
                          </div>
                        )}
                      </div>
                      {updateSectionMutation.isError && (
                        <div className="mb-2 text-xs bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded">
                          Error updating section: {updateSectionMutation.error.message}
                        </div>
                      )}
                      <div className="bg-gradient-to-br from-gray-50 to-blue-50/30 rounded-lg p-4 border border-gray-100">
                        {isEditingSection ? (
                          <Textarea
                            value={sectionTexts[section.id] || ''}
                            onChange={(e) =>
                              setSectionTexts(prev => ({ ...prev, [section.id]: e.target.value }))
                            }
                            className="min-h-[200px] font-sans text-sm leading-relaxed border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                            placeholder="Enter section content..."
                          />
                        ) : (
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
                            {section.text}
                          </pre>
                        )}
                      </div>
                    </div>
                  );
                })}
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
