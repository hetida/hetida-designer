import { CommonModule } from '@angular/common';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { OwlDateTimeModule } from '@danielmoncada/angular-datetime-picker';
import {
  OWL_MOMENT_DATE_TIME_ADAPTER_OPTIONS,
  OwlMomentDateTimeModule
} from '@danielmoncada/angular-datetime-picker-moment-adapter';
import { HighlightTextPipe } from './highlight-text-pipe/highlight-text.pipe';
import { JsonEditorComponent } from './json-editor/json-editor.component';
import { MaterialModule } from './material.module';
import { MetaDataWiringModalComponent } from './meta-data-wiring-modal/meta-data-wiring-modal.component';
import { NodeSearchComponent } from './node-search/node-search.component';
import { NodeWiringContextMenuComponent } from './node-wiring-context-menu/node-wiring-context-menu.component';
import { TreeNodeModalComponent } from './tree-node-modal/tree-node-modal.component';
import { TreeNodeComponent } from './tree-node/tree-node.component';
import { WarningDialogComponent } from './warning-dialog/warning-dialog.component';
import { WiringDialogComponent } from './wiring-dialog/wiring-dialog.component';

@NgModule({
  declarations: [
    WiringDialogComponent,
    NodeWiringContextMenuComponent,
    JsonEditorComponent,
    MetaDataWiringModalComponent,
    NodeSearchComponent,
    TreeNodeComponent,
    TreeNodeModalComponent,
    WarningDialogComponent,
    HighlightTextPipe
  ],
  exports: [WiringDialogComponent, JsonEditorComponent],
  imports: [
    CommonModule,
    MaterialModule,
    ReactiveFormsModule,
    FormsModule,
    OwlDateTimeModule,
    OwlMomentDateTimeModule,
    NoopAnimationsModule
  ],
  providers: [
    {
      provide: OWL_MOMENT_DATE_TIME_ADAPTER_OPTIONS,
      useValue: { useUtc: true }
    },
    provideHttpClient(withInterceptorsFromDi())
  ]
})
export class HdWiringModule {}
