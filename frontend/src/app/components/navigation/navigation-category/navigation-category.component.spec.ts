import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { NavigationItemComponent } from '../navigation-item/navigation-item.component';
import { NavigationCategoryComponent } from './navigation-category.component';

describe('NavigationCategoryComponent', () => {
  let component: NavigationCategoryComponent;
  let fixture: ComponentFixture<NavigationCategoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        MatExpansionModule,
        MatIconModule,
        StoreModule.forRoot(appReducers),
        BrowserAnimationsModule
      ],
      declarations: [NavigationCategoryComponent, NavigationItemComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NavigationCategoryComponent);
    component = fixture.componentInstance;
    component.category = 'COMPONENTS';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
