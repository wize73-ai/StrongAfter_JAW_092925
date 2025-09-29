import { Component, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { TextProcessorComponent } from './components/text-processor/text-processor.component';
import { ApiService } from './services/api.service';
import { DeveloperModeService } from './services/developer-mode.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterOutlet, TextProcessorComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'StrongAfter';
  healthStatus = 'checking...';
  developerMode = false;
  isDarkMode = true; // Default to dark mode

  constructor(
    private apiService: ApiService,
    private developerModeService: DeveloperModeService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  ngOnInit() {
    this.checkHealth();
    this.developerModeService.setDeveloperMode(this.developerMode);
    if (isPlatformBrowser(this.platformId)) {
      this.setTheme(this.isDarkMode);
    }
  }

  checkHealth() {
    this.apiService.checkHealth().subscribe({
      next: (response) => {
        this.healthStatus = response.status;
      },
      error: (error) => {
        console.error('Health check failed:', error);
        this.healthStatus = 'error';
      }
    });
  }

  onDeveloperModeChange() {
    this.developerModeService.setDeveloperMode(this.developerMode);
  }

  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    if (isPlatformBrowser(this.platformId)) {
      this.setTheme(this.isDarkMode);
    }
  }

  private setTheme(isDark: boolean) {
    if (isPlatformBrowser(this.platformId)) {
      document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    }
  }
}
