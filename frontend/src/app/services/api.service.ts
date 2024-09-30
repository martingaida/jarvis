import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient) {}

  transcribeSample(): Observable<any> {
    return new Observable(observer => {
      setTimeout(() => {
        observer.next(this.mockTranscriptResponse);
        observer.complete();
      }, 2000);
    });
  }

  uploadAudio(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(`${this.apiUrl}/upload`, formData);
  }

  private async sendFileToLambda(file: File): Promise<any> {
    const arrayBuffer = await file.arrayBuffer();
    const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

    const payload = {
      filename: file.name,
      contentType: file.type,
      content: base64
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post(this.lambdaUrl!, payload, { headers }).toPromise();
  }

  checkTranscriptionStatus(fileName: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/status/${fileName}`);
  }
}