import {
  SearchRequest,
  SearchResponse,
  CandidateDetail,
  AvailabilityRecord,
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
}

export const apiClient = new APIClient(API_BASE_URL);
