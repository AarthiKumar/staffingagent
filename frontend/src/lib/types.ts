export interface SearchFilters {
  required_skills?: string[];
  required_certs?: string[];
  min_years?: Record<string, number>;
  location?: string;
  availability_from?: string;
  capacity_pct_min?: number;
}

export interface SearchRequest {
  agent_id: string;
  filters: SearchFilters;
  text?: string;
  use_llm_rerank?: boolean;
  top_k?: number;
}

export interface AvailabilityInfo {
  from_date: string;
  capacity_pct: number;
}

export interface WhySnippet {
  section: string;
  text: string;
  start: number;
  end: number;
}

export interface WhyInfo {
  skills: string[];
  certs: string[];
  snippets: WhySnippet[];
}

export interface SearchResult {
  candidate_id: string;
  name: string;
  updated: string;
  availability?: AvailabilityInfo;
  score: number;
  why: WhyInfo;
}

export interface SearchResponse {
  query_id: string;
  flags: {
    reranked: boolean;
  };
  results: SearchResult[];
}

export interface CandidateDetail {
  candidate_id: string;
  name: string;
  email?: string;
  location?: string;
  updated: string;
  top_skills: string[];
  certifications: string[];
  availability: Array<{
    from: string;
    capacity_pct: number;
    notes?: string;
  }>;
  sections: Array<{
    type: string;
    text: string;
  }>;
}

export interface AvailabilityRecord {
  id: string;
  candidate_id: string;
  candidate_name: string;
  available_from: string;
  capacity_pct: number;
  notes?: string;
}

export interface CandidateListItem {
  id: string;
  name: string;
  email?: string;
  location?: string;
  updated_at: string;
  document_filename?: string;
  embeddings_count: number;
  availability_from?: string;
  capacity_pct?: number;
}

export interface CandidateListResponse {
  total: number;
  page: number;
  page_size: number;
  candidates: CandidateListItem[];
}

export interface SectionDetail {
  id: string;
  type: string;
  text: string;
}

export interface AvailabilityDetail {
  id: string;
  available_from: string;
  capacity_pct: number;
  notes?: string;
  updated_at: string;
}

export interface CandidateFullDetail {
  id: string;
  name: string;
  email?: string;
  location?: string;
  updated_at: string;
  document_id: string;
  document_filename?: string;
  document_mime_type?: string;
  embeddings_count: number;
  availability: AvailabilityDetail[];
  sections: SectionDetail[];
}

export interface CandidateUpdate {
  name?: string;
  email?: string;
  location?: string;
}

// Auth0 Types
export enum UserRole {
  SUPERUSER = 'superuser',
  PROJECT_MANAGER = 'project_manager',
  STAFF = 'staff',
}

export interface User {
  sub: string;
  email: string;
  name?: string;
  roles: string[];
}

export interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: () => void;
  logout: () => void;
  getAccessToken: () => Promise<string>;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (...roles: UserRole[]) => boolean;
}
