/**
 * Takes any type and makes it an object type.
 * Useful when combined with `&` intersection types.
 * @param T A type who will be converted into an object
 * @returns An object formed by the key, value pairs of T
 */
export type ObjectType<T> = {
  [k in keyof T]: T[k];
};

/**
 * Takes two objects and returns their intersection.
 * This combines all keys and uses `ObjectType` to "clean up" the resultant object.
 * Useful for making extremely complex types look nice in VSCode.
 * @param T First object to be intersected
 * @param U Second object to be intersected
 * @returns `T` & `U` cleaned up to look like flat object to VSCode
 */
export type CombineObjects<T extends object, U extends object> = ObjectType<
  T & U
>;

export type OptionalMembers<
  T extends object,
  K extends keyof T
> = CombineObjects<{ [k in K]?: T[k] | null }, Omit<T, K>>;

export class Utils {
  static string = {
    isEmpty(s: string, trim: boolean = true): boolean {
      return (trim ? s.trim() : s) === '';
    },
    isEmptyOrUndefined(
      s: string | undefined | null,
      trim: boolean = true
    ): boolean {
      if (s === null || s === undefined) {
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

  static isInteger(value: string): value is string {
    return Utils.isNumber(value) && Number.isInteger(+value);
  }

  static isFloat(value: string): value is string {
    return RegExp('^[-+]?[0-9]*.?[0-9]+([eE][-+]?[0-9]+)?$').test(value);
  }

  static isNullOrUndefined(value: any): value is null | undefined {
    return value === null || value === undefined;
  }

  static isDefined<T = any>(value: T): value is Exclude<T, undefined | null> {
    return value !== null && value !== undefined;
  }

  static assert(condition: any, msg?: string): asserts condition {
    if (!condition) {
      throw new Error(msg);
    }
  }
}
