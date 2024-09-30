import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

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
  private apiUrl = this.getApiUrl();

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  private getApiUrl(): string {
    return environment.apiUrl || '';
  }

  transcribeSample(): Observable<any> {
    const body = { action: 'sample-transcribe' };

    console.log('Requesting URL:', this.apiUrl, 'with body:', body);

    return this.http.post<any>(
      this.apiUrl,
      body,
      {
        headers: this.getHeaders(),
      }
    );
  }

  uploadAndTranscribe(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    console.log('Uploading file to URL:', this.apiUrl);

    return this.http.post<any>(
      `${this.apiUrl}/upload-transcribe`,
      formData
    );
  }
}