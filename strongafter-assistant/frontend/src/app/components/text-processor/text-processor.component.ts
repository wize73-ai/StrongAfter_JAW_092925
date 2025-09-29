import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MarkdownModule } from 'ngx-markdown';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import { ApiService } from '../../services/api.service';
import { DeveloperModeService } from '../../services/developer-mode.service';
import { Subscription } from 'rxjs';

interface Excerpt {
  excerpt: {
    text: string;
    headers: string[];
    book_url: string;
    title: string;
  };
  similarity_score: number;
}

interface Theme {
  id: string;
  label: string;
  description: string;
  type: string;
  related_parent_label: string | null;
  related_parent_id: string | null;
  analysis?: string;
  score: number;
  is_relevant: boolean;
  excerpts?: Excerpt[];
  excerpt_summary?: string;
}

@Component({
  selector: 'app-text-processor',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownModule],
  templateUrl: './text-processor.component.html',
  styleUrl: './text-processor.component.scss'
})
export class TextProcessorComponent implements OnInit, OnDestroy {
  inputText: string = '';
  themes: Theme[] = [];
  summary: string = '';
  bookMetadata: { [key: string]: any } = {};
  isProcessing: boolean = false;
  error: string | null = null;
  isDeveloperMode: boolean = false;
  private subscription: Subscription | null = null;
  clickedThemeIds: Set<string> = new Set();

  constructor(
    private apiService: ApiService,
    private developerModeService: DeveloperModeService,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit() {
    try {
      this.subscription = this.developerModeService.isDeveloperMode$.subscribe(
        isEnabled => this.isDeveloperMode = isEnabled
      );
    } catch (error) {
      console.error('Error subscribing to developer mode:', error);
      // Fallback to false if service fails
      this.isDeveloperMode = false;
    }
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      this.processText();
    }
  }

  processText() {
    if (!this.inputText.trim()) {
      return;
    }

    this.isProcessing = true;
    this.error = null;
    this.themes = [];
    this.summary = '';

    this.apiService.processText(this.inputText).subscribe({
      next: (response) => {
        console.log('=== NEW API RESPONSE ===');
        console.log('Input was:', this.inputText);
        console.log('Summary received:', response.summary?.substring(0, 100));
        console.log('Themes count:', response.themes?.length);
        console.log('Book metadata keys:', Object.keys(response.book_metadata || {}));

        this.themes = response.themes;
        this.summary = response.summary;
        this.bookMetadata = response.book_metadata || {};
        this.isProcessing = false;

        console.log('=== RESPONSE PROCESSED ===');
      },
      error: (error) => {
        console.error('Error processing text:', error);
        this.error = 'Failed to process text. Please try again.';
        this.isProcessing = false;
      }
    });
  }

  toggleTheme(themeId: string) {
    if (this.isDeveloperMode) {
      if (this.clickedThemeIds.has(themeId)) {
        this.clickedThemeIds.delete(themeId);
      } else {
        this.clickedThemeIds.add(themeId);
      }
    }
  }

  isThemeClicked(themeId: string): boolean {
    return this.clickedThemeIds.has(themeId);
  }

  // Helper methods for template
  getRelevantThemes(): Theme[] {
    return this.themes.filter(theme => theme.is_relevant);
  }

  getNonRelevantThemes(): Theme[] {
    return this.themes.filter(theme => !theme.is_relevant);
  }

  // For non-developer mode, get all themes
  getAllThemes(): Theme[] {
    return this.isDeveloperMode 
      ? [] // Not used in developer mode
      : this.themes.filter(theme => theme.is_relevant);
  }

  // Process citations in summary text
  processCitations(summaryText: string, excerpts: Excerpt[]): SafeHtml {
    if (!summaryText || summaryText.trim() === '') {
      return this.sanitizer.bypassSecurityTrustHtml('');
    }

    // If no excerpts, still process the summary text without citations
    if (!excerpts || excerpts.length === 0) {
      try {
        const htmlContent = marked.parse(summaryText) as string;
        return this.sanitizer.bypassSecurityTrustHtml(htmlContent);
      } catch (error) {
        console.error('Error processing markdown:', error);
        return this.sanitizer.bypassSecurityTrustHtml(summaryText);
      }
    }

    let htmlContent = '';

    // 1. Process markdown first to get a base HTML structure
    try {
      htmlContent = marked.parse(summaryText) as string;
    } catch (error) {
      console.error('Error processing markdown:', error);
      htmlContent = summaryText; // Fallback to original text if markdown fails
    }

    // 2. First normalize superscript digits, then replace ⁽number⁾ patterns with clickable links
    // Map of superscript digits to regular digits
    const superscriptMap: { [key: string]: string } = {
      '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
      '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    };

    // Convert superscript digits to regular digits in HTML content
    const normalizedHtml = htmlContent.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (match) => superscriptMap[match] || match);

    // Then replace ⁽number⁾ patterns with clickable superscript links
    const processedHtml = normalizedHtml.replace(/⁽(\d+)⁾/g, (match, number) => {
      const excerptIndex = parseInt(number) - 1;
      if (excerptIndex >= 0 && excerptIndex < excerpts.length) {
        const excerpt = excerpts[excerptIndex];
        const url = excerpt.excerpt.book_url;
        const title = excerpt.excerpt.title || 'Source';
        const text = excerpt.excerpt.text;

        // Create APA-lite style tooltip with source info
        const tooltipText = `${title}\n\n"${text.substring(0, 200)}${text.length > 200 ? '...' : ''}"`;

        if (url) {
          return `<sup><a href="${url}" target="_blank" rel="noopener noreferrer" title="${tooltipText}" class="citation-link">[${number}]</a></sup>`;
        } else {
          return `<sup class="citation-no-link" title="${tooltipText}">[${number}]</sup>`;
        }
      }
      return match; // Return original match if something goes wrong
    });


    return this.sanitizer.bypassSecurityTrustHtml(processedHtml);
  }

