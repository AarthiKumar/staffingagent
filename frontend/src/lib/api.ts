import {
  SearchRequest,
  SearchResponse,
  CandidateDetail,
  AvailabilityRecord,
  CandidateListResponse,
  CandidateFullDetail,
  CandidateUpdate,
  UserListItem,
} from './types';
import { API_BASE_URL } from './config';

class APIClient {
  private baseURL: string;
  private getAccessToken?: () => Promise<string>;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setTokenGetter(getter: () => Promise<string>) {
    this.getAccessToken = getter;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (this.getAccessToken) {
      try {
        const token = await this.getAccessToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
      } catch (_e) {
        // proceed without token
      }
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getCandidateDetail(candidateId: string): Promise<CandidateDetail> {
    return this.request<CandidateDetail>(`/search/candidates/${candidateId}`);
  }

  async listAvailability(): Promise<AvailabilityRecord[]> {
    return this.request<AvailabilityRecord[]>('/availability/');
  }

  async updateAvailability(
    candidateId: string,
    data: {
      available_from: string;
      capacity_pct: number;
      notes?: string;
    }
  ): Promise<AvailabilityRecord> {
    return this.request<AvailabilityRecord>(`/availability/${candidateId}`, {
      method: 'PUT',
      body: JSON.stringify({
        candidate_id: candidateId,
        ...data,
      }),
    });
  }

  async uploadAvailabilityCSV(file: File): Promise<{
    created: number;
    updated: number;
    errors: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseURL}/availability/upload`;
    const headers: Record<string, string> = {};
    if (this.getAccessToken) {
      try {
        const token = await this.getAccessToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
      } catch (_e) {}
    }
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async parseNL(agentId: string, text: string): Promise<any> {
    return this.request<any>('/nl/parse', {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, text }),
    });
  }

  async uploadCV(
    file: File,
    agentId: string = 'staffing',
    useOCR: boolean = false,
    manualData?: {
      manual_name?: string;
      manual_email?: string;
      manual_phone?: string;
    }
  ): Promise<{
    document_id: string;
    candidate_id: string | null;
    sections_count: number;
    embeddings_count: number;
    missing_required_fields?: string[];
    requires_manual_input?: boolean;
    merge_proposal?: any;
    requires_approval?: boolean;
  }> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const base64Content = btoa(
            new Uint8Array(e.target?.result as ArrayBuffer)
              .reduce((data, byte) => data + String.fromCharCode(byte), '')
          );

          const response = await this.request<{
            document_id: string;
            candidate_id: string | null;
            sections_count: number;
            embeddings_count: number;
            missing_required_fields?: string[];
            requires_manual_input?: boolean;
            merge_proposal?: any;
            requires_approval?: boolean;
          }>('/ingest/', {
            method: 'POST',
            body: JSON.stringify({
              agent_id: agentId,
              document_type: 'resume',
              filename: file.name,
              content_base64: base64Content,
              use_ocr: useOCR,
              ...manualData,
            }),
          });

          resolve(response);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsArrayBuffer(file);
    });
  }

  async approveMerge(
    candidateId: string,
    newDocumentId: string,
    approvedData: {
      name: string;
      email?: string | null;
      phone?: string | null;
      location?: string | null;
    }
  ): Promise<{
    success: boolean;
    candidate_id: string;
    message: string;
  }> {
    return this.request('/ingest/approve-merge', {
      method: 'POST',
      body: JSON.stringify({
        candidate_id: candidateId,
        new_document_id: newDocumentId,
        approved_data: approvedData,
      }),
    });
  }

  async listCandidates(
    page: number = 1,
    pageSize: number = 50,
    search?: string
  ): Promise<CandidateListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) {
      params.append('search', search);
    }
    return this.request<CandidateListResponse>(`/candidates/?${params.toString()}`);
  }

  async getCandidateFull(candidateId: string): Promise<CandidateFullDetail> {
    return this.request<CandidateFullDetail>(`/candidates/${candidateId}`);
  }

  async updateCandidate(
    candidateId: string,
    data: CandidateUpdate
  ): Promise<{
    id: string;
    name: string;
    email?: string;
    phone?: string;
    location?: string;
    updated_at: string;
  }> {
    return this.request(`/candidates/${candidateId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async updateSection(
    sectionId: string,
    text: string
  ): Promise<{
    id: string;
    type: string;
    text: string;
    updated: boolean;
    embeddings_regenerated: boolean;
  }> {
    return this.request(`/sections/${sectionId}`, {
      method: 'PUT',
      body: JSON.stringify({ text }),
    });
  }

  async deleteSection(sectionId: string): Promise<{
    id: string;
    deleted: boolean;
  }> {
    return this.request(`/sections/${sectionId}`, {
      method: 'DELETE',
    });
  }

  // Async upload methods
  async uploadCVAsync(data: {
    agent_id: string;
    document_type: string;
    filename: string;
    content_base64: string;
    use_ocr?: boolean;
  }): Promise<{
    job_id: string;
    status: string;
    message: string;
  }> {
    return this.request('/async/upload-async', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUploadStatus(jobId: string): Promise<{
    job_id: string;
    status: string;
    progress: number;
    current_step: string | null;
    document_id: string | null;
    candidate_id: string | null;
    missing_fields: string[] | null;
    error_message: string | null;
    sections_count: number;
    embeddings_count: number;
    merge_proposal: any | null;
    requires_approval: boolean;
    created_at: string | null;
    completed_at: string | null;
  }> {
    return this.request(`/async/upload-status/${jobId}`);
  }

  async completeUpload(data: {
    job_id: string;
    manual_name?: string;
    manual_email?: string;
    manual_phone?: string;
  }): Promise<{
    success: boolean;
    candidate_id?: string;
    document_id?: string;
    missing_fields?: string[];
    requires_approval?: boolean;
    merge_proposal?: any;
    message: string;
  }> {
    return this.request('/async/complete-upload', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // User management
  async listUsers(): Promise<UserListItem[]> {
    return this.request<UserListItem[]>('/users/');
  }

  async createUser(data: {
    auth0_sub: string;
    email: string;
    role?: 'superuser' | 'project_manager' | 'candidate';
    candidate_id?: string | null;
    name?: string;
  }): Promise<UserListItem> {
    return this.request<UserListItem>('/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUser(
    userId: string,
    data: {
      role?: 'superuser' | 'project_manager' | 'candidate';
      candidate_id?: string | null;
      name?: string;
    }
  ): Promise<UserListItem> {
    return this.request<UserListItem>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUser(userId: string): Promise<{ deleted: boolean; id: string }> {
    return this.request<{ deleted: boolean; id: string }>(`/users/${userId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new APIClient(API_BASE_URL);
