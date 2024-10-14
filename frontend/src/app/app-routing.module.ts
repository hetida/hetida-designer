import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { AuthCallbackComponent } from './components/auth-callback/auth-callback.component';
import { AuthGuard } from './auth/auth.guard';
import { AppComponent } from './app.component';

const appRoutes: Routes = [
  {
    path: 'home',
    component: HomeComponent,
    canActivate: [AuthGuard]
  },
  { path: 'authcallback', component: AuthCallbackComponent },
  { path: '', pathMatch: 'full', redirectTo: 'home' },
  {
    path: '**',
    component: AppComponent,
    canActivate: [AuthGuard]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(appRoutes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
