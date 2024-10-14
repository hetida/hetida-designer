import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AppComponent } from './app.component';
import { BasicTestModule } from './basic-test.module';
import { RouterTestingModule } from '@angular/router/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
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
      imports: [
        BasicTestModule,
        FormsModule,
        ReactiveFormsModule,
        HttpClientModule,
        RouterTestingModule
      ],
      providers: [
        {
          provide: OidcSecurityService,
          useClass: OidcSecurityServiceStub
        }
      ],
      declarations: [AppComponent]
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
