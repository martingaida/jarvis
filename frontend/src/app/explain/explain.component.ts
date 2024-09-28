import { ApiService, Topic, Concept, Layer, ArXivPaper } from '../services/api.service';
import { trigger, transition, style, animate } from '@angular/animations';
import { Component, ViewChild, ElementRef, OnInit } from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatExpansionModule } from '@angular/material/expansion';
import { ExplanationResponse } from '../services/api.service';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-explain',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    MatProgressBarModule, 
    MatCardModule, 
    MatExpansionModule, 
    MatTabsModule, 
    MatTooltipModule, 
    MatIconModule,
    MatButtonToggleModule,
    MatButtonModule
  ],
  templateUrl: './explain.component.html',
  styleUrls: ['./explain.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})

export class ExplainComponent implements OnInit {
  inputText = '';
  explanations: Topic[] = [];
  mainTakeaway: string = '';
  totalTime: number = 0;
  isLoading = false;
  isExplanationVisible = false;
  mode: 'arXiv' | 'Custom' = 'arXiv';
  arXivPapers: ArXivPaper[] = [];
  isLoadingArXiv = false;
  explainedPapers: { [id: string]: ExplanationResponse } = {};
  maxRetries = 3;
  currentPaperTitle: string | null = null;
  currentPaperPdfUrl: string | null = null;

  constructor(private apiService: ApiService) {}

  @ViewChild('explanationContainer') private explanationContainer!: ElementRef;

  ngOnInit() {
    this.loadArXivPapers();
  }

  loadArXivPapers() {
    if (this.arXivPapers.length > 0) return;

    this.isLoadingArXiv = true;
    this.fetchArXivPapers(this.maxRetries);
  }

  fetchArXivPapers(retriesLeft: number) {
    this.apiService.getArXivPapers().subscribe(
      (papers) => {
        this.arXivPapers = papers;
        this.isLoadingArXiv = false;
      },
      (error) => {
        console.error('Error fetching arXiv papers:', error);
        if (retriesLeft > 0) {
          setTimeout(() => this.fetchArXivPapers(retriesLeft - 1), 2000);
        } else {
          this.isLoadingArXiv = false;
        }
      }
    );
  }

  get isExplainDisabled(): boolean {
    return this.isLoading || this.isLoadingArXiv || (!this.inputText.trim() && this.mode === 'Custom');
  }

  explainText() {
    this.currentPaperTitle = null;
    if (this.isExplainDisabled) return;

    this.isLoading = true;
    this.isExplanationVisible = false;
    console.log('Explaining text:', this.inputText);
    this.apiService.explainText(this.inputText).subscribe(
      (response) => {
        console.log('Received response:', response);
        this.explanations = response.explanations.topics;
        this.mainTakeaway = response.explanations.main_takeaway;
        this.isLoading = false;
        setTimeout(() => {
          this.isExplanationVisible = true;
          this.scrollToExplanation();
        }, 100);
      },
      (error) => {
        console.error('Error:', error);
        this.isLoading = false;
      }
    );
  }

  private scrollToExplanation() {
    if (this.explanationContainer) {
      this.explanationContainer.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  explainArXiv(paper: ArXivPaper) {
    this.currentPaperTitle = paper.title;
    this.currentPaperPdfUrl = paper.pdf_url;
    if (this.explainedPapers[paper.id]) {
      // Paper has already been explained, retrieve from storage
      const savedExplanation = this.explainedPapers[paper.id];
      this.explanations = savedExplanation.explanations.topics;
      this.mainTakeaway = savedExplanation.explanations.main_takeaway;
      this.isExplanationVisible = true;
      this.scrollToExplanation();
    } else {
      this.inputText = `${paper.title}\n\n${paper.abstract}`;
      this.isLoading = true;
      this.isExplanationVisible = false;
      this.apiService.explainText(this.inputText).subscribe(
        (response) => {
          console.log('Received response:', response);
          this.explanations = response.explanations.topics;
          this.mainTakeaway = response.explanations.main_takeaway;
          this.explainedPapers[paper.id] = response; // Save the explanation
          this.isLoading = false;
          setTimeout(() => {
            this.isExplanationVisible = true;
            this.scrollToExplanation();
          }, 100);
        },
        (error) => {
          console.error('Error:', error);
          this.isLoading = false;
        }
      );
    }
  }

  isPaperExplained(paperId: string): boolean {
    return !!this.explainedPapers[paperId];
  }
}