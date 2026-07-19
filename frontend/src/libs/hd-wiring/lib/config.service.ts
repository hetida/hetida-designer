import { Injectable, Injector } from '@angular/core';
import {
  HdWiringConfig,
  HD_WIRING_CONFIG,
  WiringTheme
} from './hd-wiring-config';

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  readonly DEFAULT_CONFIG: HdWiringConfig = {
    allowManualWiring: true,
    allowOutputWiring: true,
    showUploadJsonButton: true,
    showDownloadExampleJsonButton: true,
    monacoEditorTheme: WiringTheme.LightTheme,
    showDialogHeader: true,
    confirmationButtonText: 'Execute',
    enableDateRangeSelectionOnSeriesTypes: false
  };

  constructor(private readonly injector: Injector) {}

  get app_config(): HdWiringConfig {
    const wiringConfig: HdWiringConfig = this.injector.get(HD_WIRING_CONFIG);
    return {
      ...this.DEFAULT_CONFIG,
      ...wiringConfig
    };
  }
}
