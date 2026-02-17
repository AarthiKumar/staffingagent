import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { DEFAULT_AGENT_ID } from '@/lib/config';
import { CheckCircle, XCircle, AlertTriangle, Loader2, Upload, FileText } from 'lucide-react';

interface UploadJob {
  file: File;
  jobId: string | null;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'requires_input';
  progress: number;
  currentStep: string;
  candidateId?: string;
  documentId?: string;
  missingFields?: string[];
  errorMessage?: string;
  mergeProposal?: any;
  requiresApproval?: boolean;
}

interface ManualInputData {
  jobId: string;
  name: string;
  email: string;
  phone: string;
}

export function UploadCVAsync() {
  const navigate = useNavigate();
  const [uploads, setUploads] = useState<UploadJob[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [useOCR, setUseOCR] = useState(false);
  const [manualInput, setManualInput] = useState<ManualInputData | null>(null);
  const pollingIntervals = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      pollingIntervals.current.forEach(interval => clearInterval(interval));
      pollingIntervals.current.clear();
    };
  }, []);

  const startPolling = useCallback((jobId: string, index: number) => {
    // Clear existing interval if any
    const existingInterval = pollingIntervals.current.get(jobId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    const interval = setInterval(async () => {
      try {
        const status = await apiClient.getUploadStatus(jobId);

        setUploads(prev => prev.map((job, i) => {
          if (i !== index) return job;

          return {
            ...job,
            status: status.status as any,
            progress: status.progress,
            currentStep: status.current_step || '',
            candidateId: status.candidate_id || undefined,
            documentId: status.document_id || undefined,
            missingFields: status.missing_fields || undefined,
            errorMessage: status.error_message || undefined,
            mergeProposal: status.merge_proposal || undefined,
            requiresApproval: status.requires_approval,
          };
        }));

        // Stop polling if completed or failed or requires input
        if (['completed', 'failed', 'requires_input'].includes(status.status)) {
          const interval = pollingIntervals.current.get(jobId);
          if (interval) {
            clearInterval(interval);
            pollingIntervals.current.delete(jobId);
          }

          // Show notification for requires_input
          if (status.status === 'requires_input' && status.missing_fields) {
            // Show manual input form
            setManualInput({
              jobId,
              name: '',
              email: '',
              phone: '',
            });
          }
        }
      } catch (error) {
        console.error('Failed to poll status:', error);
        const interval = pollingIntervals.current.get(jobId);
        if (interval) {
          clearInterval(interval);
          pollingIntervals.current.delete(jobId);
        }
      }
    }, 1000); // Poll every second

    pollingIntervals.current.set(jobId, interval);
  }, []);

  const handleFileSelect = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const fileArray = Array.from(files);

      // Add files to uploads list
      const newUploads: UploadJob[] = fileArray.map(file => ({
        file,
        jobId: null,
        status: 'queued',
        progress: 0,
        currentStep: 'Preparing upload...',
      }));

      setUploads(prev => [...prev, ...newUploads]);

      // Start uploading each file
      for (let i = 0; i < newUploads.length; i++) {
        const file = fileArray[i];
        const uploadIndex = uploads.length + i;

        try {
          // Convert file to base64
          const base64Content = await fileToBase64(file);

          // Start async upload
          const response = await apiClient.uploadCVAsync({
            agent_id: DEFAULT_AGENT_ID,
            document_type: 'resume',
            filename: file.name,
            content_base64: base64Content,
            use_ocr: useOCR,
          });

          // Update with job ID
          setUploads(prev => prev.map((job, idx) => {
            if (idx === uploadIndex) {
              return { ...job, jobId: response.job_id, status: 'processing' };
            }
            return job;
          }));

          // Start polling for status
          startPolling(response.job_id, uploadIndex);

        } catch (error: any) {
          setUploads(prev => prev.map((job, idx) => {
            if (idx === uploadIndex) {
              return {
                ...job,
                status: 'failed',
                errorMessage: error.message || 'Upload failed',
              };
            }
            return job;
          }));
        }
      }
    },
    [uploads.length, useOCR, startPolling]
  );

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        // Remove data:*;base64, prefix
        const base64Content = base64.split(',')[1];
        resolve(base64Content);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleManualInputSubmit = async () => {
    if (!manualInput) return;

    try {
      const result = await apiClient.completeUpload({
        job_id: manualInput.jobId,
        manual_name: manualInput.name,
        manual_email: manualInput.email,
        manual_phone: manualInput.phone,
      });

      if (result.success) {
        setManualInput(null);

        // Update upload status
        setUploads(prev => prev.map(job => {
          if (job.jobId === manualInput.jobId) {
            return {
              ...job,
              status: 'completed',
              progress: 100,
              candidateId: result.candidate_id,
              documentId: result.document_id,
              requiresApproval: result.requires_approval,
              mergeProposal: result.merge_proposal,
            };
          }
          return job;
        }));
      } else if (result.missing_fields) {
        alert(`Still missing fields: ${result.missing_fields.join(', ')}`);
      }
    } catch (error: any) {
      alert(`Failed to submit: ${error.message}`);
    }
  };

  const getStatusIcon = (status: UploadJob['status']) => {
    switch (status) {
      case 'queued':
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'requires_input':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: UploadJob['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'requires_input':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'processing':
      case 'queued':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Upload CVs</h1>
        <p className="text-gray-600 mb-8">
          Upload candidate resumes in PDF, DOCX, or DOC format. Processing happens in the background.
        </p>

        {/* Upload Area */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Drop CVs here or click to browse</h3>
              <p className="text-sm text-gray-600 mb-4">
                Supports PDF, DOCX, and DOC files (max 10MB each)
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc"
                onChange={(e) => handleFileSelect(e.target.files)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button type="button" onClick={() => document.getElementById('file-upload')?.click()}>
                  Select Files
                </Button>
              </label>

              <div className="mt-4">
                <label className="flex items-center justify-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useOCR}
                    onChange={(e) => setUseOCR(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">Use OCR for scanned PDFs</span>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Upload Queue */}
        {uploads.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Upload Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {uploads.map((upload, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${getStatusColor(upload.status)}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3 flex-1">
                        {getStatusIcon(upload.status)}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium truncate">{upload.file.name}</h4>
                          <p className="text-sm opacity-75">{upload.currentStep}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="ml-2">
                        {upload.status}
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    {(upload.status === 'processing' || upload.status === 'queued') && (
                      <div className="mt-3">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Progress</span>
                          <span>{upload.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${upload.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Success Info */}
                    {upload.status === 'completed' && upload.candidateId && (
                      <div className="mt-3 flex items-center justify-between">
                        <span className="text-sm">Candidate created successfully</span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/candidates/${upload.candidateId}`)}
                        >
                          View Profile
                        </Button>
                      </div>
                    )}

                    {/* Error Info */}
                    {upload.status === 'failed' && upload.errorMessage && (
                      <div className="mt-3">
                        <p className="text-sm font-medium">Error:</p>
                        <p className="text-sm">{upload.errorMessage}</p>
                      </div>
                    )}

                    {/* Missing Fields Info */}
                    {upload.status === 'requires_input' && upload.missingFields && (
                      <div className="mt-3">
                        <p className="text-sm font-medium">Missing required fields:</p>
                        <p className="text-sm">{upload.missingFields.join(', ')}</p>
                        <Button
                          size="sm"
                          className="mt-2"
                          onClick={() => setManualInput({
                            jobId: upload.jobId!,
                            name: '',
                            email: '',
                            phone: '',
                          })}
                        >
                          Provide Information
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Manual Input Dialog */}
        {manualInput && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle>Provide Missing Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="name">Full Name *</Label>
                    <Input
                      id="name"
                      value={manualInput.name}
                      onChange={(e) => setManualInput({ ...manualInput, name: e.target.value })}
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={manualInput.email}
                      onChange={(e) => setManualInput({ ...manualInput, email: e.target.value })}
                      placeholder="john@example.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone *</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={manualInput.phone}
                      onChange={(e) => setManualInput({ ...manualInput, phone: e.target.value })}
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <div className="flex space-x-2 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => setManualInput(null)}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleManualInputSubmit}
                      className="flex-1"
                      disabled={!manualInput.name || !manualInput.email || !manualInput.phone}
                    >
                      Submit
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
