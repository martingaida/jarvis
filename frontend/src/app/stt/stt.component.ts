import { Component, ViewChild, ElementRef, OnInit } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { EntitiesComponent } from '../entities/entities.component';
import { SegmentsComponent } from '../segments/segments.component';
import { environment } from '../../environments/environment';
import { FormBuilder, FormGroup } from '@angular/forms';
import { InfoComponent } from '../info/info.component';
import { ApiService } from '../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-stt',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    MatProgressBarModule, 
    MatButtonToggleModule, 
    InfoComponent, 
    EntitiesComponent,
    SegmentsComponent
  ],
  templateUrl: './stt.component.html',
  styleUrls: ['./stt.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class SttComponent implements OnInit {
  mode: 'Sample' | 'Upload' = 'Sample';
  form: FormGroup;
  isLoading = false;
  sampleResponse: any;
  uploadResponse: any;
  videoUrl: SafeResourceUrl;
  isFileValid = false;
  documentTitle: any;
  entities: any;
  segments: any;
  uploadedFileName: string = '';

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private sanitizer: DomSanitizer
  ) {
    this.form = this.fb.group({
      audioFile: [null],
    });
    const videoId = this.extractVideoId(environment.mockDepositionUrl!);
    const embedUrl = `https://www.youtube.com/embed/${videoId}`;
    this.videoUrl = this.sanitizer.bypassSecurityTrustResourceUrl(embedUrl);
  }

  ngOnInit() {}

  switchMode(mode: 'Sample' | 'Upload') {
    this.mode = mode;
    this.updateDisplayedResponse();
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      const isValidType = file.type.startsWith('audio/');
      const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB

      if (isValidType && isValidSize) {
        this.form.get('audioFile')?.setValue(file);
        this.isFileValid = true;
        this.uploadedFileName = file.name.split('.').slice(0, -1).join('.'); // Remove file extension
      } else {
        this.form.get('audioFile')?.setValue(null);
        this.isFileValid = false;
        this.uploadedFileName = '';
        alert('Invalid file. Please upload an audio file no larger than 10MB.');
      }
    }
  }

  transcribe() {
    this.isLoading = true;
    if (this.mode === 'Sample') {
      this.apiService.transcribeSample().subscribe(
        (res) => {
          this.sampleResponse = res;
          this.updateDisplayedResponse();
          this.isLoading = false;
        },
        (err) => {
          console.error(err);
          this.isLoading = false;
        }
      );
    } else {
      const audioFile = this.form.get('audioFile')?.value;
      if (audioFile) {
        this.apiService.uploadAndTranscribe(audioFile).subscribe(
          (res) => {
            this.uploadResponse = res;
            this.updateDisplayedResponse();
            this.isLoading = false;
          },
          (err) => {
            console.error('Error uploading and transcribing:', err);
            this.isLoading = false;
          }
        );
      } else {
        this.isLoading = false;
      }
    }
  }

  updateDisplayedResponse() {
    const response = this.mode === 'Sample' ? this.sampleResponse : this.uploadResponse;
    if (response) {
      this.processResponse(response);
    } else {
      this.clearDisplayedResponse();
    }
  }

  processResponse(response: any) {
    this.documentTitle = {
      caseNumber: response.entities.CASE_NUMBER[0],
      date: response.entities.DATE[0],
      plaintiffs: response.entities.PLAINTIFF,
      defendants: response.entities.DEFENDANT
    };
    this.entities = response.entities;
    this.segments = response.segments;
  }

  clearDisplayedResponse() {
    this.documentTitle = null;
    this.entities = null;
    this.segments = null;
  }

  private extractVideoId(url: string): string {
    const videoIdMatch = url.match(/(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&]+)/);
    return videoIdMatch ? videoIdMatch[1] : '';
  }
}