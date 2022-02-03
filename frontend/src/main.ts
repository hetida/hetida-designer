import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app/app.module';
import { environment } from './environments/environment';

if (environment.production) {
  enableProdMode();
}

platformBrowserDynamic()
  .bootstrapModule(AppModule)
  // .then(moduleRef => {
  //   enables change detection performance monitoring (run in console: ng.profiler.timeChangeDetection())
  //   const applicationRef = moduleRef.injector.get(ApplicationRef);
  //   const componentRef = applicationRef.components[0];
  //   enableDebugTools(componentRef);
  // })
  .catch(err => console.error(err));
