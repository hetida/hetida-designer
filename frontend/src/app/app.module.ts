import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { APP_INITIALIZER, ErrorHandler, NgModule } from '@angular/core';
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
import { OwlDateTimeModule } from '@danielmoncada/angular-datetime-picker';
import { OwlMomentDateTimeModule } from '@danielmoncada/angular-datetime-picker-moment-adapter';
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
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';
import { environment } from '../environments/environment';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { AuthCallbackComponent } from './components/auth-callback/auth-callback.component';
import { AuthInterceptor } from './auth/auth.interceptor';
import { TransformationContextMenuComponent } from './components/transformation-context-menu/transformation-context-menu.component';
import { ComponentEditorComponent } from './components/component-editor/component-editor.component';
import { ComponentIODialogComponent } from './components/component-io-dialog/component-io-dialog.component';
import { ConfirmDialogComponent } from './components/confirmation-dialog/confirm-dialog.component';
import { ContentViewComponent } from './components/content-view/content-view.component';
import { CopyTransformationDialogComponent } from './components/copy-transformation-dialog/copy-transformation-dialog.component';
import { DocumentationEditorComponent } from './components/documentation-editor-dialog/documentation-editor.component';
import { HomeComponent } from './components/home/home.component';
import { HomeTabComponent } from './components/home-tab/home-tab.component';
import { NavigationCategoryComponent } from './components/navigation/navigation-category/navigation-category.component';
import { NavigationContainerComponent } from './components/navigation/navigation-container/navigation-container.component';
import { NavigationItemComponent } from './components/navigation/navigation-item/navigation-item.component';
// eslint-disable-next-line max-len
import { OperatorChangeRevisionDialogComponent } from './components/operator-change-revision-dialog/operator-change-revision-dialog.component';
import { PopoverTransformationComponent } from './components/popover-transformation/popover-transformation.component';
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
import { OptionalFieldsDialogComponent } from './components/optional-fields-dialog/optional-fields-dialog.component';
import { from, map } from 'rxjs';

const httpLoaderFactory = (configService: ConfigService) => {
  const authConfig = from(configService.getConfig()).pipe(
    map(config => {
      return {
        authority: config.authConfig?.authority,
        redirectUrl: `${window.location.origin}/authcallback`,
        postLogoutRedirectUri: window.location.origin,
        clientId: config.authConfig?.clientId,
        responseType: 'code',
        scope: 'openid',
        silentRenew: true,
        silentRenewUrl: `${window.location.origin}/silent-renew.html`,
        ...config.authConfig
      };
    })
  );

  return new StsConfigHttpLoader(authConfig);
};

@NgModule({
  declarations: [
    AppComponent,
    AuthCallbackComponent,
    NavigationCategoryComponent,
    NavigationContainerComponent,
    ConfirmDialogComponent,
    ComponentIODialogComponent,
    WorkflowIODialogComponent,
    HomeComponent,
    HomeTabComponent,
    WorkflowEditorComponent,
    ComponentEditorComponent,
    ContentViewComponent,
    DocumentationEditorComponent,
    OperatorChangeRevisionDialogComponent,
    ProtocolViewerComponent,
    ToolbarComponent,
    PopoverTransformationComponent,
    NavigationItemComponent,
    CopyTransformationDialogComponent,
    RenameOperatorDialogComponent,
    ErrorVisualDirective,
    TransformationContextMenuComponent,
    OptionalFieldsDialogComponent
  ],
  imports: [
    AppRoutingModule,
    PlotlyViaWindowModule,
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    OwlDateTimeModule,
    OwlMomentDateTimeModule,
    MaterialModule,
    HdWiringModule,
    MonacoEditorModule.forRoot({
      baseUrl: './assets'
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
    })
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
      provide: APP_INITIALIZER,
      useFactory: (appConfig: ConfigService) => {
        return async () => {
          await appConfig.loadConfig();
        };
      },
      multi: true,
      deps: [ConfigService]
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
