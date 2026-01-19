import {
  SearchRequest,
  SearchResponse,
  CandidateDetail,
  AvailabilityRecord,
  CandidateListResponse,
  CandidateFullDetail,
  CandidateUpdate,
} from './types';
import { API_BASE_URL } from './config';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
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
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
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
    location?: string;
    updated_at: string;
  }> {
    return this.request(`/candidates/${candidateId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new APIClient(API_BASE_URL);
