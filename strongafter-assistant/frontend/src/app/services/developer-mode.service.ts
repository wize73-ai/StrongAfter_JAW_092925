import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DeveloperModeService {
  private developerModeSubject = new BehaviorSubject<boolean>(false);
  
  get isDeveloperMode$(): Observable<boolean> {
    return this.developerModeSubject.asObservable();
  }
  
  get isDeveloperMode(): boolean {
    return this.developerModeSubject.value;
  }
  
  setDeveloperMode(isEnabled: boolean): void {
    this.developerModeSubject.next(isEnabled);
  }
} 