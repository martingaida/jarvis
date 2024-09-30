import { ComponentFixture, TestBed } from '@angular/core/testing';

import { STTComponent } from './stt.component';

describe('STTComponent', () => {
  let component: STTComponent;
  let fixture: ComponentFixture<STTComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [STTComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(STTComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
