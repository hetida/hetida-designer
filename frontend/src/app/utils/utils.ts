export class Utils {
  static string = {
    isEmpty(s: string, trim: boolean = true): boolean {
      return (trim ? s.trim() : s) === '';
    },
    isEmptyOrUndefined(
      s: string | undefined | null,
      trim: boolean = true
    ): boolean {
      if (Utils.isNullOrUndefined(s)) {
        return true;
      }

      return Utils.string.isEmpty(s, trim);
    },
    compare(lhsString: string, rhsString: string): number {
      return lhsString.toLowerCase().localeCompare(rhsString.toLowerCase());
    }
  };

  static object = {
    isEmpty(o: object): boolean {
      return Object.keys(o).length === 0;
    }
  };

  static isNumber(value: string): boolean {
    return !(isNaN(+value) || value.trim() === '');
  }

  static isInteger(value: string) {
    return Utils.isNumber(value) && Number.isInteger(+value);
  }

  static isFloat(value: string): boolean {
    return /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/.test(value);
  }

  static isNullOrUndefined(value: any): boolean {
    return value === null || value === undefined;
  }

  static isDefined<T = any>(value: T): value is Exclude<T, undefined> {
    return value !== null && value !== undefined;
  }

  static assert(condition: any, msg?: string): asserts condition {
    if (!condition) {
      throw new Error(msg);
    }
  }

  static deepCopy<T>(source: T): T {
    // TODO replace with structuredClone once there is better support
    return JSON.parse(JSON.stringify(source)) as typeof source;
  }
}
