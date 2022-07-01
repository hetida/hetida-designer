import { APP_BASE_HREF } from '@angular/common';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { ErrorHandler, NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  MAT_DIALOG_DATA,
  MAT_DIALOG_DEFAULT_OPTIONS,
  MatDialogRef
} from '@angular/material/dialog';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
import { BrowserModule } from '@angular/platform-browser';
import {
  ANIMATION_MODULE_TYPE,
  BrowserAnimationsModule
} from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import {
  OwlDateTimeModule,
  OwlNativeDateTimeModule
} from '@danielmoncada/angular-datetime-picker';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import {
  AuthModule,
  StsConfigHttpLoader,
  StsConfigLoader
} from 'angular-auth-oidc-client';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
import {
  HD_WIRING_CONFIG,
  HdWiringConfig,
  HdWiringModule,
  WiringTheme
} from 'hd-wiring';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { from } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { AuthGuard } from './auth/auth.guard';
import { AuthInterceptor } from './auth/auth.interceptor';
import { BaseItemContextMenuComponent } from './components/base-item-context-menu/base-item-context-menu.component';
import { ComponentEditorComponent } from './components/component-editor/component-editor.component';
import { ComponentIODialogComponent } from './components/component-io-dialog/component-io-dialog.component';
import { ConfirmDialogComponent } from './components/confirmation-dialog/confirm-dialog.component';
import { ContentViewComponent } from './components/content-view/content-view.component';
import { CopyBaseItemDialogComponent } from './components/copy-base-item-dialog/copy-base-item-dialog.component';
import { DocumentationEditorComponent } from './components/documentation-editor-dialog/documentation-editor.component';
import { HomeComponent } from './components/home/home.component';
import { NavigationCategoryComponent } from './components/navigation/navigation-category/navigation-category.component';
import { NavigationContainerComponent } from './components/navigation/navigation-container/navigation-container.component';
import { NavigationItemComponent } from './components/navigation/navigation-item/navigation-item.component';
import { OperatorChangeRevisionDialogComponent } from './components/operator-change-revision-dialog/operator-change-revision-dialog.component';
import { PopoverBaseItemComponent } from './components/popover-base-item/popover-base-item.component';
import { ProtocolViewerComponent } from './components/protocol-viewer/protocol-viewer.component';
import { RenameOperatorDialogComponent } from './components/rename-operator-dialog/rename-operator-dialog.component';
import { ToolbarComponent } from './components/toolbar/toolbar.component';
import { WorkflowEditorComponent } from './components/workflow-editor/workflow-editor.component';
import { WorkflowIODialogComponent } from './components/workflow-io-dialog/workflow-io-dialog.component';
import { ErrorVisualDirective } from './directives/error-visual.directive';
import { MaterialModule } from './material.module';
import { ConfigService } from './service/configuration/config.service';
import { AppErrorHandler } from './service/error-handler/app-error-handler.service';
import { HttpErrorInterceptor } from './service/http-interceptors/http-error.interceptor';
import { LocalStorageService } from './service/local-storage/local-storage.service';
import { NotificationService } from './service/notifications/notification.service';
import { ThemeService } from './service/theme/theme.service';
import { appReducers } from './store/app.reducers';

const httpLoaderFactory = (configService: ConfigService) => {
  // we need to first load the hetida designer config upon app initialization, then use its values to initialize the auth module
  // since the auth module uses an APP_INITIALIZER token internally, we have to combine both calls
  // the calls can be split again once we migrate to v14 of the oidc library, see
  // https://github.com/damienbod/angular-auth-oidc-client/blob/main/docs/site/angular-auth-oidc-client/docs/migrations/v13-to-v14.md
  const config$ = from(configService.loadConfig())
    .pipe(
      map(config => {
        // unfortunately, the oidc library requires some config values upon initialization
        // it throws an error if authority and clientId are undefined, which can be ignored if no auth is needed
        // the error can be fixed by migrating to version 14, see above
        return {
          authority: config.authConfig?.authority,
          redirectUrl: window.location.origin,
          clientId: config.authConfig?.clientId,
          responseType: 'code',
          scope: 'openid',
          postLogoutRedirectUri: window.location.origin,
          silentRenew: true,
          silentRenewUrl: `${window.location.origin}/silent-renew.html`,
          ...config.authConfig
        };
      })
    )
    .toPromise();

  return new StsConfigHttpLoader(config$);
};

@NgModule({
  declarations: [
    AppComponent,
    NavigationCategoryComponent,
    NavigationContainerComponent,
    ConfirmDialogComponent,
    ComponentIODialogComponent,
    WorkflowIODialogComponent,
    HomeComponent,
    WorkflowEditorComponent,
    ComponentEditorComponent,
    ContentViewComponent,
    DocumentationEditorComponent,
    DocumentationEditorComponent,
    OperatorChangeRevisionDialogComponent,
    ProtocolViewerComponent,
    ToolbarComponent,
    PopoverBaseItemComponent,
    NavigationItemComponent,
    CopyBaseItemDialogComponent,
    RenameOperatorDialogComponent,
    ErrorVisualDirective,
    BaseItemContextMenuComponent
  ],

  imports: [
    PlotlyViaWindowModule,
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    OwlDateTimeModule,
    OwlNativeDateTimeModule,
    MaterialModule,
    HdWiringModule,
    MonacoEditorModule.forRoot({
      baseUrl: `./assets`
    }), // use forRoot() in main app module only.
    StoreModule.forRoot(appReducers, {
      runtimeChecks: {
        strictStateImmutability: false,
        strictActionImmutability: false,
        strictStateSerializability: false,
        strictActionSerializability: false
      }
    }),
    !environment.production ? StoreDevtoolsModule.instrument() : [],
    NgHetidaFlowchartModule,
    AuthModule.forRoot({
      loader: {
        provide: StsConfigLoader,
        useFactory: httpLoaderFactory,
        deps: [ConfigService]
      }
    }),
    RouterModule.forRoot([
      {
        path: '**',
        component: AppComponent,
        canActivate: [AuthGuard]
      }
    ])
  ],
  providers: [
    NotificationService,
    LocalStorageService,
    { provide: HTTP_INTERCEPTORS, useClass: HttpErrorInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    { provide: ErrorHandler, useClass: AppErrorHandler },
    { provide: MAT_DIALOG_DATA, useValue: {} },
    {
      provide: MAT_DIALOG_DEFAULT_OPTIONS,
      useValue: {
        hasBackdrop: true,
        maxWidth: '95vw',
        width: '95vw',
        disableClose: true
      }
    },
    {
      provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
      useValue: { floatLabel: 'always' }
    },
    { provide: MatDialogRef, useValue: {} },
    ConfigService,
    {
      provide: APP_BASE_HREF,
      useValue: window.location.pathname
    },
    {
      provide: HD_WIRING_CONFIG,
      useFactory: (themeService: ThemeService): HdWiringConfig => {
        const activeTheme = themeService.activeTheme as WiringTheme;
        return {
          allowOutputWiring: true,
          showDownloadExampleJsonButton: true,
          showUploadJsonButton: true,
          allowManualWiring: true,
          monacoEditorTheme: activeTheme,
          showDialogHeader: true,
          confirmationButtonText: 'Execute',
          enableDateRangeSelectionOnSeriesTypes: true
        };
      },
      deps: [ConfigService, ThemeService]
    },
    // Fix for Frozen Progress bar animation, in an *ngIf condition.
    // https://github.com/angular/components/issues/11453#issuecomment-466038415
    { provide: ANIMATION_MODULE_TYPE, useValue: 'BrowserAnimations' }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
