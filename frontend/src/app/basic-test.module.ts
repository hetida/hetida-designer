import { Injectable, NgModule } from '@angular/core';
import { MatIconRegistry } from '@angular/material/icon';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Observable, of } from 'rxjs';
import { MaterialModule } from './material.module';

@Injectable()
export class FakeMatIconRegistry extends MatIconRegistry {
  addSvgIcon(): this {
    return this;
  }

  addSvgIconLiteral(): this {
    return this;
  }

  addSvgIconInNamespace(): this {
    return this;
  }

  addSvgIconLiteralInNamespace(): this {
    return this;
  }

  addSvgIconSet(): this {
    return this;
  }

  addSvgIconSetLiteral(): this {
    return this;
  }

  addSvgIconSetInNamespace(): this {
    return this;
  }

  addSvgIconSetLiteralInNamespace(): this {
    return this;
  }

  registerFontClassAlias(): this {
    return this;
  }

  classNameForFontAlias(alias: string): string {
    return alias;
  }

  getDefaultFontSetClass() {
    return ['material-icons'];
  }

  getSvgIconFromUrl(): Observable<SVGElement> {
    return of(this._generateEmptySvg());
  }

  getNamedSvgIcon(): Observable<SVGElement> {
    return of(this._generateEmptySvg());
  }

  setDefaultFontSetClass(): this {
    return this;
  }

  private _generateEmptySvg(): SVGElement {
    const emptySvg = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'svg'
    );
    emptySvg.classList.add('fake-testing-svg');
    // Emulate real icon characteristics from `MatIconRegistry` so size remains consistent in tests.
    emptySvg.setAttribute('fit', '');
    emptySvg.setAttribute('height', '100%');
    emptySvg.setAttribute('width', '100%');
    emptySvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    emptySvg.setAttribute('focusable', 'false');
    return emptySvg;
  }
}

@NgModule({
  imports: [MaterialModule, NoopAnimationsModule],
  exports: [MaterialModule, NoopAnimationsModule],
  providers: [
    {
      provide: MatIconRegistry,
      useClass: FakeMatIconRegistry
    }
  ]
})
export class BasicTestModule {}
