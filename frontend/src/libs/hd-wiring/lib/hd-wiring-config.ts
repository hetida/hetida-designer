import { InjectionToken } from '@angular/core';

export enum WiringTheme {
  darkTheme = 'dark-theme',
  LightTheme = 'light-theme'
}

export interface HdWiringConfig {
  allowOutputWiring?: boolean;
  showDownloadExampleJsonButton?: boolean;
  showUploadJsonButton?: boolean;
  allowManualWiring?: boolean;
  monacoEditorTheme?: WiringTheme;
  showDialogHeader?: boolean;
  confirmationButtonText?: string;
  enableDateRangeSelectionOnSeriesTypes?: boolean;
}

export const HD_WIRING_CONFIG = new InjectionToken<HdWiringConfig>(
  'AdapterListUrl',
  {
    factory: () => ({})
  }
);
