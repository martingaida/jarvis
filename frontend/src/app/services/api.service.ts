import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../environments/environment';
import sampleTranscript from './sample_transcript.json';
import { Injectable } from '@angular/core';
import { delay } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;
  private s3Upload = environment.s3Upload;
  private s3Transcript = environment.s3Transcript;

  constructor(private http: HttpClient) {}

  transcribeSample(): Observable<any> {
    return of(sampleTranscript).pipe();
  }

  uploadFile(file: File): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': file.type
    });

    const uploadUrl = `https://${this.s3Upload}.s3.us-east-1.amazonaws.com/${file.name}`;
    return this.http.put(uploadUrl, file, { headers });
  }

  checkTranscriptionStatus(fileName: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });

    return this.http
      .get(`${this.apiUrl}?fileName=${encodeURIComponent(fileName)}`, { headers })
      .pipe(
        map((response: any) => {
          if (response) {
            if (typeof response === 'string') {
              const parsedResponse = JSON.parse(response);
              return parsedResponse.result;
            } else if (typeof response === 'object') {
              return response.result;
            }
          } else if (response.body) {
            return response.body.result;
          }
          console.log(response);
          throw new Error('Invalid response format');
        })
      );
  }

  getTranscript(fileName: string): Observable<any> {
    const transcriptUrl = `https://${this.s3Transcript}.s3.us-east-1.amazonaws.com/${fileName}`;
    return this.http.get(transcriptUrl);
  }
}