  // Extract citation numbers from summary text
  extractCitationNumbers(summaryText: string): number[] {
    // Map of superscript digits to regular digits
    const superscriptMap: { [key: string]: string } = {
      '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
      '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    };

    // Convert superscript digits to regular digits
    const normalizedText = summaryText.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (match) => superscriptMap[match] || match);

    const matches = normalizedText.match(/⁽(\d+)⁾/g);
    if (!matches) return [];

    return matches.map(match => parseInt(match.replace(/[⁽⁾]/g, '')))
      .filter((num, index, arr) => arr.indexOf(num) === index) // Remove duplicates
      .sort((a, b) => a - b); // Sort numerically
  }

  // Get unique resource cards for citations used in summary
  getResourceCards(): Array<{
    title: string,
    author: string,
    description: string,
    primaryCTA: { text: string, url: string },
    secondaryCTA?: { text: string, url: string }, // For future feature
    cardType: string
  }> {
    console.log('=== getResourceCards CALLED ===');
    console.log('Summary exists:', !!this.summary);
    console.log('Summary content:', this.summary?.substring(0, 100));
    console.log('BookMetadata exists:', Object.keys(this.bookMetadata).length > 0);

    if (!this.summary) return [];

    const citationNumbers = this.extractCitationNumbers(this.summary);
    console.log('Citation numbers found:', citationNumbers);

    const allExcerpts = this.getAllExcerpts();
    console.log('All excerpts count:', allExcerpts.length);
    console.log('Book metadata keys:', Object.keys(this.bookMetadata));

    const uniqueResources = new Map();

    for (const num of citationNumbers) {
      const excerptIndex = num - 1;
      if (excerptIndex >= 0 && excerptIndex < allExcerpts.length) {
        const excerpt = allExcerpts[excerptIndex];
        const title = excerpt.excerpt.title || 'Unknown Source';

        // Since all excerpts are from the same book (Men's Road to Healing),
        // just use the first available metadata entry
        let metadata = null;
        const metadataEntries = Object.values(this.bookMetadata);
        if (metadataEntries.length > 0) {
          metadata = metadataEntries[0];
          console.log('Using first available metadata:', metadata);
        }

        if (metadata && !uniqueResources.has(metadata.title)) {
          // Determine primary CTA based on resource type
          let primaryCTA = {
            text: 'Read the Ebook',
            url: metadata.purchase_url || metadata.url
          };

          // Resource description based on excerpt content
          const description = `Insights on ${this.getResourceDescription(excerpt.excerpt.text)}`;

          uniqueResources.set(metadata.title, {
            title: metadata.title,
            author: metadata.author,
            description: description,
            primaryCTA: primaryCTA,
            secondaryCTA: undefined, // For future member benefits
            cardType: 'ebook'
          });
        }
      }
    }

    const result = Array.from(uniqueResources.values());
    console.log('Final resource cards:', result);

    // Fallback: if we have citations but no resource cards, create a default one
    if (result.length === 0 && citationNumbers.length > 0 && Object.keys(this.bookMetadata).length > 0) {
      console.log('Creating fallback resource card');
      const firstMetadata = Object.values(this.bookMetadata)[0];
      result.push({
        title: firstMetadata.title,
        author: firstMetadata.author,
        description: 'Insights on healing and personal growth',
        primaryCTA: {
          text: 'Read the Ebook',
          url: firstMetadata.purchase_url || firstMetadata.url
        },
        cardType: 'ebook'
      });
    }

    console.log('=== getResourceCards Debug End ===');
    return result;
  }

  // Helper method to create resource descriptions
  private getResourceDescription(excerptText: string): string {
    // Extract key themes from excerpt for description
    if (excerptText.toLowerCase().includes('trauma')) return 'trauma recovery and healing';
    if (excerptText.toLowerCase().includes('emotion')) return 'emotional regulation and expression';
    if (excerptText.toLowerCase().includes('masculin')) return 'masculinity and emotional wellbeing';
    if (excerptText.toLowerCase().includes('relationship')) return 'relationships and intimacy';
    if (excerptText.toLowerCase().includes('recover')) return 'recovery strategies and coping';
    return 'healing and personal growth';
  }

  // Get all excerpts from relevant themes for citation processing
  getAllExcerpts(): Excerpt[] {
    const relevantThemes = this.getRelevantThemes();
    const allExcerpts: Excerpt[] = [];
    
    for (const theme of relevantThemes) {
      if (theme.excerpts) {
        allExcerpts.push(...theme.excerpts);
      }
    }
    
    return allExcerpts;
  }
}
