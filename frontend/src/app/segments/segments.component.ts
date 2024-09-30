import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDividerModule } from '@angular/material/divider';

@Component({
  selector: 'app-segments',
  standalone: true,
  imports: [CommonModule, MatDividerModule],
  templateUrl: './segments.component.html',
  styleUrls: ['./segments.component.scss']
})
export class SegmentsComponent {
  @Input() segments: any[] = [];

  formatTimestamp(timestamp: string): string {
    const seconds = parseFloat(timestamp);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `[${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}]`;
  }
}