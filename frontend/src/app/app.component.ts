import { Component, OnInit } from '@angular/core';
// import { OidcSecurityService } from 'angular-auth-oidc-client';

@Component({
  selector: 'hd-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  // constructor(private readonly oidcSecurityService: OidcSecurityService) {}

  ngOnInit() {
    // this.oidcSecurityService.checkAuth().subscribe(({ isAuthenticated }) => {
    //   console.log('callback authenticated', isAuthenticated);
    // });
  }
}
