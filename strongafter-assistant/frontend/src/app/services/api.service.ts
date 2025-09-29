import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, timeout } from 'rxjs';
import { environment } from '../../environments/environment';

interface HealthResponse {
  status: string;
  message: string;
}

interface Theme {
  id: string;
  label: string;
  description: string;
  type: string;
  related_parent_label: string | null;
  related_parent_id: string | null;
  analysis?: string;
  score: number;
  is_relevant: boolean;
  excerpt_summary?: string;
  excerpts?: {
    excerpt: {
      text: string;
      headers: string[];
      book_url: string;
      title: string;
    };
    similarity_score: number;
  }[];
}

interface BookMetadata {
  author: string;
  year: string;
  title: string;
  publisher: string;
  url: string;
  purchase_url: string;
}

interface TextProcessResponse {
  original: string;
  themes: Theme[];
  summary: string;
  processing_time: number;
  quality_score?: number;
  book_metadata: { [key: string]: BookMetadata };
}

interface ParsedBookResponse {
  filename: string;
  parsed: any;
}

interface SearchResult {
  excerpt: {
    text: string;
    title: string;
    headers: string[];
    book_url: string;
  };
  similarity: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  checkHealth(): Observable<HealthResponse> {
    console.log('Checking health...');
    return this.http.get<HealthResponse>(`${this.apiUrl}/health`).pipe(
      tap(response => console.log('Health check response:', response))
    );
  }

  processText(text: string): Observable<TextProcessResponse> {
    console.log('Processing text:', text);
    return this.http.post<TextProcessResponse>(`${this.apiUrl}/process-text`, { text }).pipe(
      timeout(120000), // 120 second timeout
      tap({
        next: response => console.log('Process text response:', response),
        error: error => console.error('Process text error:', error)
      })
    );
  }

  getParsedBook(): Observable<ParsedBookResponse> {
    return this.http.get<ParsedBookResponse>(`${this.apiUrl}/parsed-book`);
  }

  semanticSearch(query: string): Observable<SearchResult[]> {
    return this.http.post<SearchResult[]>(`${this.apiUrl}/semantic-search`, { query });
  }
}
