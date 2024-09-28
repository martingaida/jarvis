import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { provideStore } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { ApiService } from './services/api.service';
import { environment } from '../environments/environment';
import { provideAnimations } from '@angular/platform-browser/animations';
import { MatProgressBarModule } from '@angular/material/progress-bar';


export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideClientHydration(),
    provideHttpClient(),
    provideStore(),
    provideEffects(),
    provideAnimations(),
    MatProgressBarModule,
    provideStoreDevtools({ maxAge: 25 }),
    { provide: 'API_URL', useValue: environment.apiUrl },
    ApiService
  ]
};