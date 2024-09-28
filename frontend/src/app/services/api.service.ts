import { Injectable, Inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Layer {
  what: string;
  why: string;
  how: string;
}

export interface Concept {
  concept: string;
  layers: Layer[];
}

export interface Topic {
  topic: string;
  concepts: Concept[];
}

export interface ExplanationResponse {
  explanations: {
    topics: Topic[];
    main_takeaway: string;
  };
}

export interface ArXivPaper {
  id: string;
  title: string;
  abstract: string;
  category: string;
  authors: string;
  published: string;
  abstract_url: string;
  pdf_url: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  constructor(
    private http: HttpClient,
    @Inject('API_URL') private apiUrl: string
  ) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  getArXivPapers(): Observable<ArXivPaper[]> {
    const body = { action: 'arxiv' };  // Set the action in the body

    console.log('Requesting URL:', this.apiUrl, 'with body:', body);
    
    return this.http.post<ArXivPaper[]>(
      this.apiUrl,
      body,  // Pass the action in the request body
      { 
        headers: this.getHeaders(),  // Set headers (if needed)
      }
    );
  }

  explainText(text: string): Observable<ExplanationResponse> {
    const body = { action: 'explain', text };  // Include both action and text in the body

    console.log('Requesting URL:', this.apiUrl, 'with body:', body);
    
    return this.http.post<ExplanationResponse>(
      this.apiUrl,
      body,  // Send action and text in the body
      { 
        headers: this.getHeaders(),  // Set headers (if needed)
      }
    );
  }
}