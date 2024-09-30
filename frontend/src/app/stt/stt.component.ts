import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { trigger, transition, style, animate } from '@angular/animations';
import { environment } from '../../environments/environment';
import { CommonModule } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-stt',
  standalone: true,
  imports: [CommonModule, FormsModule, MatProgressBarModule, MatButtonToggleModule],
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
  response: any;
  videoUrl: SafeResourceUrl;
  isFileValid = false;

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
      } else {
        this.form.get('audioFile')?.setValue(null);
        this.isFileValid = false;
        alert('Invalid file. Please upload an audio file no larger than 10MB.');
      }
    }
  }

  transcribe() {
    this.isLoading = true;
    if (this.mode === 'Sample') {
      this.apiService.transcribeSample().subscribe(
        (res) => {
          this.response = res;
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
            this.response = res;
            this.isLoading = false;
          },
          (err) => {
            console.error(err);
            this.isLoading = false;
          }
        );
      } else {
        this.isLoading = false;
      }
    }
  }

  private extractVideoId(url: string): string {
    const videoIdMatch = url.match(/(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&]+)/);
    return videoIdMatch ? videoIdMatch[1] : '';
  }
}