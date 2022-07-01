/*
 Chen, Yi-Cyuan 2014-2017
 @license MIT
 Kirill, Fomichev 2014
 @license MIT
 Hakes, Taylor 2014
 @license MIT
*/
(function (K, L) {
  if ('object' === typeof exports)
    'object' === typeof module
      ? (module.exports = L(require('js-sha256'), require('base64-js')))
      : (exports.keycloak = L(require('js-sha256'), require('base64-js')));
  else {
    !(function () {
      function p(b, a) {
        a
          ? ((r[0] = r[16] = r[1] = r[2] = r[3] = r[4] = r[5] = r[6] = r[7] = r[8] = r[9] = r[10] = r[11] = r[12] = r[13] = r[14] = r[15] = 0),
            (this.blocks = r))
          : (this.blocks = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        b
          ? ((this.h0 = 3238371032),
            (this.h1 = 914150663),
            (this.h2 = 812702999),
            (this.h3 = 4144912697),
            (this.h4 = 4290775857),
            (this.h5 = 1750603025),
            (this.h6 = 1694076839),
            (this.h7 = 3204075428))
          : ((this.h0 = 1779033703),
            (this.h1 = 3144134277),
            (this.h2 = 1013904242),
            (this.h3 = 2773480762),
            (this.h4 = 1359893119),
            (this.h5 = 2600822924),
            (this.h6 = 528734635),
            (this.h7 = 1541459225));
        this.block = this.start = this.bytes = this.hBytes = 0;
        this.finalized = this.hashed = !1;
        this.first = !0;
        this.is224 = b;
      }
      function w(b, a, d) {
        var z;
        z = typeof b;
        if ('string' === z) {
          var e,
            x = [],
            k = b.length,
            c = 0;
          for (z = 0; z < k; ++z)
            128 > (e = b.charCodeAt(z))
              ? (x[c++] = e)
              : 2048 > e
              ? ((x[c++] = 192 | (e >> 6)), (x[c++] = 128 | (63 & e)))
              : 55296 > e || 57344 <= e
              ? ((x[c++] = 224 | (e >> 12)),
                (x[c++] = 128 | ((e >> 6) & 63)),
                (x[c++] = 128 | (63 & e)))
              : ((e =
                  65536 + (((1023 & e) << 10) | (1023 & b.charCodeAt(++z)))),
                (x[c++] = 240 | (e >> 18)),
                (x[c++] = 128 | ((e >> 12) & 63)),
                (x[c++] = 128 | ((e >> 6) & 63)),
                (x[c++] = 128 | (63 & e)));
          b = x;
        } else {
          if ('object' !== z) throw Error(l);
          if (null === b) throw Error(l);
          if (D && b.constructor === ArrayBuffer) b = new Uint8Array(b);
          else if (!(Array.isArray(b) || (D && ArrayBuffer.isView(b))))
            throw Error(l);
        }
        64 < b.length && (b = new p(a, !0).update(b).array());
        e = [];
        x = [];
        for (z = 0; 64 > z; ++z)
          (k = b[z] || 0), (e[z] = 92 ^ k), (x[z] = 54 ^ k);
        p.call(this, a, d);
        this.update(x);
        this.oKeyPad = e;
        this.inner = !0;
        this.sharedMemory = d;
      }
      var l = 'input is invalid type',
        u = 'object' == typeof window,
        n = u ? window : {};
      n.JS_SHA256_NO_WINDOW && (u = !1);
      var u = !u && 'object' == typeof self,
        y =
          !n.JS_SHA256_NO_NODE_JS &&
          'object' == typeof process &&
          process.versions &&
          process.versions.node;
      y ? (n = global) : u && (n = self);
      var u =
          !n.JS_SHA256_NO_COMMON_JS &&
          'object' == typeof module &&
          module.exports,
        q = 'function' == typeof define && define.amd,
        D = !n.JS_SHA256_NO_ARRAY_BUFFER && 'undefined' != typeof ArrayBuffer,
        a = '0123456789abcdef'.split(''),
        g = [-2147483648, 8388608, 32768, 128],
        d = [24, 16, 8, 0],
        c = [
          1116352408,
          1899447441,
          3049323471,
          3921009573,
          961987163,
          1508970993,
          2453635748,
          2870763221,
          3624381080,
          310598401,
          607225278,
          1426881987,
          1925078388,
          2162078206,
          2614888103,
          3248222580,
          3835390401,
          4022224774,
          264347078,
          604807628,
          770255983,
          1249150122,
          1555081692,
          1996064986,
          2554220882,
          2821834349,
          2952996808,
          3210313671,
          3336571891,
          3584528711,
          113926993,
          338241895,
          666307205,
          773529912,
          1294757372,
          1396182291,
          1695183700,
          1986661051,
          2177026350,
          2456956037,
          2730485921,
          2820302411,
          3259730800,
          3345764771,
          3516065817,
          3600352804,
          4094571909,
          275423344,
          430227734,
          506948616,
          659060556,
          883997877,
          958139571,
          1322822218,
          1537002063,
          1747873779,
          1955562222,
          2024104815,
          2227730452,
          2361852424,
          2428436474,
          2756734187,
          3204031479,
          3329325298
        ],
        f = ['hex', 'array', 'digest', 'arrayBuffer'],
        r = [];
      (!n.JS_SHA256_NO_NODE_JS && Array.isArray) ||
        (Array.isArray = function (b) {
          return '[object Array]' === Object.prototype.toString.call(b);
        });
      !D ||
        (!n.JS_SHA256_NO_ARRAY_BUFFER_IS_VIEW && ArrayBuffer.isView) ||
        (ArrayBuffer.isView = function (b) {
          return (
            'object' == typeof b &&
            b.buffer &&
            b.buffer.constructor === ArrayBuffer
          );
        });
      var m = function (b, a) {
          return function (d) {
            return new p(a, !0).update(d)[b]();
          };
        },
        I = function (b) {
          var a = m('hex', b);
          y && (a = Q(a, b));
          a.create = function () {
            return new p(b);
          };
          a.update = function (b) {
            return a.create().update(b);
          };
          for (var d = 0; d < f.length; ++d) {
            var c = f[d];
            a[c] = m(c, b);
          }
          return a;
        },
        Q = function (b, a) {
          var d = eval("require('crypto')"),
            c = eval("require('buffer').Buffer"),
            e = a ? 'sha224' : 'sha256';
          return function (a) {
            if ('string' == typeof a)
              return d.createHash(e).update(a, 'utf8').digest('hex');
            if (null === a || void 0 === a) throw Error(l);
            return (
              a.constructor === ArrayBuffer && (a = new Uint8Array(a)),
              Array.isArray(a) || ArrayBuffer.isView(a) || a.constructor === c
                ? d.createHash(e).update(new c(a)).digest('hex')
                : b(a)
            );
          };
        },
        F = function (b, a) {
          return function (d, c) {
            return new w(d, a, !0).update(c)[b]();
          };
        },
        J = function (b) {
          var a = F('hex', b);
          a.create = function (a) {
            return new w(a, b);
          };
          a.update = function (b, d) {
            return a.create(b).update(d);
          };
          for (var d = 0; d < f.length; ++d) {
            var c = f[d];
            a[c] = F(c, b);
          }
          return a;
        };
      p.prototype.update = function (b) {
        if (!this.finalized) {
          var a,
            c = typeof b;
          if ('string' !== c) {
            if ('object' !== c) throw Error(l);
            if (null === b) throw Error(l);
            if (D && b.constructor === ArrayBuffer) b = new Uint8Array(b);
            else if (!(Array.isArray(b) || (D && ArrayBuffer.isView(b))))
              throw Error(l);
            a = !0;
          }
          for (var f, e = 0, r = b.length, k = this.blocks; e < r; ) {
            if (
              (this.hashed &&
                ((this.hashed = !1),
                (k[0] = this.block),
                (k[16] = k[1] = k[2] = k[3] = k[4] = k[5] = k[6] = k[7] = k[8] = k[9] = k[10] = k[11] = k[12] = k[13] = k[14] = k[15] = 0)),
              a)
            )
              for (c = this.start; e < r && 64 > c; ++e)
                k[c >> 2] |= b[e] << d[3 & c++];
            else
              for (c = this.start; e < r && 64 > c; ++e)
                128 > (f = b.charCodeAt(e))
                  ? (k[c >> 2] |= f << d[3 & c++])
                  : 2048 > f
                  ? ((k[c >> 2] |= (192 | (f >> 6)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | (63 & f)) << d[3 & c++]))
                  : 55296 > f || 57344 <= f
                  ? ((k[c >> 2] |= (224 | (f >> 12)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | ((f >> 6) & 63)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | (63 & f)) << d[3 & c++]))
                  : ((f =
                      65536 +
                      (((1023 & f) << 10) | (1023 & b.charCodeAt(++e)))),
                    (k[c >> 2] |= (240 | (f >> 18)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | ((f >> 12) & 63)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | ((f >> 6) & 63)) << d[3 & c++]),
                    (k[c >> 2] |= (128 | (63 & f)) << d[3 & c++]));
            this.lastByteIndex = c;
            this.bytes += c - this.start;
            64 <= c
              ? ((this.block = k[16]),
                (this.start = c - 64),
                this.hash(),
                (this.hashed = !0))
              : (this.start = c);
          }
          return (
            4294967295 < this.bytes &&
              ((this.hBytes += (this.bytes / 4294967296) << 0),
              (this.bytes %= 4294967296)),
            this
          );
        }
      };
      p.prototype.finalize = function () {
        if (!this.finalized) {
          this.finalized = !0;
          var b = this.blocks,
            a = this.lastByteIndex;
          b[16] = this.block;
          b[a >> 2] |= g[3 & a];
          this.block = b[16];
          56 <= a &&
            (this.hashed || this.hash(),
            (b[0] = this.block),
            (b[16] = b[1] = b[2] = b[3] = b[4] = b[5] = b[6] = b[7] = b[8] = b[9] = b[10] = b[11] = b[12] = b[13] = b[14] = b[15] = 0));
          b[14] = (this.hBytes << 3) | (this.bytes >>> 29);
          b[15] = this.bytes << 3;
          this.hash();
        }
      };
      p.prototype.hash = function () {
        var b,
          a,
          d,
          f,
          e,
          r,
          k,
          m = this.h0,
          g = this.h1,
          n = this.h2,
          l = this.h3,
          p = this.h4,
          h = this.h5,
          t = this.h6,
          A = this.h7,
          C = this.blocks;
        for (b = 16; 64 > b; ++b)
          (a =
            (((e = C[b - 15]) >>> 7) | (e << 25)) ^
            ((e >>> 18) | (e << 14)) ^
            (e >>> 3)),
            (d =
              (((e = C[b - 2]) >>> 17) | (e << 15)) ^
              ((e >>> 19) | (e << 13)) ^
              (e >>> 10)),
            (C[b] = (C[b - 16] + a + C[b - 7] + d) << 0);
        k = g & n;
        for (b = 0; 64 > b; b += 4)
          this.first
            ? (this.is224
                ? ((r = 300032),
                  (A = ((e = C[0] - 1413257819) - 150054599) << 0),
                  (l = (e + 24177077) << 0))
                : ((r = 704751109),
                  (A = ((e = C[0] - 210244248) - 1521486534) << 0),
                  (l = (e + 143694565) << 0)),
              (this.first = !1))
            : ((a =
                ((m >>> 2) | (m << 30)) ^
                ((m >>> 13) | (m << 19)) ^
                ((m >>> 22) | (m << 10))),
              (f = (r = m & g) ^ (m & n) ^ k),
              (A =
                (l +
                  (e =
                    A +
                    (((p >>> 6) | (p << 26)) ^
                      ((p >>> 11) | (p << 21)) ^
                      ((p >>> 25) | (p << 7))) +
                    ((p & h) ^ (~p & t)) +
                    c[b] +
                    C[b])) <<
                0),
              (l = (e + (a + f)) << 0)),
            (a =
              ((l >>> 2) | (l << 30)) ^
              ((l >>> 13) | (l << 19)) ^
              ((l >>> 22) | (l << 10))),
            (f = (k = l & m) ^ (l & g) ^ r),
            (t =
              (n +
                (e =
                  t +
                  (((A >>> 6) | (A << 26)) ^
                    ((A >>> 11) | (A << 21)) ^
                    ((A >>> 25) | (A << 7))) +
                  ((A & p) ^ (~A & h)) +
                  c[b + 1] +
                  C[b + 1])) <<
              0),
            (a =
              (((n = (e + (a + f)) << 0) >>> 2) | (n << 30)) ^
              ((n >>> 13) | (n << 19)) ^
              ((n >>> 22) | (n << 10))),
            (f = (d = n & l) ^ (n & m) ^ k),
            (h =
              (g +
                (e =
                  h +
                  (((t >>> 6) | (t << 26)) ^
                    ((t >>> 11) | (t << 21)) ^
                    ((t >>> 25) | (t << 7))) +
                  ((t & A) ^ (~t & p)) +
                  c[b + 2] +
                  C[b + 2])) <<
              0),
            (a =
              (((g = (e + (a + f)) << 0) >>> 2) | (g << 30)) ^
              ((g >>> 13) | (g << 19)) ^
              ((g >>> 22) | (g << 10))),
            (f = (k = g & n) ^ (g & l) ^ d),
            (p =
              (m +
                (e =
                  p +
                  (((h >>> 6) | (h << 26)) ^
                    ((h >>> 11) | (h << 21)) ^
                    ((h >>> 25) | (h << 7))) +
                  ((h & t) ^ (~h & A)) +
                  c[b + 3] +
                  C[b + 3])) <<
              0),
            (m = (e + (a + f)) << 0);
        this.h0 = (this.h0 + m) << 0;
        this.h1 = (this.h1 + g) << 0;
        this.h2 = (this.h2 + n) << 0;
        this.h3 = (this.h3 + l) << 0;
        this.h4 = (this.h4 + p) << 0;
        this.h5 = (this.h5 + h) << 0;
        this.h6 = (this.h6 + t) << 0;
        this.h7 = (this.h7 + A) << 0;
      };
      p.prototype.hex = function () {
        this.finalize();
        var b = this.h0,
          c = this.h1,
          d = this.h2,
          f = this.h3,
          e = this.h4,
          m = this.h5,
          k = this.h6,
          g = this.h7,
          b =
            a[(b >> 28) & 15] +
            a[(b >> 24) & 15] +
            a[(b >> 20) & 15] +
            a[(b >> 16) & 15] +
            a[(b >> 12) & 15] +
            a[(b >> 8) & 15] +
            a[(b >> 4) & 15] +
            a[15 & b] +
            a[(c >> 28) & 15] +
            a[(c >> 24) & 15] +
            a[(c >> 20) & 15] +
            a[(c >> 16) & 15] +
            a[(c >> 12) & 15] +
            a[(c >> 8) & 15] +
            a[(c >> 4) & 15] +
            a[15 & c] +
            a[(d >> 28) & 15] +
            a[(d >> 24) & 15] +
            a[(d >> 20) & 15] +
            a[(d >> 16) & 15] +
            a[(d >> 12) & 15] +
            a[(d >> 8) & 15] +
            a[(d >> 4) & 15] +
            a[15 & d] +
            a[(f >> 28) & 15] +
            a[(f >> 24) & 15] +
            a[(f >> 20) & 15] +
            a[(f >> 16) & 15] +
            a[(f >> 12) & 15] +
            a[(f >> 8) & 15] +
            a[(f >> 4) & 15] +
            a[15 & f] +
            a[(e >> 28) & 15] +
            a[(e >> 24) & 15] +
            a[(e >> 20) & 15] +
            a[(e >> 16) & 15] +
            a[(e >> 12) & 15] +
            a[(e >> 8) & 15] +
            a[(e >> 4) & 15] +
            a[15 & e] +
            a[(m >> 28) & 15] +
            a[(m >> 24) & 15] +
            a[(m >> 20) & 15] +
            a[(m >> 16) & 15] +
            a[(m >> 12) & 15] +
            a[(m >> 8) & 15] +
            a[(m >> 4) & 15] +
            a[15 & m] +
            a[(k >> 28) & 15] +
            a[(k >> 24) & 15] +
            a[(k >> 20) & 15] +
            a[(k >> 16) & 15] +
            a[(k >> 12) & 15] +
            a[(k >> 8) & 15] +
            a[(k >> 4) & 15] +
            a[15 & k];
        return (
          this.is224 ||
            (b +=
              a[(g >> 28) & 15] +
              a[(g >> 24) & 15] +
              a[(g >> 20) & 15] +
              a[(g >> 16) & 15] +
              a[(g >> 12) & 15] +
              a[(g >> 8) & 15] +
              a[(g >> 4) & 15] +
              a[15 & g]),
          b
        );
      };
      p.prototype.toString = p.prototype.hex;
      p.prototype.digest = function () {
        this.finalize();
        var b = this.h0,
          a = this.h1,
          c = this.h2,
          d = this.h3,
          f = this.h4,
          m = this.h5,
          k = this.h6,
          g = this.h7,
          b = [
            (b >> 24) & 255,
            (b >> 16) & 255,
            (b >> 8) & 255,
            255 & b,
            (a >> 24) & 255,
            (a >> 16) & 255,
            (a >> 8) & 255,
            255 & a,
            (c >> 24) & 255,
            (c >> 16) & 255,
            (c >> 8) & 255,
            255 & c,
            (d >> 24) & 255,
            (d >> 16) & 255,
            (d >> 8) & 255,
            255 & d,
            (f >> 24) & 255,
            (f >> 16) & 255,
            (f >> 8) & 255,
            255 & f,
            (m >> 24) & 255,
            (m >> 16) & 255,
            (m >> 8) & 255,
            255 & m,
            (k >> 24) & 255,
            (k >> 16) & 255,
            (k >> 8) & 255,
            255 & k
          ];
        return (
          this.is224 ||
            b.push((g >> 24) & 255, (g >> 16) & 255, (g >> 8) & 255, 255 & g),
          b
        );
      };
      p.prototype.array = p.prototype.digest;
      p.prototype.arrayBuffer = function () {
        this.finalize();
        var b = new ArrayBuffer(this.is224 ? 28 : 32),
          a = new DataView(b);
        return (
          a.setUint32(0, this.h0),
          a.setUint32(4, this.h1),
          a.setUint32(8, this.h2),
          a.setUint32(12, this.h3),
          a.setUint32(16, this.h4),
          a.setUint32(20, this.h5),
          a.setUint32(24, this.h6),
          this.is224 || a.setUint32(28, this.h7),
          b
        );
      };
      w.prototype = new p();
      w.prototype.finalize = function () {
        if ((p.prototype.finalize.call(this), this.inner)) {
          this.inner = !1;
          var b = this.array();
          p.call(this, this.is224, this.sharedMemory);
          this.update(this.oKeyPad);
          this.update(b);
          p.prototype.finalize.call(this);
        }
      };
      var B = I();
      B.sha256 = B;
      B.sha224 = I(!0);
      B.sha256.hmac = J();
      B.sha224.hmac = J(!0);
      u
        ? (module.exports = B)
        : ((n.sha256 = B.sha256),
          (n.sha224 = B.sha224),
          q &&
            define(function () {
              return B;
            }));
    })();
    (function (p) {
      'object' === typeof exports && 'undefined' !== typeof module
        ? (module.exports = p())
        : 'function' === typeof define && define.amd
        ? define([], p)
        : (('undefined' !== typeof window
            ? window
            : 'undefined' !== typeof global
            ? global
            : 'undefined' !== typeof self
            ? self
            : this
          ).base64js = p());
    })(function () {
      return (function () {
        function p(w, l, u) {
          function n(q, a) {
            if (!l[q]) {
              if (!w[q]) {
                var g = 'function' == typeof require && require;
                if (!a && g) return g(q, !0);
                if (y) return y(q, !0);
                a = Error("Cannot find module '" + q + "'");
                throw ((a.code = 'MODULE_NOT_FOUND'), a);
              }
              a = l[q] = { exports: {} };
              w[q][0].call(
                a.exports,
                function (a) {
                  return n(w[q][1][a] || a);
                },
                a,
                a.exports,
                p,
                w,
                l,
                u
              );
            }
            return l[q].exports;
          }
          for (
            var y = 'function' == typeof require && require, q = 0;
            q < u.length;
            q++
          )
            n(u[q]);
          return n;
        }
        return p;
      })()(
        {
          '/': [
            function (p, w, l) {
              function u(a) {
                var g = a.length;
                if (0 < g % 4)
                  throw Error('Invalid string. Length must be a multiple of 4');
                a = a.indexOf('\x3d');
                -1 === a && (a = g);
                return [a, a === g ? 0 : 4 - (a % 4)];
              }
              function n(a, g, d) {
                for (var c = [], f = g; f < d; f += 3)
                  (g =
                    ((a[f] << 16) & 16711680) +
                    ((a[f + 1] << 8) & 65280) +
                    (a[f + 2] & 255)),
                    c.push(
                      y[(g >> 18) & 63] +
                        y[(g >> 12) & 63] +
                        y[(g >> 6) & 63] +
                        y[g & 63]
                    );
                return c.join('');
              }
              l.byteLength = function (a) {
                a = u(a);
                var g = a[1];
                return (3 * (a[0] + g)) / 4 - g;
              };
              l.toByteArray = function (a) {
                var g,
                  d = u(a);
                g = d[0];
                for (
                  var d = d[1],
                    c = new D((3 * (g + d)) / 4 - d),
                    f = 0,
                    r = 0 < d ? g - 4 : g,
                    m = 0;
                  m < r;
                  m += 4
                )
                  (g =
                    (q[a.charCodeAt(m)] << 18) |
                    (q[a.charCodeAt(m + 1)] << 12) |
                    (q[a.charCodeAt(m + 2)] << 6) |
                    q[a.charCodeAt(m + 3)]),
                    (c[f++] = (g >> 16) & 255),
                    (c[f++] = (g >> 8) & 255),
                    (c[f++] = g & 255);
                2 === d &&
                  ((g =
                    (q[a.charCodeAt(m)] << 2) | (q[a.charCodeAt(m + 1)] >> 4)),
                  (c[f++] = g & 255));
                1 === d &&
                  ((g =
                    (q[a.charCodeAt(m)] << 10) |
                    (q[a.charCodeAt(m + 1)] << 4) |
                    (q[a.charCodeAt(m + 2)] >> 2)),
                  (c[f++] = (g >> 8) & 255),
                  (c[f++] = g & 255));
                return c;
              };
              l.fromByteArray = function (a) {
                for (
                  var g = a.length, d = g % 3, c = [], f = 0, r = g - d;
                  f < r;
                  f += 16383
                )
                  c.push(n(a, f, f + 16383 > r ? r : f + 16383));
                1 === d
                  ? ((a = a[g - 1]),
                    c.push(y[a >> 2] + y[(a << 4) & 63] + '\x3d\x3d'))
                  : 2 === d &&
                    ((a = (a[g - 2] << 8) + a[g - 1]),
                    c.push(
                      y[a >> 10] + y[(a >> 4) & 63] + y[(a << 2) & 63] + '\x3d'
                    ));
                return c.join('');
              };
              var y = [],
                q = [],
                D = 'undefined' !== typeof Uint8Array ? Uint8Array : Array;
              for (p = 0; 64 > p; ++p)
                (y[
                  p
                ] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'[
                  p
                ]),
                  (q[
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'.charCodeAt(
                      p
                    )
                  ] = p);
              q[45] = 62;
              q[95] = 63;
            },
            {}
          ]
        },
        {},
        []
      )('/');
    });
    !(function (p, w) {
      'object' == typeof exports && 'undefined' != typeof module
        ? w()
        : 'function' == typeof define && define.amd
        ? define(w)
        : w();
    })(0, function () {
      function p(a) {
        var c = this.constructor;
        return this.then(
          function (d) {
            return c.resolve(a()).then(function () {
              return d;
            });
          },
          function (d) {
            return c.resolve(a()).then(function () {
              return c.reject(d);
            });
          }
        );
      }
      function w() {}
      function l(a) {
        if (!(this instanceof l))
          throw new TypeError('Promises must be constructed via new');
        if ('function' != typeof a) throw new TypeError('not a function');
        this._state = 0;
        this._handled = !1;
        this._value = void 0;
        this._deferreds = [];
        D(a, this);
      }
      function u(a, c) {
        for (; 3 === a._state; ) a = a._value;
        0 !== a._state
          ? ((a._handled = !0),
            l._immediateFn(function () {
              var d = 1 === a._state ? c.onFulfilled : c.onRejected;
              if (null !== d) {
                var g;
                try {
                  g = d(a._value);
                } catch (m) {
                  return void y(c.promise, m);
                }
                n(c.promise, g);
              } else (1 === a._state ? n : y)(c.promise, a._value);
            }))
          : a._deferreds.push(c);
      }
      function n(a, c) {
        try {
          if (c === a)
            throw new TypeError('A promise cannot be resolved with itself.');
          if (c && ('object' == typeof c || 'function' == typeof c)) {
            var d = c.then;
            if (c instanceof l)
              return (a._state = 3), (a._value = c), void q(a);
            if ('function' == typeof d)
              return void D(
                (function (a, c) {
                  return function () {
                    a.apply(c, arguments);
                  };
                })(d, c),
                a
              );
          }
          a._state = 1;
          a._value = c;
          q(a);
        } catch (r) {
          y(a, r);
        }
      }
      function y(a, c) {
        a._state = 2;
        a._value = c;
        q(a);
      }
      function q(a) {
        2 === a._state &&
          0 === a._deferreds.length &&
          l._immediateFn(function () {
            a._handled || l._unhandledRejectionFn(a._value);
          });
        for (var c = 0, d = a._deferreds.length; d > c; c++)
          u(a, a._deferreds[c]);
        a._deferreds = null;
      }
      function D(a, c) {
        var d = !1;
        try {
          a(
            function (a) {
              d || ((d = !0), n(c, a));
            },
            function (a) {
              d || ((d = !0), y(c, a));
            }
          );
        } catch (r) {
          d || ((d = !0), y(c, r));
        }
      }
      var a = setTimeout;
      l.prototype['catch'] = function (a) {
        return this.then(null, a);
      };
      l.prototype.then = function (a, c) {
        var d = new this.constructor(w);
        return (
          u(
            this,
            new (function (a, c, d) {
              this.onFulfilled = 'function' == typeof a ? a : null;
              this.onRejected = 'function' == typeof c ? c : null;
              this.promise = d;
            })(a, c, d)
          ),
          d
        );
      };
      l.prototype['finally'] = p;
      l.all = function (a) {
        return new l(function (c, d) {
          function g(a, m) {
            try {
              if (m && ('object' == typeof m || 'function' == typeof m)) {
                var n = m.then;
                if ('function' == typeof n)
                  return void n.call(
                    m,
                    function (b) {
                      g(a, b);
                    },
                    d
                  );
              }
              f[a] = m;
              0 == --l && c(f);
            } catch (b) {
              d(b);
            }
          }
          if (!a || 'undefined' == typeof a.length)
            return d(new TypeError('Promise.all accepts an array'));
          var f = Array.prototype.slice.call(a);
          if (0 === f.length) return c([]);
          for (var l = f.length, n = 0; f.length > n; n++) g(n, f[n]);
        });
      };
      l.resolve = function (a) {
        return a && 'object' == typeof a && a.constructor === l
          ? a
          : new l(function (c) {
              c(a);
            });
      };
      l.reject = function (a) {
        return new l(function (c, d) {
          d(a);
        });
      };
      l.race = function (a) {
        return new l(function (c, d) {
          if (!a || 'undefined' == typeof a.length)
            return d(new TypeError('Promise.race accepts an array'));
          for (var g = 0, f = a.length; f > g; g++) l.resolve(a[g]).then(c, d);
        });
      };
      l._immediateFn =
        ('function' == typeof setImmediate &&
          function (a) {
            setImmediate(a);
          }) ||
        function (d) {
          a(d, 0);
        };
      l._unhandledRejectionFn = function (a) {
        void 0 !== console &&
          console &&
          console.warn('Possible Unhandled Promise Rejection:', a);
      };
      var g = (function () {
        if ('undefined' != typeof self) return self;
        if ('undefined' != typeof window) return window;
        if ('undefined' != typeof global) return global;
        throw Error('unable to locate global object');
      })();
      'Promise' in g
        ? g.Promise.prototype['finally'] || (g.Promise.prototype['finally'] = p)
        : (g.Promise = l);
    });
    var E = L(K.sha256, K.base64js);
    K.Keycloak = E;
    'function' === typeof define &&
      define.amd &&
      define('keycloak', [], function () {
        return E;
      });
  }
})(window, function (K, L) {
  function E() {
    u ||
      ((u = !0),
      console.warn(
        '[KEYCLOAK] Usage of legacy style promise methods such as `.error()` and `.success()` has been deprecated and support will be removed in future versions. Use standard style promise methods such as `.then() and `.catch()` instead.'
      ));
  }
  function p(n) {
    n.__proto__ = w.prototype;
    return n;
  }
  function w(n) {
    return p(new Promise(n));
  }
  function l(n) {
    function p(b, a) {
      var h;
      var c = window.crypto || window.msCrypto;
      if (c && c.getRandomValues && window.Uint8Array)
        (h = new Uint8Array(b)), c.getRandomValues(h);
      else
        for (h = Array(b), c = 0; c < h.length; c++)
          h[c] = Math.floor(256 * Math.random());
      for (var c = Array(b), t = 0; t < b; t++)
        c[t] = a.charCodeAt(h[t] % a.length);
      return String.fromCharCode.apply(null, c);
    }
    function q() {
      if ('undefined' !== typeof b.authServerUrl)
        return '/' == b.authServerUrl.charAt(b.authServerUrl.length - 1)
          ? b.authServerUrl + 'realms/' + encodeURIComponent(b.realm)
          : b.authServerUrl + '/realms/' + encodeURIComponent(b.realm);
    }
    function u(a, c) {
      function h(h, t, v, d) {
        e = (e + new Date().getTime()) / 2;
        g(h, t, v, e);
        N &&
        ((b.tokenParsed && b.tokenParsed.nonce != a.storedNonce) ||
          (b.refreshTokenParsed &&
            b.refreshTokenParsed.nonce != a.storedNonce) ||
          (b.idTokenParsed && b.idTokenParsed.nonce != a.storedNonce))
          ? (G('[KEYCLOAK] Invalid nonce, clearing token'),
            b.clearToken(),
            c && c.setError())
          : d && (b.onAuthSuccess && b.onAuthSuccess(), c && c.setSuccess());
      }
      var t = a.code,
        d = a.error,
        v = a.prompt,
        e = new Date().getTime();
      a.kc_action_status &&
        b.onActionUpdate &&
        b.onActionUpdate(a.kc_action_status);
      if (d)
        'none' != v
          ? ((t = { error: d, error_description: a.error_description }),
            b.onAuthError && b.onAuthError(t),
            c && c.setError(t))
          : c && c.setSuccess();
      else if (
        ('standard' != b.flow &&
          (a.access_token || a.id_token) &&
          h(a.access_token, null, a.id_token, !0),
        'implicit' != b.flow && t)
      ) {
        var t = 'code\x3d' + t + '\x26grant_type\x3dauthorization_code',
          d = b.endpoints.token(),
          f = new XMLHttpRequest();
        f.open('POST', d, !0);
        f.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        t += '\x26client_id\x3d' + encodeURIComponent(b.clientId);
        t += '\x26redirect_uri\x3d' + a.redirectUri;
        a.pkceCodeVerifier &&
          (t += '\x26code_verifier\x3d' + a.pkceCodeVerifier);
        f.withCredentials = !0;
        f.onreadystatechange = function () {
          if (4 == f.readyState)
            if (200 == f.status) {
              var a = JSON.parse(f.responseText);
              h(
                a.access_token,
                a.refresh_token,
                a.id_token,
                'standard' === b.flow
              );
              E();
            } else b.onAuthError && b.onAuthError(), c && c.setError();
        };
        f.send(t);
      }
    }
    function a(a) {
      function h(a) {
        b.endpoints = a
          ? {
              authorize: function () {
                return a.authorization_endpoint;
              },
              token: function () {
                return a.token_endpoint;
              },
              logout: function () {
                if (!a.end_session_endpoint)
                  throw 'Not supported by the OIDC server';
                return a.end_session_endpoint;
              },
              checkSessionIframe: function () {
                if (!a.check_session_iframe)
                  throw 'Not supported by the OIDC server';
                return a.check_session_iframe;
              },
              register: function () {
                throw 'Redirection to "Register user" page not supported in standard OIDC mode';
              },
              userinfo: function () {
                if (!a.userinfo_endpoint)
                  throw 'Not supported by the OIDC server';
                return a.userinfo_endpoint;
              }
            }
          : {
              authorize: function () {
                return q() + '/protocol/openid-connect/auth';
              },
              token: function () {
                return q() + '/protocol/openid-connect/token';
              },
              logout: function () {
                return q() + '/protocol/openid-connect/logout';
              },
              checkSessionIframe: function () {
                var a =
                  q() + '/protocol/openid-connect/login-status-iframe.html';
                b.iframeVersion && (a = a + '?version\x3d' + b.iframeVersion);
                return a;
              },
              register: function () {
                return q() + '/protocol/openid-connect/registrations';
              },
              userinfo: function () {
                return q() + '/protocol/openid-connect/userinfo';
              }
            };
      }
      var c = m(),
        d;
      n ? 'string' === typeof n && (d = n) : (d = 'keycloak.json');
      if (d) {
        var e = new XMLHttpRequest();
        e.open('GET', d, !0);
        e.setRequestHeader('Accept', 'application/json');
        e.onreadystatechange = function () {
          if (4 == e.readyState)
            if (
              200 == e.status ||
              (0 == e.status &&
                e.responseText &&
                e.responseURL.startsWith('file:'))
            ) {
              var a = JSON.parse(e.responseText);
              b.authServerUrl = a['auth-server-url'];
              b.realm = a.realm;
              b.clientId = a.resource;
              h(null);
              c.setSuccess();
            } else c.setError();
        };
        e.send();
      } else {
        if (!n.clientId) throw 'clientId missing';
        b.clientId = n.clientId;
        if ((a = n.oidcProvider))
          'string' === typeof a
            ? ((a =
                '/' == a.charAt(a.length - 1)
                  ? a + '.well-known/openid-configuration'
                  : a + '/.well-known/openid-configuration'),
              (e = new XMLHttpRequest()),
              e.open('GET', a, !0),
              e.setRequestHeader('Accept', 'application/json'),
              (e.onreadystatechange = function () {
                if (4 == e.readyState)
                  if (
                    200 == e.status ||
                    (0 == e.status &&
                      e.responseText &&
                      e.responseURL.startsWith('file:'))
                  ) {
                    var b = JSON.parse(e.responseText);
                    h(b);
                    c.setSuccess();
                  } else c.setError();
              }),
              e.send())
            : (h(a), c.setSuccess());
        else {
          if (!n.url)
            for (
              a = document.getElementsByTagName('script'), d = 0;
              d < a.length;
              d++
            )
              if (a[d].src.match(/.*keycloak\.js/)) {
                n.url = a[d].src.substr(0, a[d].src.indexOf('/js/keycloak.js'));
                break;
              }
          if (!n.realm) throw 'realm missing';
          b.authServerUrl = n.url;
          b.realm = n.realm;
          h(null);
          c.setSuccess();
        }
      }
      return c.promise;
    }
    function g(a, c, e, f) {
      b.tokenTimeoutHandle &&
        (clearTimeout(b.tokenTimeoutHandle), (b.tokenTimeoutHandle = null));
      c
        ? ((b.refreshToken = c), (b.refreshTokenParsed = d(c)))
        : (delete b.refreshToken, delete b.refreshTokenParsed);
      e
        ? ((b.idToken = e), (b.idTokenParsed = d(e)))
        : (delete b.idToken, delete b.idTokenParsed);
      if (a) {
        if (
          ((b.token = a),
          (b.tokenParsed = d(a)),
          (b.sessionId = b.tokenParsed.session_state),
          (b.authenticated = !0),
          (b.subject = b.tokenParsed.sub),
          (b.realmAccess = b.tokenParsed.realm_access),
          (b.resourceAccess = b.tokenParsed.resource_access),
          f && (b.timeSkew = Math.floor(f / 1e3) - b.tokenParsed.iat),
          null != b.timeSkew &&
            (G(
              '[KEYCLOAK] Estimated time difference between browser and server is ' +
                b.timeSkew +
                ' seconds'
            ),
            b.onTokenExpired))
        )
          if (
            ((a =
              1e3 *
              (b.tokenParsed.exp - new Date().getTime() / 1e3 + b.timeSkew)),
            G('[KEYCLOAK] Token expires in ' + Math.round(a / 1e3) + ' s'),
            0 >= a)
          )
            b.onTokenExpired();
          else b.tokenTimeoutHandle = setTimeout(b.onTokenExpired, a);
      } else delete b.token, delete b.tokenParsed, delete b.subject, delete b.realmAccess, delete b.resourceAccess, (b.authenticated = !1);
    }
    function d(a) {
      a = a.split('.')[1];
      a = a.replace('/-/g', '+');
      a = a.replace('/_/g', '/');
      switch (a.length % 4) {
        case 0:
          break;
        case 2:
          a += '\x3d\x3d';
          break;
        case 3:
          a += '\x3d';
          break;
        default:
          throw 'Invalid token';
      }
      a = (a + '\x3d\x3d\x3d').slice(0, a.length + (a.length % 4));
      a = a.replace(/-/g, '+').replace(/_/g, '/');
      a = decodeURIComponent(escape(atob(a)));
      return (a = JSON.parse(a));
    }
    function c() {
      var a = p(36, '0123456789abcdef').split('');
      a[14] = '4';
      a[19] = '0123456789abcdef'.substr((a[19] & 3) | 8, 1);
      a[8] = a[13] = a[18] = a[23] = '-';
      return a.join('');
    }
    function f(a) {
      a: {
        var h;
        switch (b.flow) {
          case 'standard':
            h = ['code', 'state', 'session_state', 'kc_action_status'];
            break;
          case 'implicit':
            h = 'access_token token_type id_token state session_state expires_in kc_action_status'.split(
              ' '
            );
            break;
          case 'hybrid':
            h = 'access_token id_token code state session_state kc_action_status'.split(
              ' '
            );
        }
        h.push('error');
        h.push('error_description');
        h.push('error_uri');
        var c = a.indexOf('?'),
          d = a.indexOf('#'),
          e,
          v;
        'query' === b.responseMode && -1 !== c
          ? ((e = a.substring(0, c)),
            (v = r(a.substring(c + 1, -1 !== d ? d : a.length), h)),
            '' !== v.paramsString && (e += '?' + v.paramsString),
            -1 !== d && (e += a.substring(d)))
          : 'fragment' === b.responseMode &&
            -1 !== d &&
            ((e = a.substring(0, d)),
            (v = r(a.substring(d + 1), h)),
            '' !== v.paramsString && (e += '#' + v.paramsString));
        if (v && v.oauthParams)
          if ('standard' === b.flow || 'hybrid' === b.flow) {
            if (
              (v.oauthParams.code || v.oauthParams.error) &&
              v.oauthParams.state
            ) {
              v.oauthParams.newUrl = e;
              a = v.oauthParams;
              break a;
            }
          } else if (
            'implicit' === b.flow &&
            (v.oauthParams.access_token || v.oauthParams.error) &&
            v.oauthParams.state
          ) {
            v.oauthParams.newUrl = e;
            a = v.oauthParams;
            break a;
          }
        a = void 0;
      }
      if (a) {
        if ((h = M.get(a.state)))
          (a.valid = !0),
            (a.redirectUri = h.redirectUri),
            (a.storedNonce = h.nonce),
            (a.prompt = h.prompt),
            (a.pkceCodeVerifier = h.pkceCodeVerifier);
        return a;
      }
    }
    function r(a, b) {
      a = a.split('\x26');
      for (
        var h = { paramsString: '', oauthParams: {} }, c = 0;
        c < a.length;
        c++
      ) {
        var d = a[c].indexOf('\x3d'),
          e = a[c].slice(0, d);
        -1 !== b.indexOf(e)
          ? (h.oauthParams[e] = a[c].slice(d + 1))
          : ('' !== h.paramsString && (h.paramsString += '\x26'),
            (h.paramsString += a[c]));
      }
      return h;
    }
    function m() {
      var a = {
        setSuccess: function (b) {
          a.resolve(b);
        },
        setError: function (b) {
          a.reject(b);
        }
      };
      a.promise = new w(function (b, c) {
        a.resolve = b;
        a.reject = c;
      });
      return a;
    }
    function I() {
      var a = m();
      if (!e.enable || e.iframe) return a.setSuccess(), a.promise;
      var c = document.createElement('iframe');
      e.iframe = c;
      c.onload = function () {
        var c = b.endpoints.authorize();
        '/' === c.charAt(0)
          ? ((c = window.location.origin
              ? window.location.origin
              : window.location.protocol +
                '//' +
                window.location.hostname +
                (window.location.port ? ':' + window.location.port : '')),
            (e.iframeOrigin = c))
          : (e.iframeOrigin = c.substring(0, c.indexOf('/', 8)));
        a.setSuccess();
      };
      var d = b.endpoints.checkSessionIframe();
      c.setAttribute('src', d);
      c.setAttribute('title', 'keycloak-session-iframe');
      c.style.display = 'none';
      document.body.appendChild(c);
      window.addEventListener(
        'message',
        function (a) {
          if (
            a.origin === e.iframeOrigin &&
            e.iframe.contentWindow === a.source &&
            ('unchanged' == a.data || 'changed' == a.data || 'error' == a.data)
          ) {
            'unchanged' != a.data && b.clearToken();
            for (
              var c = e.callbackList.splice(0, e.callbackList.length),
                h = c.length - 1;
              0 <= h;
              --h
            ) {
              var d = c[h];
              'error' == a.data
                ? d.setError()
                : d.setSuccess('unchanged' == a.data);
            }
          }
        },
        !1
      );
      return a.promise;
    }
    function E() {
      e.enable &&
        b.token &&
        setTimeout(function () {
          F().then(function (a) {
            a && E();
          });
        }, 1e3 * e.interval);
    }
    function F() {
      var a = m();
      if (e.iframe && e.iframeOrigin) {
        var c = b.clientId + ' ' + (b.sessionId ? b.sessionId : '');
        e.callbackList.push(a);
        var d = e.iframeOrigin;
        1 == e.callbackList.length && e.iframe.contentWindow.postMessage(c, d);
      } else a.setSuccess();
      return a.promise;
    }
    function J(a) {
      if (!a || 'default' == a)
        return {
          login: function (a) {
            window.location.replace(b.createLoginUrl(a));
            return m().promise;
          },
          logout: function (a) {
            window.location.replace(b.createLogoutUrl(a));
            return m().promise;
          },
          register: function (a) {
            window.location.replace(b.createRegisterUrl(a));
            return m().promise;
          },
          accountManagement: function () {
            var a = b.createAccountUrl();
            if ('undefined' !== typeof a) window.location.href = a;
            else throw 'Not supported by the OIDC server';
            return m().promise;
          },
          redirectUri: function (a, c) {
            1 == arguments.length && (c = !0);
            return a && a.redirectUri
              ? a.redirectUri
              : b.redirectUri
              ? b.redirectUri
              : location.href;
          }
        };
      if ('cordova' == a) {
        e.enable = !1;
        var c = function (a, b, c) {
            return window.cordova && window.cordova.InAppBrowser
              ? window.cordova.InAppBrowser.open(a, b, c)
              : window.open(a, b, c);
          },
          h = function (a) {
            return a && a.cordovaOptions
              ? Object.keys(a.cordovaOptions).reduce(function (b, c) {
                  b[c] = a.cordovaOptions[c];
                  return b;
                }, {})
              : {};
          },
          d = function (a) {
            return Object.keys(a)
              .reduce(function (b, c) {
                b.push(c + '\x3d' + a[c]);
                return b;
              }, [])
              .join(',');
          },
          g = function (a) {
            var b = h(a);
            b.location = 'no';
            a && 'none' == a.prompt && (b.hidden = 'yes');
            return d(b);
          };
        return {
          login: function (a) {
            var h = m(),
              d = g(a);
            a = b.createLoginUrl(a);
            var e = c(a, '_blank', d),
              t = !1,
              v = !1;
            e.addEventListener('loadstart', function (a) {
              0 == a.url.indexOf('http://localhost') &&
                ((a = f(a.url)), u(a, h), (v = !0), e.close(), (t = !0));
            });
            e.addEventListener('loaderror', function (a) {
              t ||
                (0 == a.url.indexOf('http://localhost')
                  ? ((a = f(a.url)), u(a, h), (v = !0), e.close(), (t = !0))
                  : (h.setError(), (v = !0), e.close()));
            });
            e.addEventListener('exit', function (a) {
              v || h.setError({ reason: 'closed_by_user' });
            });
            return h.promise;
          },
          logout: function (a) {
            var h = m();
            a = b.createLogoutUrl(a);
            var d = c(a, '_blank', 'location\x3dno,hidden\x3dyes'),
              e;
            d.addEventListener('loadstart', function (a) {
              0 == a.url.indexOf('http://localhost') && d.close();
            });
            d.addEventListener('loaderror', function (a) {
              0 != a.url.indexOf('http://localhost') && (e = !0);
              d.close();
            });
            d.addEventListener('exit', function (a) {
              e ? h.setError() : (b.clearToken(), h.setSuccess());
            });
            return h.promise;
          },
          register: function (a) {
            var h = m(),
              d = b.createRegisterUrl();
            a = g(a);
            var e = c(d, '_blank', a);
            e.addEventListener('loadstart', function (a) {
              0 == a.url.indexOf('http://localhost') &&
                (e.close(), (a = f(a.url)), u(a, h));
            });
            return h.promise;
          },
          accountManagement: function () {
            var a = b.createAccountUrl();
            if ('undefined' !== typeof a) {
              var h = c(a, '_blank', 'location\x3dno');
              h.addEventListener('loadstart', function (a) {
                0 == a.url.indexOf('http://localhost') && h.close();
              });
            } else throw 'Not supported by the OIDC server';
          },
          redirectUri: function (a) {
            return 'http://localhost';
          }
        };
      }
      if ('cordova-native' == a)
        return (
          (e.enable = !1),
          {
            login: function (a) {
              var c = m();
              a = b.createLoginUrl(a);
              universalLinks.subscribe('keycloak', function (a) {
                universalLinks.unsubscribe('keycloak');
                window.cordova.plugins.browsertab.close();
                a = f(a.url);
                u(a, c);
              });
              window.cordova.plugins.browsertab.openUrl(a);
              return c.promise;
            },
            logout: function (a) {
              var c = m();
              a = b.createLogoutUrl(a);
              universalLinks.subscribe('keycloak', function (a) {
                universalLinks.unsubscribe('keycloak');
                window.cordova.plugins.browsertab.close();
                b.clearToken();
                c.setSuccess();
              });
              window.cordova.plugins.browsertab.openUrl(a);
              return c.promise;
            },
            register: function (a) {
              var c = m();
              a = b.createRegisterUrl(a);
              universalLinks.subscribe('keycloak', function (a) {
                universalLinks.unsubscribe('keycloak');
                window.cordova.plugins.browsertab.close();
                a = f(a.url);
                u(a, c);
              });
              window.cordova.plugins.browsertab.openUrl(a);
              return c.promise;
            },
            accountManagement: function () {
              var a = b.createAccountUrl();
              if ('undefined' !== typeof a)
                window.cordova.plugins.browsertab.openUrl(a);
              else throw 'Not supported by the OIDC server';
            },
            redirectUri: function (a) {
              return a && a.redirectUri
                ? a.redirectUri
                : b.redirectUri
                ? b.redirectUri
                : 'http://localhost';
            }
          }
        );
      throw 'invalid adapter type: ' + a;
    }
    function B(a) {
      return function () {
        b.enableLogging &&
          a.apply(console, Array.prototype.slice.call(arguments));
      };
    }
    if (!(this instanceof l)) return new l(n);
    for (
      var b = this,
        x,
        z = [],
        M,
        e = { enable: !0, callbackList: [], interval: 5 },
        H = document.getElementsByTagName('script'),
        k = 0;
      k < H.length;
      k++
    )
      (-1 === H[k].src.indexOf('keycloak.js') &&
        -1 === H[k].src.indexOf('keycloak.min.js')) ||
        -1 === H[k].src.indexOf('version\x3d') ||
        (b.iframeVersion = H[k].src
          .substring(H[k].src.indexOf('version\x3d') + 8)
          .split('\x26')[0]);
    var N = !0,
      G = B(console.info),
      R = B(console.warn);
    b.init = function (c) {
      function d() {
        var a = function (a) {
            a || (d.prompt = 'none');
            b.login(d)
              .then(function () {
                l.setSuccess();
              })
              .catch(function () {
                l.setError();
              });
          },
          h = function () {
            var a = document.createElement('iframe'),
              c = b.createLoginUrl({
                prompt: 'none',
                redirectUri: b.silentCheckSsoRedirectUri
              });
            a.setAttribute('src', c);
            a.setAttribute('title', 'keycloak-silent-check-sso');
            a.style.display = 'none';
            document.body.appendChild(a);
            var h = function (b) {
              b.origin === window.location.origin &&
                a.contentWindow === b.source &&
                ((b = f(b.data)),
                u(b, l),
                document.body.removeChild(a),
                window.removeEventListener('message', h));
            };
            window.addEventListener('message', h);
          },
          d = {};
        switch (c.onLoad) {
          case 'check-sso':
            e.enable
              ? I().then(function () {
                  F()
                    .then(function (c) {
                      c
                        ? l.setSuccess()
                        : b.silentCheckSsoRedirectUri
                        ? h()
                        : a(!1);
                    })
                    .catch(function () {
                      l.setError();
                    });
                })
              : b.silentCheckSsoRedirectUri
              ? h()
              : a(!1);
            break;
          case 'login-required':
            a(!0);
            break;
          default:
            throw 'Invalid value for onLoad';
        }
      }
      b.authenticated = !1;
      a: {
        try {
          M = new O();
          break a;
        } catch (v) {}
        M = new P();
      }
      var h = ['default', 'cordova', 'cordova-native'];
      x =
        c && -1 < h.indexOf(c.adapter)
          ? J(c.adapter)
          : c && 'object' === typeof c.adapter
          ? c.adapter
          : window.Cordova || window.cordova
          ? J('cordova')
          : J();
      if (c) {
        'undefined' !== typeof c.useNonce && (N = c.useNonce);
        'undefined' !== typeof c.checkLoginIframe &&
          (e.enable = c.checkLoginIframe);
        c.checkLoginIframeInterval && (e.interval = c.checkLoginIframeInterval);
        'login-required' === c.onLoad && (b.loginRequired = !0);
        if (c.responseMode)
          if ('query' === c.responseMode || 'fragment' === c.responseMode)
            b.responseMode = c.responseMode;
          else throw 'Invalid value for responseMode';
        if (c.flow) {
          switch (c.flow) {
            case 'standard':
              b.responseType = 'code';
              break;
            case 'implicit':
              b.responseType = 'id_token token';
              break;
            case 'hybrid':
              b.responseType = 'code id_token token';
              break;
            default:
              throw 'Invalid value for flow';
          }
          b.flow = c.flow;
        }
        null != c.timeSkew && (b.timeSkew = c.timeSkew);
        c.redirectUri && (b.redirectUri = c.redirectUri);
        c.silentCheckSsoRedirectUri &&
          (b.silentCheckSsoRedirectUri = c.silentCheckSsoRedirectUri);
        if (c.pkceMethod) {
          if ('S256' !== c.pkceMethod) throw 'Invalid value for pkceMethod';
          b.pkceMethod = c.pkceMethod;
        }
        b.enableLogging =
          'boolean' === typeof c.enableLogging ? c.enableLogging : !1;
      }
      b.responseMode || (b.responseMode = 'fragment');
      b.responseType || ((b.responseType = 'code'), (b.flow = 'standard'));
      var k = m(),
        l = m();
      l.promise
        .then(function () {
          b.onReady && b.onReady(b.authenticated);
          k.setSuccess(b.authenticated);
        })
        .catch(function (a) {
          k.setError(a);
        });
      h = a(n);
      h.then(function () {
        var a = f(window.location.href);
        a && window.history.replaceState(window.history.state, null, a.newUrl);
        if (a && a.valid)
          return I()
            .then(function () {
              u(a, l);
            })
            .catch(function (a) {
              l.setError();
            });
        c
          ? c.token && c.refreshToken
            ? (g(c.token, c.refreshToken, c.idToken),
              e.enable
                ? I().then(function () {
                    F()
                      .then(function (a) {
                        a
                          ? (b.onAuthSuccess && b.onAuthSuccess(),
                            l.setSuccess(),
                            E())
                          : l.setSuccess();
                      })
                      .catch(function () {
                        l.setError();
                      });
                  })
                : b
                    .updateToken(-1)
                    .then(function () {
                      b.onAuthSuccess && b.onAuthSuccess();
                      l.setSuccess();
                    })
                    .catch(function () {
                      b.onAuthError && b.onAuthError();
                      c.onLoad ? d() : l.setError();
                    }))
            : c.onLoad
            ? d()
            : l.setSuccess()
          : l.setSuccess();
      });
      h.catch(function () {
        k.setError();
      });
      return k.promise;
    };
    b.login = function (a) {
      return x.login(a);
    };
    b.createLoginUrl = function (a) {
      var d = c(),
        e = c(),
        h = x.redirectUri(a),
        f = { state: d, nonce: e, redirectUri: encodeURIComponent(h) };
      a && a.prompt && (f.prompt = a.prompt);
      var g;
      g =
        a && 'register' == a.action
          ? b.endpoints.register()
          : b.endpoints.authorize();
      var k;
      k =
        a && a.scope
          ? -1 != a.scope.indexOf('openid')
            ? a.scope
            : 'openid ' + a.scope
          : 'openid';
      d =
        g +
        '?client_id\x3d' +
        encodeURIComponent(b.clientId) +
        '\x26redirect_uri\x3d' +
        encodeURIComponent(h) +
        '\x26state\x3d' +
        encodeURIComponent(d) +
        '\x26response_mode\x3d' +
        encodeURIComponent(b.responseMode) +
        '\x26response_type\x3d' +
        encodeURIComponent(b.responseType) +
        '\x26scope\x3d' +
        encodeURIComponent(k);
      N && (d = d + '\x26nonce\x3d' + encodeURIComponent(e));
      a && a.prompt && (d += '\x26prompt\x3d' + encodeURIComponent(a.prompt));
      a && a.maxAge && (d += '\x26max_age\x3d' + encodeURIComponent(a.maxAge));
      a &&
        a.loginHint &&
        (d += '\x26login_hint\x3d' + encodeURIComponent(a.loginHint));
      a &&
        a.idpHint &&
        (d += '\x26kc_idp_hint\x3d' + encodeURIComponent(a.idpHint));
      a &&
        a.action &&
        'register' != a.action &&
        (d += '\x26kc_action\x3d' + encodeURIComponent(a.action));
      a &&
        a.locale &&
        (d += '\x26ui_locales\x3d' + encodeURIComponent(a.locale));
      if (b.pkceMethod) {
        a = p(
          96,
          'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        );
        f.pkceCodeVerifier = a;
        a: switch (b.pkceMethod) {
          case 'S256':
            a = new Uint8Array(K.arrayBuffer(a));
            a = L.fromByteArray(a)
              .replace(/\+/g, '-')
              .replace(/\//g, '_')
              .replace(/\=/g, '');
            break a;
          default:
            throw 'Invalid value for pkceMethod';
        }
        d =
          d +
          ('\x26code_challenge\x3d' + a) +
          ('\x26code_challenge_method\x3d' + b.pkceMethod);
      }
      M.add(f);
      return d;
    };
    b.logout = function (a) {
      return x.logout(a);
    };
    b.createLogoutUrl = function (a) {
      return (
        b.endpoints.logout() +
        '?redirect_uri\x3d' +
        encodeURIComponent(x.redirectUri(a, !1))
      );
    };
    b.register = function (a) {
      return x.register(a);
    };
    b.createRegisterUrl = function (a) {
      a || (a = {});
      a.action = 'register';
      return b.createLoginUrl(a);
    };
    b.createAccountUrl = function (a) {
      var c = q(),
        d = void 0;
      'undefined' !== typeof c &&
        (d =
          c +
          '/account?referrer\x3d' +
          encodeURIComponent(b.clientId) +
          '\x26referrer_uri\x3d' +
          encodeURIComponent(x.redirectUri(a)));
      return d;
    };
    b.accountManagement = function () {
      return x.accountManagement();
    };
    b.hasRealmRole = function (a) {
      var c = b.realmAccess;
      return !!c && 0 <= c.roles.indexOf(a);
    };
    b.hasResourceRole = function (a, c) {
      if (!b.resourceAccess) return !1;
      c = b.resourceAccess[c || b.clientId];
      return !!c && 0 <= c.roles.indexOf(a);
    };
    b.loadUserProfile = function () {
      var a = q() + '/account',
        c = new XMLHttpRequest();
      c.open('GET', a, !0);
      c.setRequestHeader('Accept', 'application/json');
      c.setRequestHeader('Authorization', 'bearer ' + b.token);
      var d = m();
      c.onreadystatechange = function () {
        4 == c.readyState &&
          (200 == c.status
            ? ((b.profile = JSON.parse(c.responseText)),
              d.setSuccess(b.profile))
            : d.setError());
      };
      c.send();
      return d.promise;
    };
    b.loadUserInfo = function () {
      var a = b.endpoints.userinfo(),
        c = new XMLHttpRequest();
      c.open('GET', a, !0);
      c.setRequestHeader('Accept', 'application/json');
      c.setRequestHeader('Authorization', 'bearer ' + b.token);
      var d = m();
      c.onreadystatechange = function () {
        4 == c.readyState &&
          (200 == c.status
            ? ((b.userInfo = JSON.parse(c.responseText)),
              d.setSuccess(b.userInfo))
            : d.setError());
      };
      c.send();
      return d.promise;
    };
    b.isTokenExpired = function (a) {
      if (!b.tokenParsed || (!b.refreshToken && 'implicit' != b.flow))
        throw 'Not authenticated';
      if (null == b.timeSkew)
        return (
          G(
            '[KEYCLOAK] Unable to determine if token is expired as timeskew is not set'
          ),
          !0
        );
      var c =
        b.tokenParsed.exp - Math.ceil(new Date().getTime() / 1e3) + b.timeSkew;
      if (a) {
        if (isNaN(a)) throw 'Invalid minValidity';
        c -= a;
      }
      return 0 > c;
    };
    b.updateToken = function (a) {
      var c = m();
      if (!b.refreshToken) return c.setError(), c.promise;
      a = a || 5;
      var d = function () {
        var d = !1;
        if (-1 == a) (d = !0), G('[KEYCLOAK] Refreshing token: forced refresh');
        else if (!b.tokenParsed || b.isTokenExpired(a))
          (d = !0), G('[KEYCLOAK] Refreshing token: token expired');
        if (d) {
          var d =
              'grant_type\x3drefresh_token\x26refresh_token\x3d' +
              b.refreshToken,
            e = b.endpoints.token();
          z.push(c);
          if (1 == z.length) {
            var f = new XMLHttpRequest();
            f.open('POST', e, !0);
            f.setRequestHeader(
              'Content-type',
              'application/x-www-form-urlencoded'
            );
            f.withCredentials = !0;
            var d = d + ('\x26client_id\x3d' + encodeURIComponent(b.clientId)),
              h = new Date().getTime();
            f.onreadystatechange = function () {
              if (4 == f.readyState)
                if (200 == f.status) {
                  G('[KEYCLOAK] Token refreshed');
                  h = (h + new Date().getTime()) / 2;
                  var a = JSON.parse(f.responseText);
                  g(a.access_token, a.refresh_token, a.id_token, h);
                  b.onAuthRefreshSuccess && b.onAuthRefreshSuccess();
                  for (a = z.pop(); null != a; a = z.pop()) a.setSuccess(!0);
                } else
                  for (
                    R('[KEYCLOAK] Failed to refresh token'),
                      400 == f.status && b.clearToken(),
                      b.onAuthRefreshError && b.onAuthRefreshError(),
                      a = z.pop();
                    null != a;
                    a = z.pop()
                  )
                    a.setError(!0);
            };
            f.send(d);
          }
        } else c.setSuccess(!1);
      };
      e.enable
        ? F()
            .then(function () {
              d();
            })
            .catch(function () {
              c.setError();
            })
        : d();
      return c.promise;
    };
    b.clearToken = function () {
      b.token &&
        (g(null, null, null),
        b.onAuthLogout && b.onAuthLogout(),
        b.loginRequired && b.login());
    };
    var O = function () {
        function a() {
          for (
            var a = new Date().getTime(), b = 0;
            b < localStorage.length;
            b++
          ) {
            var c = localStorage.key(b);
            if (c && 0 == c.indexOf('kc-callback-')) {
              var d = localStorage.getItem(c);
              if (d)
                try {
                  var e = JSON.parse(d).expires;
                  (!e || e < a) && localStorage.removeItem(c);
                } catch (S) {
                  localStorage.removeItem(c);
                }
            }
          }
        }
        if (!(this instanceof O)) return new O();
        localStorage.setItem('kc-test', 'test');
        localStorage.removeItem('kc-test');
        this.get = function (b) {
          if (b) {
            b = 'kc-callback-' + b;
            var c = localStorage.getItem(b);
            c && (localStorage.removeItem(b), (c = JSON.parse(c)));
            a();
            return c;
          }
        };
        this.add = function (b) {
          a();
          var c = 'kc-callback-' + b.state;
          b.expires = new Date().getTime() + 36e5;
          localStorage.setItem(c, JSON.stringify(b));
        };
      },
      P = function () {
        if (!(this instanceof P)) return new P();
        this.get = function (c) {
          if (c) {
            var d;
            a: {
              d = 'kc-callback-' + c + '\x3d';
              for (
                var e = document.cookie.split(';'), f = 0;
                f < e.length;
                f++
              ) {
                for (var g = e[f]; ' ' == g.charAt(0); ) g = g.substring(1);
                if (0 == g.indexOf(d)) {
                  d = g.substring(d.length, g.length);
                  break a;
                }
              }
              d = '';
            }
            b('kc-callback-' + c, '', a(-100));
            if (d) return JSON.parse(d);
          }
        };
        this.add = function (c) {
          b('kc-callback-' + c.state, JSON.stringify(c), a(60));
        };
        this.removeItem = function (c) {
          b(c, '', a(-100));
        };
        var a = function (a) {
            var b = new Date();
            b.setTime(b.getTime() + 6e4 * a);
            return b;
          },
          b = function (a, b, c) {
            a = a + '\x3d' + b + '; expires\x3d' + c.toUTCString() + '; ';
            document.cookie = a;
          };
      };
  }
  if ('undefined' === typeof Promise)
    throw Error(
      'Keycloak requires an environment that supports Promises. Make sure that you include the appropriate polyfill.'
    );
  var u = !1;
  w.prototype = Object.create(Promise.prototype);
  w.prototype.constructor = w;
  w.prototype.success = function (l) {
    E();
    var n = this.then(function (n) {
      l(n);
    });
    return p(n);
  };
  w.prototype.error = function (l) {
    E();
    var n = this.catch(function (n) {
      l(n);
    });
    return p(n);
  };
  return l;
});
//# sourceMappingURL=keycloak.min.js.map
