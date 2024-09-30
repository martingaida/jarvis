import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-entities',
  standalone: true,
  imports: [CommonModule, MatChipsModule],
  templateUrl: './entities.component.html',
  styleUrls: ['./entities.component.scss']
})
export class EntitiesComponent {
  @Input() set entities(value: any) {
    if (value) {
      this.entityList = Object.entries(value)
        .filter(([key, values]) => 
          !['CASE_NUMBER', 'DATE'].includes(key) && 
          Array.isArray(values) && 
          values.length > 0
        )
        .map(([key, values]) => ({
          key: this.getPluralizedKey(key, (values as string[]).length),
          values: key === 'LOCATION' ? this.convertWordNumbersToDigits(values as string[]) : values as string[],
          color: this.getEntityColor(key)
        }));
    } else {
      this.entityList = [];
    }
  }

  entityList: any[] = [];

  private entityColors: { [key: string]: string } = {
    'ATTORNEY': 'hsla(0, 100%, 80%, 0.6)',    // Light Red
    'EXHIBIT': 'hsla(120, 70%, 80%, 0.6)',    // Light Green
    'COMPANY': 'hsla(210, 100%, 80%, 0.6)',   // Light Blue
    'JUDGE': 'hsla(50, 100%, 80%, 0.6)',      // Light Yellow
    'WITNESS': 'hsla(180, 70%, 80%, 0.6)',    // Light Cyan
    'EXPERT': 'hsla(300, 70%, 80%, 0.6)',     // Light Magenta
    'DEFENDANT': 'hsla(30, 100%, 80%, 0.6)',  // Light Orange
    'COURT': 'hsla(270, 70%, 80%, 0.6)',      // Light Purple
    'LOCATION': 'hsla(150, 70%, 80%, 0.6)',   // Light Teal
    'STATUTE': 'hsla(90, 70%, 80%, 0.6)',     // Light Lime
    'PLAINTIFF': 'hsla(240, 70%, 80%, 0.6)',  // Light Indigo
    'LEGAL_TERM': 'hsla(330, 70%, 80%, 0.6)'  // Light Pink
  };

  getEntityColor(entityType: string): string {
    return this.entityColors[entityType] || 'hsla(0, 0%, 90%, 0.6)'; // Light Gray for unknown types
  }

  private convertWordNumbersToDigits(locations: string[]): string[] {
    const wordToNumber: { [key: string]: string } = {
      'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
      'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
      'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
      'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20',
      'twenty-one': '21', 'twenty-two': '22', 'twenty-three': '23', 'twenty-four': '24', 'twenty-five': '25',
      'twenty-six': '26', 'twenty-seven': '27', 'twenty-eight': '28', 'twenty-nine': '29', 'thirty': '30',
      'thirty-one': '31', 'thirty-two': '32', 'thirty-three': '33', 'thirty-four': '34', 'thirty-five': '35',
      'thirty-six': '36', 'thirty-seven': '37', 'thirty-eight': '38', 'thirty-nine': '39', 'forty': '40',
      'forty-one': '41', 'forty-two': '42', 'forty-three': '43', 'forty-four': '44', 'forty-five': '45',
      'forty-six': '46', 'forty-seven': '47', 'forty-eight': '48', 'forty-nine': '49', 'fifty': '50'
    };

    return locations.map(location => {
      const words = location.split(' ');
      const convertedWords = words.map(word => {
        const lowerWord = word.toLowerCase();
        return wordToNumber[lowerWord] || word;
      });
      return convertedWords.join(' ');
    });
  }

  private getPluralizedKey(key: string, count: number): string {
    const pluralizeMap: { [key: string]: string } = {
      'ATTORNEY': 'ATTORNEYS',
      'PLAINTIFF': 'PLAINTIFFS',
      'DEFENDANT': 'DEFENDANTS',
      'WITNESS': 'WITNESSES',
      'COMPANY': 'COMPANIES',
      'LEGAL_TERM': 'TERMS'
    };

    if (count > 1 && key in pluralizeMap) {
      return pluralizeMap[key];
    }

    return key === 'LEGAL_TERM' ? 'TERM' : key;
  }
}