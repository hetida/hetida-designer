interface ThrottleData {
  element: Element;
  lastExec: number;
  once: boolean;
}

export class ThrotteledEventDispatcher {
  constructor(private readonly throttleTime: number) {
    setInterval(() => this.checkTimeout(), throttleTime);
  }

  private readonly throttleMap = new Map<string, ThrottleData>();

  /**
   * checks if the sent event is throtteled,
   * if the combination of element and eventtype doesn't exist we add it
   * @param key element and eventType
   */
  private isThrotteled(element: Element, eventType: string): boolean {
    const keyString = `${eventType}_${element.id}`;
    const data = this.throttleMap.get(keyString);
    let throtteled = false;
    const now = new Date().getTime();
    if (data !== undefined) {
      throtteled = now - data.lastExec < this.throttleTime;
      data.once = false;
    }
    if (!throtteled) {
      const update = {
        element,
        lastExec: now,
        once: true
      };
      this.throttleMap.set(keyString, update);
    }
    return throtteled;
  }

  /**
   * checks all throtteled events, if the wait time has expired and sends the correct event a final time
   */
  private checkTimeout(): void {
    const now = new Date().getTime();
    for (const [key, data] of this.throttleMap) {
      if (data.once) {
        this.throttleMap.delete(key);
        continue;
      }
      if (now - data.lastExec > this.throttleTime) {
        const eventType = key.split('_')[0];
        this.asyncDispatch(
          data.element,
          new Event(eventType, { bubbles: true })
        );
        this.throttleMap.delete(key);
      }
    }
  }

  /**
   * dispatches events asynchronously, without relying on setTimeout
   * setTimeout has a 4ms minimum delay (HTML5 spec)
   * zone.js adds some overhead, which this functions minimizes
   * @param element element the event should be dispatched from
   * @param event event to be dispatched
   */
  private asyncDispatch(element: Element, event: Event): void {
    const dispatch = () => {
      element.dispatchEvent(event);
      window.removeEventListener('message', dispatch, false);
    };
    window.addEventListener('message', dispatch, false);
    window.postMessage('', '*');
  }

  /**
   * dispatches the given event type from the given element synchronously, if not throtteled
   * @PerformanceCritical - this function should be used carefully, as it has to wait for ALL event listeners to be processed
   * @param element element to dispatch the event
   * @param eventType event type to be dispatched
   */
  public dispatch(element: Element, eventType: string): void {
    if (element.getAttribute('dispatcher') === null) {
      return;
    }
    if (this.isThrotteled(element, eventType)) {
      return;
    }
    element.dispatchEvent(new Event(eventType, { bubbles: true }));
  }

  /**
   * dispatches the given event type from the given element asynchronously, if not throtteled
   * @param element element to dispatch the event
   * @param eventType event type to be dispatched
   */
  public dispatchAsync(element: Element | null, eventType: string): void {
    if (element === null) {
      return;
    }
    const dispatcher = this.findDispatcher(element);
    if (this.isThrotteled(dispatcher, eventType)) {
      return;
    }
    this.asyncDispatch(dispatcher, new Event(eventType, { bubbles: true }));
  }

  public dispatchAsyncCustom(
    element: Element | null,
    eventType: string,
    detail: { [key: string]: any } = {}
  ): void {
    if (element === null) {
      return;
    }
    const dispatcher = this.findDispatcher(element);
    if (this.isThrotteled(dispatcher, eventType)) {
      return;
    }
    this.asyncDispatch(
      dispatcher,
      new CustomEvent(eventType, { bubbles: true, detail })
    );
  }

  private findDispatcher(parent: Element): Element {
    if (parent.getAttribute('dispatcher') !== null) {
      return parent;
    }
    for (const child of parent.children) {
      if (child.getAttribute('dispatcher') !== null) {
        return child;
      }
    }
    return parent;
  }
}
