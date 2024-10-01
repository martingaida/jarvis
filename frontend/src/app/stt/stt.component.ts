import { Component, ViewChild, ElementRef, OnInit, OnDestroy } from '@angular/core';
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
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

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
export class SttComponent implements OnInit, OnDestroy {
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
  transcriptionStatus: string = '';
  errorMessage: string = '';
  statusCheckSubscription: Subscription | undefined;
  buttonText: string = 'Initializing...';
  messages = [
    "Initializing...",
    "Processing audio...",
    "Analyzing speech patterns...",
    "Identifying speakers...",
    "Applying language models...",
    "Refining transcription...",
    "Finalizing results..."
  ];

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
      this.buttonText = 'Transcribe';

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
    this.errorMessage = '';

    if (this.mode === 'Sample') {
      // Iterate over the messages and wait for it to finish before rendering the transcript
      this.iterateWithDelay(this.messages, 5000)
        .then(() => {
          // Once the messages have finished, fetch and display the sample transcript
          this.apiService.transcribeSample().subscribe(
            (res) => {
              this.sampleResponse = res;
              this.updateDisplayedResponse();
              this.isLoading = false;
              this.buttonText = "Done!";
            },
            (err) => {
              console.error('Error loading sample transcription:', err);
              this.isLoading = false;
              this.buttonText = "Error";
              alert('Error loading sample transcription. Please try again.');
            }
          );
        })
        .catch((error) => {
          console.error('Error in iterateWithDelay:', error);
          this.buttonText = "Error";
          this.isLoading = false;
        });
    } else {
      // For Upload mode
      const audioFile = this.form.get('audioFile')?.value;
      if (audioFile) {
        this.apiService.uploadFile(audioFile).subscribe(
          () => {
            this.checkTranscriptionStatus(audioFile.name);
          },
          (err) => {
            console.error('Error uploading file:', err);
            this.isLoading = false;
            alert('Error uploading file. Please try again.');
          }
        );
      } else {
        this.isLoading = false;
        alert('Please select a file to upload.');
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

  private async iterateWithDelay(messages: string[], delayInMs: number) {
    for (const message of messages) {
      this.buttonText = message;
      await new Promise(resolve => setTimeout(resolve, delayInMs)); // Wait for X ms before moving to the next item
    }
  }

  async checkTranscriptionStatus(fileName: string) {
    this.isLoading = true;
    this.errorMessage = '';
    fileName = fileName.split('.').slice(0, -1).join('.');  // Remove the extension
  
    let attempts = 0;
    const maxAttempts = 60;  // 30 minutes maximum (30 seconds * 60)
    let messageIndex = 0;  // Keep track of the current message
  
    // Function to cycle through the messages
    const updateMessage = () => {
      this.buttonText = this.messages[Math.min(messageIndex, this.messages.length - 1)];
      messageIndex++; // Increment the message index
    };
  
    // Set the initial message and then cycle through the messages every 5 seconds
    updateMessage();
    const messageInterval = setInterval(() => {
      updateMessage();
    }, 5000);
  
    // Polling function
    const checkStatus = () => {
      this.apiService.checkTranscriptionStatus(fileName).subscribe(
        (response) => {

          if (Object.keys(response).length > 0) {
            this.uploadResponse = response;
            this.updateDisplayedResponse();
            this.buttonText = "Done!";
            this.isLoading = false;
            clearInterval(messageInterval); // Stop changing messages
            return;
          } else if (attempts >= maxAttempts) {
            this.errorMessage = 'Transcription timed out';
            this.buttonText = "Timed Out";
            this.isLoading = false;
            clearInterval(messageInterval); // Stop changing messages
            return;
          }
  
          // Increment attempt count and schedule the next status check
          attempts++;
          if (this.isLoading) {
            setTimeout(checkStatus, 15000); // Poll again in 15 seconds
          }
        },
        (error) => {
          console.error('Error checking transcription status:', error);
          this.errorMessage = 'Error checking transcription status';
          this.buttonText = "Error";
          this.isLoading = false;
          clearInterval(messageInterval); // Stop changing messages
        }
      );
    };
  
    checkStatus(); // Start the first status check
  }
  

  ngOnDestroy() {
    if (this.statusCheckSubscription) {
      this.statusCheckSubscription.unsubscribe();
    }
  }
}