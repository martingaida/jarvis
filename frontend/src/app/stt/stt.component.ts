import { Component, ViewChild, ElementRef, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormBuilder, FormGroup } from '@angular/forms';
import { trigger, transition, style, animate } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';

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

  constructor(private http: HttpClient, private fb: FormBuilder) {
    this.form = this.fb.group({
      audioFile: [null],
    });
  }

  ngOnInit() {}

  switchMode(mode: 'Sample' | 'Upload') {
    this.mode = mode;
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.form.get('audioFile')?.setValue(input.files[0]);
    }
  }

  transcribe() {
    this.isLoading = true;
    if (this.mode === 'Sample') {
      this.http.get('/api/sample-transcribe').subscribe(
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
      const formData = new FormData();
      const audioFile = this.form.get('audioFile')?.value;
      if (audioFile) {
        formData.append('file', audioFile);
        this.http.post('/api/upload-transcribe', formData).subscribe(
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
        // Handle the case where audioFile is null
      }
    }
  }
}
