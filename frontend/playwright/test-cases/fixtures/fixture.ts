import { ConsoleMessage, Page, test as base } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { BackendApi } from './backend-api';

type HetidaDesignerFixture = {
  page: Page;
  hetidaDesigner: HetidaDesigner;
  backendApi: BackendApi;
};

const formatLocation = (msg: ConsoleMessage): string => {
  const location = msg.location();
  return location.url === ''
    ? ''
    : `\n    at ${location.url}:${location.lineNumber}:${location.columnNumber}`;
};

interface ConsoleArgument {
  /**
   * Monaco's CancellationError, which it raises whenever async work started by
   * typing is superseded - a suggestion lookup, a worker round trip. Its name
   * and message are both "Canceled".
   */
  cancellation: boolean;
  text: string;
}

/**
 * Reads the console arguments rather than the rendered message.
 *
 * `msg.text()` renders an Error argument as its toString, so an error without
 * a useful message collapses to the single word "Error" - which was all a
 * failing CI run ever reported. The arguments are live handles that stop
 * working once the page navigates, so this has to start while the message
 * arrives and be awaited later.
 */
const describeConsoleMessage = async (
  msg: ConsoleMessage
): Promise<string | null> => {
  let args: ConsoleArgument[];
  try {
    args = await Promise.all(
      msg.args().map(arg =>
        arg.evaluate((value): ConsoleArgument => {
          if (value instanceof Error) {
            return {
              cancellation: value.name === 'Canceled',
              text: `${value.name}: ${value.message}\n${value.stack ?? ''}`
            };
          }
          return {
            cancellation: false,
            text:
              typeof value === 'object' && value !== null
                ? JSON.stringify(value, Object.getOwnPropertyNames(value))
                : String(value)
          };
        })
      )
    );
  } catch {
    // The page went away before the arguments could be read.
    args = [];
  }

  // Monaco cancels its own async work constantly while text is being typed,
  // and does it far more often on a busy machine. It says nothing about the
  // application, so it must not fail the test - but only an actual
  // CancellationError is ignored, never console errors in general.
  if (args.length > 0 && args.every(arg => arg.cancellation)) {
    return null;
  }

  const rendered =
    args.length > 0 ? args.map(a => a.text).join(' ') : msg.text();

  return `console.${msg.type()}: ${rendered}${formatLocation(msg)}`;
};

export const test = base.extend<HetidaDesignerFixture>({
  page: async ({ baseURL, page }, use) => {
    // Errors logged to the browser console fail the test. They are collected
    // instead of thrown right away: throwing from an event listener aborts
    // whatever step happens to be in flight, which blames an unrelated line and
    // hides the actual message.
    const browserErrors: Promise<string | null>[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        browserErrors.push(describeConsoleMessage(msg));
      }
    });

    page.on('pageerror', error => {
      browserErrors.push(
        Promise.resolve(`uncaught: ${error.stack ?? error.message}`)
      );
    });

    // `baseURL` is always set by playwright.config.ts, its type just allows
    // undefined. The fallback mirrors the default configured there.
    await page.goto(baseURL ?? 'http://localhost', {
      waitUntil: 'domcontentloaded'
    });

    await use(page);

    const reported = (await Promise.all(browserErrors)).filter(
      (entry): entry is string => entry !== null
    );
    if (reported.length > 0) {
      throw new Error(
        `${reported.length} error(s) logged to the browser console:\n\n` +
          reported.join('\n\n')
      );
    }
  },

  hetidaDesigner: async ({ page }, use) => {
    const hetidaDesigner = new HetidaDesigner(page);
    await use(hetidaDesigner);
  },

  backendApi: async ({ request, baseURL }, use) => {
    await use(await BackendApi.create(request, baseURL ?? 'http://localhost'));
  }
});

export { expect } from '@playwright/test';
