import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AppComponent } from './app.component';
import { BasicTestModule } from './basic-test.module';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { PlotlyViaWindowModule, PlotlyService } from 'angular-plotly.js';
import { of } from 'rxjs';

class OidcSecurityServiceStub {
  checkAuth(url: string) {
    return of(url);
  }
}

describe('AppComponent', () => {
  let app: AppComponent;
  let fixture: ComponentFixture<AppComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AppComponent],
      imports: [
        BasicTestModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forRoot([]),
        PlotlyViaWindowModule
      ],
      providers: [
        {
          provide: OidcSecurityService,
          useClass: OidcSecurityServiceStub
        },
        provideHttpClient(withInterceptorsFromDi()),
        PlotlyService
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AppComponent);
    app = fixture.debugElement.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app', () => {
    expect(app).toBeTruthy();
  });
});
