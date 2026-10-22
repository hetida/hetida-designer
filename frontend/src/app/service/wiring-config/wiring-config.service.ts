import { Injectable } from '@angular/core';
import { HdWiringConfig, WiringTheme } from 'hd-wiring/lib/hd-wiring-config';
import { ThemeService } from '../theme/theme.service';

@Injectable({ providedIn: 'root' })
export class WiringConfigService implements HdWiringConfig {
  // Implement all HdWiringConfig properties
  allowOutputWiring = true;
  showDownloadExampleJsonButton = true;
  showUploadJsonButton = true;
  allowManualWiring = true;
  monacoEditorTheme: WiringTheme = WiringTheme.LightTheme;
  showDialogHeader = true;
  confirmationButtonText = 'Execute';
  enableDateRangeSelectionOnSeriesTypes = true;

  constructor(private readonly themeService: ThemeService) {
    this.themeService.currentTheme.subscribe(currentTheme => {
      this.monacoEditorTheme = currentTheme as WiringTheme;
    });
  }

  resetToDefaults(): void {
    this.confirmationButtonText = 'Execute';
    this.showDialogHeader = true;
  }
}
