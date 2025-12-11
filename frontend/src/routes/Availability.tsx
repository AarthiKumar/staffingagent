import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { apiClient } from '@/lib/api';

export function Availability() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['availability'],
    queryFn: () => apiClient.listAvailability(),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadAvailabilityCSV(file),
    onSuccess: (result) => {
      alert(`Success! Created: ${result.created}, Updated: ${result.updated}`);
      if (result.errors.length > 0) {
        console.error('Errors:', result.errors);
      }
      queryClient.invalidateQueries({ queryKey: ['availability'] });
      setSelectedFile(null);
    },
    onError: (error) => {
      alert(`Upload failed: ${(error as Error).message}`);
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Availability Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Upload CSV</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Upload a CSV file with columns: email, available_from, capacity_pct, notes
                </p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
              {selectedFile && (
                <div>
                  <p className="text-sm mb-2">Selected: {selectedFile.name}</p>
                  <Button
                    onClick={handleUpload}
                    disabled={uploadMutation.isPending}
                    className="w-full"
                  >
                    {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Availability Records</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading && <div>Loading...</div>}
              {error && (
                <div className="text-red-600">
                  Error: {(error as Error).message}
                </div>
              )}
              {data && data.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No availability records found
                </div>
              )}
              {data && data.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Candidate</TableHead>
                      <TableHead>Available From</TableHead>
                      <TableHead>Capacity</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>{record.candidate_name}</TableCell>
                        <TableCell>
                          {new Date(record.available_from).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{record.capacity_pct}%</TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {record.notes || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
