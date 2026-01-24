import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ManualInputDialog } from '@/components/ManualInputDialog';
import { MergeApprovalDialog } from '@/components/MergeApprovalDialog';
import { apiClient } from '@/lib/api';
import { DEFAULT_AGENT_ID } from '@/lib/config';

interface UploadResult {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'manual_input' | 'approval_needed';
  candidate_id?: string;
  document_id?: string;
  sections_count?: number;
  embeddings_count?: number;
  error?: string;
  missing_required_fields?: string[];
  manual_data?: { name?: string; email?: string; phone?: string };
  merge_proposal?: any;
}

export function UploadCV() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploads, setUploads] = useState<UploadResult[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [useOCR, setUseOCR] = useState(false);

  // Manual input dialog state
  const [manualInputDialog, setManualInputDialog] = useState<{
    open: boolean;
    index: number;
    file: File;
    missingFields: string[];
  } | null>(null);

  // Merge approval dialog state
  const [mergeDialog, setMergeDialog] = useState<{
    open: boolean;
    index: number;
    file: File;
    proposal: any;
    documentId: string;
  } | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      index,
      manualData,
    }: {
      file: File;
      index: number;
      manualData?: { manual_name?: string; manual_email?: string; manual_phone?: string };
    }) => {
      setUploads((prev) =>
        prev.map((u, i) => (i === index ? { ...u, status: 'uploading' } : u))
      );

      try {
        const result = await apiClient.uploadCV(file, DEFAULT_AGENT_ID, useOCR, manualData);

        // Handle missing required fields
        if (result.requires_manual_input && result.missing_required_fields) {
          setUploads((prev) =>
            prev.map((u, i) =>
              i === index
                ? {
                    ...u,
                    status: 'manual_input',
                    document_id: result.document_id,
                    missing_required_fields: result.missing_required_fields,
                    manual_data: u.manual_data,
                  }
                : u
            )
          );

          // Show manual input dialog
          setManualInputDialog({
            open: true,
            index,
            file,
            missingFields: result.missing_required_fields,
          });

          return result;
        }

        // Handle duplicate/merge required
        if (result.requires_approval && result.merge_proposal) {
          setUploads((prev) =>
            prev.map((u, i) =>
              i === index
                ? {
                    ...u,
                    status: 'approval_needed',
                    document_id: result.document_id,
                    merge_proposal: result.merge_proposal,
                  }
                : u
            )
          );

          // Show merge approval dialog
          setMergeDialog({
            open: true,
            index,
            file,
            proposal: result.merge_proposal,
            documentId: result.document_id,
          });

          return result;
        }

        // Success - no issues
        setUploads((prev) =>
          prev.map((u, i) =>
            i === index
              ? {
                  ...u,
                  status: 'success',
                  candidate_id: result.candidate_id!,
                  document_id: result.document_id,
                  sections_count: result.sections_count,
                  embeddings_count: result.embeddings_count,
                }
              : u
          )
        );
        queryClient.invalidateQueries({ queryKey: ['candidates'] });
        return result;
      } catch (error) {
        setUploads((prev) =>
          prev.map((u, i) =>
            i === index
              ? {
                  ...u,
                  status: 'error',
                  error: (error as Error).message,
                }
              : u
          )
        );
        throw error;
      }
    },
  });

  const approveMergeMutation = useMutation({
    mutationFn: async ({
      candidateId,
      documentId,
      approvedData,
      index,
    }: {
      candidateId: string;
      documentId: string;
      approvedData: any;
      index: number;
    }) => {
      const result = await apiClient.approveMerge(candidateId, documentId, approvedData);

      setUploads((prev) =>
        prev.map((u, i) =>
          i === index
            ? {
                ...u,
                status: 'success',
                candidate_id: result.candidate_id,
              }
            : u
        )
      );
      queryClient.invalidateQueries({ queryKey: ['candidates'] });

      return result;
    },
  });

  const handleManualInputSubmit = async (data: {
    name?: string;
    email?: string;
    phone?: string;
  }) => {
    if (!manualInputDialog) return;

    const existingData = uploads[manualInputDialog.index]?.manual_data ?? {};
    const mergedManualData = {
      ...existingData,
      ...data,
    };

    setManualInputDialog(null);

    // Re-upload with manual data
    const manualData = {
      manual_name: mergedManualData.name,
      manual_email: mergedManualData.email,
      manual_phone: mergedManualData.phone,
    };

    setUploads((prev) =>
      prev.map((u, i) =>
        i === manualInputDialog.index
          ? {
              ...u,
              manual_data: mergedManualData,
            }
          : u
      )
    );

    uploadMutation.mutate({
      file: manualInputDialog.file,
      index: manualInputDialog.index,
      manualData,
    });
  };

  const handleMergeApprove = async (mergedData: any) => {
    if (!mergeDialog) return;

    const { proposal, documentId, index } = mergeDialog;

    setMergeDialog(null);

    approveMergeMutation.mutate({
      candidateId: proposal.existing_candidate_id,
      documentId,
      approvedData: mergedData,
      index,
    });
  };

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;

      const validFiles = Array.from(files).filter((file) => {
        const extension = file.name.split('.').pop()?.toLowerCase();
        return ['pdf', 'docx', 'doc', 'txt'].includes(extension || '');
      });

      if (validFiles.length === 0) {
        alert('Please select valid CV files (PDF, DOCX, DOC, or TXT)');
        return;
      }

      const newUploads: UploadResult[] = validFiles.map((file) => ({
        file,
        status: 'pending',
      }));

      setUploads((prev) => [...prev, ...newUploads]);

      // Start uploading files
      newUploads.forEach((upload, i) => {
        const index = uploads.length + i;
        uploadMutation.mutate({ file: upload.file, index });
      });
    },
    [uploads.length, uploadMutation]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
    },
    [handleFiles]
  );

  const clearUploads = () => {
    setUploads([]);
  };

  const getStatusBadge = (status: UploadResult['status']) => {
    switch (status) {
      case 'pending':
        return <Badge variant="default">Pending</Badge>;
      case 'uploading':
        return <Badge variant="default">Uploading...</Badge>;
      case 'success':
        return <Badge variant="default" className="bg-green-600">Success</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'manual_input':
        return <Badge variant="default" className="bg-orange-500">Needs Info</Badge>;
      case 'approval_needed':
        return <Badge variant="default" className="bg-blue-600">Needs Approval</Badge>;
    }
  };

  const successfulUploads = uploads.filter((u) => u.status === 'success').length;
  const failedUploads = uploads.filter((u) => u.status === 'error').length;
  const pendingApproval = uploads.filter((u) => u.status === 'approval_needed').length;

  return (
    <>
      <div className="container mx-auto py-8 px-4">
        <div className="mb-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Upload CVs
          </h1>
          <p className="text-gray-600">
            Upload candidate resumes to add them to the database. Supported formats: PDF, DOCX, DOC, TXT
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload Files</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragging
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="text-4xl">📄</div>
                    <div>
                      <p className="text-lg font-medium mb-1">Drop CV files here</p>
                      <p className="text-sm text-gray-500">or click to browse</p>
                    </div>
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.docx,.doc,.txt"
                      onChange={handleFileInput}
                      className="hidden"
                      id="file-input"
                    />
                    <label htmlFor="file-input">
                      <Button variant="outline" className="cursor-pointer" asChild>
                        <span>Browse Files</span>
                      </Button>
                    </label>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="ocr"
                    checked={useOCR}
                    onChange={(e) => setUseOCR(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <label htmlFor="ocr" className="text-sm">
                    Enable OCR for scanned documents (slower)
                  </label>
                </div>

                {uploads.length > 0 && (
                  <div className="pt-4 border-t">
                    <div className="flex justify-between items-center mb-3">
                      <div className="text-sm text-gray-600">
                        {successfulUploads} successful{pendingApproval > 0 && `, ${pendingApproval} pending approval`}
                        {failedUploads > 0 && `, ${failedUploads} failed`}
                      </div>
                      <Button variant="outline" size="sm" onClick={clearUploads}>
                        Clear All
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Instructions</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                  <li>Select or drag one or more CV files (PDF, DOCX, DOC, or TXT)</li>
                  <li>Files will be automatically uploaded and processed</li>
                  <li>If required information is missing, you'll be prompted to provide it</li>
                  <li>If a duplicate candidate is found, you'll review and approve the merge</li>
                  <li>The system extracts skills, experience, and certifications</li>
                  <li>Embeddings are generated for semantic search</li>
                  <li>Candidates become immediately searchable</li>
                </ol>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle>Upload History</CardTitle>
              </CardHeader>
              <CardContent>
                {uploads.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No uploads yet</div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {uploads.map((upload, index) => (
                      <div
                        key={index}
                        className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{upload.file.name}</div>
                            <div className="text-xs text-gray-500">
                              {(upload.file.size / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <div className="ml-3">{getStatusBadge(upload.status)}</div>
                        </div>

                        {upload.status === 'success' && (
                          <div className="mt-3 space-y-2">
                            <div className="text-xs text-gray-600">
                              <div>✓ {upload.sections_count} sections extracted</div>
                              <div>✓ {upload.embeddings_count} embeddings created</div>
                            </div>
                            {upload.candidate_id && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => navigate(`/candidate/${upload.candidate_id}`)}
                                className="w-full"
                              >
                                View Candidate
                              </Button>
                            )}
                          </div>
                        )}

                        {upload.status === 'manual_input' && (
                          <div className="mt-2 text-xs text-orange-600">
                            Please provide missing information: {upload.missing_required_fields?.join(', ')}
                          </div>
                        )}

                        {upload.status === 'approval_needed' && (
                          <div className="mt-2 text-xs text-blue-600">
                            Duplicate candidate detected. Please review and approve the merge.
                          </div>
                        )}

                        {upload.status === 'error' && (
                          <div className="mt-2 text-xs text-red-600">{upload.error}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Manual Input Dialog */}
      {manualInputDialog && (
        <ManualInputDialog
          open={manualInputDialog.open}
          onClose={() => setManualInputDialog(null)}
          onSubmit={handleManualInputSubmit}
          missingFields={manualInputDialog.missingFields}
          filename={manualInputDialog.file.name}
          initialValues={uploads[manualInputDialog.index]?.manual_data}
        />
      )}

      {/* Merge Approval Dialog */}
      {mergeDialog && (
        <MergeApprovalDialog
          open={mergeDialog.open}
          onClose={() => setMergeDialog(null)}
          onApprove={handleMergeApprove}
          mergeProposal={mergeDialog.proposal}
          filename={mergeDialog.file.name}
          isSubmitting={approveMergeMutation.isPending}
        />
      )}
    </>
  );
}
