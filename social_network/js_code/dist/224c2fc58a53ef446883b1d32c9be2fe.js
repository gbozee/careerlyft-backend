// modules are defined as an array
// [ module function, map of requires ]
//
// map of requires is short require name -> numeric require
//
// anything defined in a previous bundle is accessed via the
// orig method which is the require for previous bundles

// eslint-disable-next-line no-global-assign
require = (function (modules, cache, entry) {
  // Save the require from previous bundle to this closure if any
  var previousRequire = typeof require === "function" && require;

  function newRequire(name, jumped) {
    if (!cache[name]) {
      if (!modules[name]) {
        // if we cannot find the module within our internal map or
        // cache jump to the current global require ie. the last bundle
        // that was added to the page.
        var currentRequire = typeof require === "function" && require;
        if (!jumped && currentRequire) {
          return currentRequire(name, true);
        }

        // If there are other bundles on this page the require from the
        // previous one is saved to 'previousRequire'. Repeat this as
        // many times as there are bundles until the module is found or
        // we exhaust the require chain.
        if (previousRequire) {
          return previousRequire(name, true);
        }

        var err = new Error('Cannot find module \'' + name + '\'');
        err.code = 'MODULE_NOT_FOUND';
        throw err;
      }

      localRequire.resolve = resolve;

      var module = cache[name] = new newRequire.Module(name);

      modules[name][0].call(module.exports, localRequire, module, module.exports);
    }

    return cache[name].exports;

    function localRequire(x){
      return newRequire(localRequire.resolve(x));
    }

    function resolve(x){
      return modules[name][1][x] || x;
    }
  }

  function Module(moduleName) {
    this.id = moduleName;
    this.bundle = newRequire;
    this.exports = {};
  }

  newRequire.isParcelRequire = true;
  newRequire.Module = Module;
  newRequire.modules = modules;
  newRequire.cache = cache;
  newRequire.parent = previousRequire;

  for (var i = 0; i < entry.length; i++) {
    newRequire(entry[i]);
  }

  // Override the current require with this new one
  return newRequire;
})({6:[function(require,module,exports) {

// shim for using process in browser
var process = module.exports = {};

// cached from whatever global is present so that test runners that stub it
// don't break things.  But we need to wrap it in a try catch in case it is
// wrapped in strict mode code which doesn't define any globals.  It's inside a
// function because try/catches deoptimize in certain engines.

var cachedSetTimeout;
var cachedClearTimeout;

function defaultSetTimout() {
    throw new Error('setTimeout has not been defined');
}
function defaultClearTimeout () {
    throw new Error('clearTimeout has not been defined');
}
(function () {
    try {
        if (typeof setTimeout === 'function') {
            cachedSetTimeout = setTimeout;
        } else {
            cachedSetTimeout = defaultSetTimout;
        }
    } catch (e) {
        cachedSetTimeout = defaultSetTimout;
    }
    try {
        if (typeof clearTimeout === 'function') {
            cachedClearTimeout = clearTimeout;
        } else {
            cachedClearTimeout = defaultClearTimeout;
        }
    } catch (e) {
        cachedClearTimeout = defaultClearTimeout;
    }
} ())
function runTimeout(fun) {
    if (cachedSetTimeout === setTimeout) {
        //normal enviroments in sane situations
        return setTimeout(fun, 0);
    }
    // if setTimeout wasn't available but was latter defined
    if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
        cachedSetTimeout = setTimeout;
        return setTimeout(fun, 0);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedSetTimeout(fun, 0);
    } catch(e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
            return cachedSetTimeout.call(null, fun, 0);
        } catch(e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
            return cachedSetTimeout.call(this, fun, 0);
        }
    }


}
function runClearTimeout(marker) {
    if (cachedClearTimeout === clearTimeout) {
        //normal enviroments in sane situations
        return clearTimeout(marker);
    }
    // if clearTimeout wasn't available but was latter defined
    if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
        cachedClearTimeout = clearTimeout;
        return clearTimeout(marker);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedClearTimeout(marker);
    } catch (e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
            return cachedClearTimeout.call(null, marker);
        } catch (e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
            // Some versions of I.E. have different rules for clearTimeout vs setTimeout
            return cachedClearTimeout.call(this, marker);
        }
    }



}
var queue = [];
var draining = false;
var currentQueue;
var queueIndex = -1;

function cleanUpNextTick() {
    if (!draining || !currentQueue) {
        return;
    }
    draining = false;
    if (currentQueue.length) {
        queue = currentQueue.concat(queue);
    } else {
        queueIndex = -1;
    }
    if (queue.length) {
        drainQueue();
    }
}

function drainQueue() {
    if (draining) {
        return;
    }
    var timeout = runTimeout(cleanUpNextTick);
    draining = true;

    var len = queue.length;
    while(len) {
        currentQueue = queue;
        queue = [];
        while (++queueIndex < len) {
            if (currentQueue) {
                currentQueue[queueIndex].run();
            }
        }
        queueIndex = -1;
        len = queue.length;
    }
    currentQueue = null;
    draining = false;
    runClearTimeout(timeout);
}

process.nextTick = function (fun) {
    var args = new Array(arguments.length - 1);
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            args[i - 1] = arguments[i];
        }
    }
    queue.push(new Item(fun, args));
    if (queue.length === 1 && !draining) {
        runTimeout(drainQueue);
    }
};

// v8 likes predictible objects
function Item(fun, array) {
    this.fun = fun;
    this.array = array;
}
Item.prototype.run = function () {
    this.fun.apply(null, this.array);
};
process.title = 'browser';
process.browser = true;
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues
process.versions = {};

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;
process.prependListener = noop;
process.prependOnceListener = noop;

process.listeners = function (name) { return [] }

process.binding = function (name) {
    throw new Error('process.binding is not supported');
};

process.cwd = function () { return '/' };
process.chdir = function (dir) {
    throw new Error('process.chdir is not supported');
};
process.umask = function() { return 0; };

},{}],5:[function(require,module,exports) {
var process = require("process");
var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*! hellojs v1.16.1 | (c) 2012-2017 Andrew Dodson | MIT https://adodson.com/hello.js/LICENSE */
Object.create || (Object.create = function () {
  function e() {}return function (t) {
    if (1 != arguments.length) throw new Error("Object.create implementation only accepts one parameter.");return e.prototype = t, new e();
  };
}()), Object.keys || (Object.keys = function (e, t, n) {
  n = [];for (t in e) {
    n.hasOwnProperty.call(e, t) && n.push(t);
  }return n;
}), Array.prototype.indexOf || (Array.prototype.indexOf = function (e) {
  for (var t = 0; t < this.length; t++) {
    if (this[t] === e) return t;
  }return -1;
}), Array.prototype.forEach || (Array.prototype.forEach = function (e) {
  if (void 0 === this || null === this) throw new TypeError();var t = Object(this),
      n = t.length >>> 0;if ("function" != typeof e) throw new TypeError();for (var i = arguments.length >= 2 ? arguments[1] : void 0, o = 0; o < n; o++) {
    o in t && e.call(i, t[o], o, t);
  }return this;
}), Array.prototype.filter || (Array.prototype.filter = function (e, t) {
  var n = [];return this.forEach(function (i, o, a) {
    e.call(t || void 0, i, o, a) && n.push(i);
  }), n;
}), Array.prototype.map || (Array.prototype.map = function (e, t) {
  var n = [];return this.forEach(function (i, o, a) {
    n.push(e.call(t || void 0, i, o, a));
  }), n;
}), Array.isArray || (Array.isArray = function (e) {
  return "[object Array]" === Object.prototype.toString.call(e);
}), "object" != (typeof window === "undefined" ? "undefined" : _typeof(window)) || "object" != _typeof(window.location) || window.location.assign || (window.location.assign = function (e) {
  window.location = e;
}), Function.prototype.bind || (Function.prototype.bind = function (e) {
  function t() {}if ("function" != typeof this) throw new TypeError("Function.prototype.bind - what is trying to be bound is not callable");var n = [].slice,
      i = n.call(arguments, 1),
      o = this,
      a = function a() {
    return o.apply(this instanceof t ? this : e || window, i.concat(n.call(arguments)));
  };return t.prototype = this.prototype, a.prototype = new t(), a;
});var hello = function hello(e) {
  return hello.use(e);
};hello.utils = { extend: function extend(e) {
    return Array.prototype.slice.call(arguments, 1).forEach(function (t) {
      if (Array.isArray(e) && Array.isArray(t)) Array.prototype.push.apply(e, t);else if (e && (e instanceof Object || "object" == (typeof e === "undefined" ? "undefined" : _typeof(e))) && t && (t instanceof Object || "object" == (typeof t === "undefined" ? "undefined" : _typeof(t))) && e !== t) for (var n in t) {
        e[n] = hello.utils.extend(e[n], t[n]);
      } else Array.isArray(t) && (t = t.slice(0)), e = t;
    }), e;
  } }, hello.utils.extend(hello, { settings: { redirect_uri: window.location.href.split("#")[0], response_type: "token", display: "popup", state: "", oauth_proxy: "https://auth-server.herokuapp.com/proxy", timeout: 2e4, popup: { resizable: 1, scrollbars: 1, width: 500, height: 550 }, scope: ["basic"], scope_map: { basic: "" }, default_service: null, force: null, page_uri: window.location.href }, services: {}, use: function use(e) {
    var t = Object.create(this);return t.settings = Object.create(this.settings), e && (t.settings.default_service = e), t.utils.Event.call(t), t;
  }, init: function init(e, t) {
    var n = this.utils;if (!e) return this.services;for (var i in e) {
      e.hasOwnProperty(i) && "object" != _typeof(e[i]) && (e[i] = { id: e[i] });
    }return n.extend(this.services, e), t && (n.extend(this.settings, t), "redirect_uri" in t && (this.settings.redirect_uri = n.url(t.redirect_uri).href)), this;
  }, login: function login() {
    function e(e, t) {
      hello.emit(e, t);
    }function t(e) {
      return e;
    }function n(e) {
      return !!e;
    }var i,
        o = this.utils,
        a = o.error,
        r = o.Promise(),
        s = o.args({ network: "s", options: "o", callback: "f" }, arguments),
        l = o.diffKey(s.options, this.settings),
        u = s.options = o.merge(this.settings, s.options || {});if (u.popup = o.merge(this.settings.popup, s.options.popup || {}), s.network = s.network || this.settings.default_service, r.proxy.then(s.callback, s.callback), r.proxy.then(e.bind(this, "auth.login auth"), e.bind(this, "auth.failed auth")), "string" != typeof s.network || !(s.network in this.services)) return r.reject(a("invalid_network", "The provided network was not recognized"));var c = this.services[s.network],
        f = o.globalEvent(function (e) {
      var t;(t = e ? JSON.parse(e) : a("cancelled", "The authentication was not completed")).error ? r.reject(t) : (o.store(t.network, t), r.fulfill({ network: t.network, authResponse: t }));
    }),
        d = o.url(u.redirect_uri).href,
        p = c.oauth.response_type || u.response_type;/\bcode\b/.test(p) && !c.oauth.grant && (p = p.replace(/\bcode\b/, "token")), s.qs = o.merge(l, { client_id: encodeURIComponent(c.id), response_type: encodeURIComponent(p), redirect_uri: encodeURIComponent(d), state: { client_id: c.id, network: s.network, display: u.display, callback: f, state: u.state, redirect_uri: d } });var h = o.store(s.network),
        m = /[,\s]+/,
        g = this.settings.scope ? [this.settings.scope.toString()] : [],
        v = o.merge(this.settings.scope_map, c.scope || {});if (u.scope && g.push(u.scope.toString()), h && "scope" in h && h.scope instanceof String && g.push(h.scope), g = g.join(",").split(m), g = o.unique(g).filter(n), s.qs.state.scope = g.join(","), g = g.map(function (e) {
      return e in v ? v[e] : e;
    }), g = g.join(",").split(m), g = o.unique(g).filter(n), s.qs.scope = g.join(c.scope_delim || ","), !1 === u.force && h && "access_token" in h && h.access_token && "expires" in h && h.expires > new Date().getTime() / 1e3) {
      if (0 === o.diff((h.scope || "").split(m), (s.qs.state.scope || "").split(m)).length) return r.fulfill({ unchanged: !0, network: s.network, authResponse: h }), r;
    }if ("page" === u.display && u.page_uri && (s.qs.state.page_uri = o.url(u.page_uri).href), "login" in c && "function" == typeof c.login && c.login(s), (!/\btoken\b/.test(p) || parseInt(c.oauth.version, 10) < 2 || "none" === u.display && c.oauth.grant && h && h.refresh_token) && (s.qs.state.oauth = c.oauth, s.qs.state.oauth_proxy = u.oauth_proxy), s.qs.state = encodeURIComponent(JSON.stringify(s.qs.state)), 1 === parseInt(c.oauth.version, 10) ? i = o.qs(u.oauth_proxy, s.qs, t) : "none" === u.display && c.oauth.grant && h && h.refresh_token ? (s.qs.refresh_token = h.refresh_token, i = o.qs(u.oauth_proxy, s.qs, t)) : i = o.qs(c.oauth.auth, s.qs, t), e("auth.init", s), "none" === u.display) o.iframe(i, d);else if ("popup" === u.display) var y = o.popup(i, d, u.popup),
        w = setInterval(function () {
      if ((!y || y.closed) && (clearInterval(w), !r.state)) {
        var e = a("cancelled", "Login has been cancelled");y || (e = a("blocked", "Popup was blocked")), e.network = s.network, r.reject(e);
      }
    }, 100);else window.location = i;return r.proxy;
  }, logout: function logout() {
    function e(e, t) {
      hello.emit(e, t);
    }var t = this.utils,
        n = t.error,
        i = t.Promise(),
        o = t.args({ name: "s", options: "o", callback: "f" }, arguments);if (o.options = o.options || {}, i.proxy.then(o.callback, o.callback), i.proxy.then(e.bind(this, "auth.logout auth"), e.bind(this, "error")), o.name = o.name || this.settings.default_service, o.authResponse = t.store(o.name), !o.name || o.name in this.services) {
      if (o.name && o.authResponse) {
        var a = function a(e) {
          t.store(o.name, null), i.fulfill(hello.utils.merge({ network: o.name }, e || {}));
        },
            r = {};if (o.options.force) {
          var s = this.services[o.name].logout;if (s) if ("function" == typeof s && (s = s(a, o)), "string" == typeof s) t.iframe(s), r.force = null, r.message = "Logout success on providers site was indeterminate";else if (void 0 === s) return i.proxy;
        }a(r);
      } else i.reject(n("invalid_session", "There was no session to remove"));
    } else i.reject(n("invalid_network", "The network was unrecognized"));return i.proxy;
  }, getAuthResponse: function getAuthResponse(e) {
    return (e = e || this.settings.default_service) && e in this.services ? this.utils.store(e) || null : null;
  }, events: {} }), hello.utils.extend(hello.utils, { error: function error(e, t) {
    return { error: { code: e, message: t } };
  }, qs: function qs(e, t, n) {
    if (t) {
      n = n || encodeURIComponent;for (var i in t) {
        var o = "([\\?\\&])" + i + "=[^\\&]*",
            a = new RegExp(o);e.match(a) && (e = e.replace(a, "$1" + i + "=" + n(t[i])), delete t[i]);
      }
    }return this.isEmpty(t) ? e : e + (e.indexOf("?") > -1 ? "&" : "?") + this.param(t, n);
  }, param: function param(e, t) {
    var n,
        i,
        o = {};if ("string" == typeof e) {
      if (t = t || decodeURIComponent, i = e.replace(/^[\#\?]/, "").match(/([^=\/\&]+)=([^\&]+)/g)) for (var a = 0; a < i.length; a++) {
        o[(n = i[a].match(/([^=]+)=(.*)/))[1]] = t(n[2]);
      }return o;
    }t = t || encodeURIComponent;var r = e;o = [];for (var s in r) {
      r.hasOwnProperty(s) && r.hasOwnProperty(s) && o.push([s, "?" === r[s] ? "?" : t(r[s])].join("="));
    }return o.join("&");
  }, store: function () {
    for (var e, t = ["localStorage", "sessionStorage"], n = -1; t[++n];) {
      try {
        (e = window[t[n]]).setItem("test" + n, n), e.removeItem("test" + n);break;
      } catch (t) {
        e = null;
      }
    }if (!e) {
      var i = null;e = { getItem: function getItem(e) {
          e += "=";for (var t = document.cookie.split(";"), n = 0; n < t.length; n++) {
            var o = t[n].replace(/(^\s+|\s+$)/, "");if (o && 0 === o.indexOf(e)) return o.substr(e.length);
          }return i;
        }, setItem: function setItem(e, t) {
          i = t, document.cookie = e + "=" + t;
        } }, i = e.getItem("hello");
    }return function (t, n, i) {
      var o = function () {
        var t = {};try {
          t = JSON.parse(e.getItem("hello")) || {};
        } catch (e) {}return t;
      }();if (t && void 0 === n) return o[t] || null;if (t && null === n) try {
        delete o[t];
      } catch (e) {
        o[t] = null;
      } else {
        if (!t) return o;o[t] = n;
      }return function (t) {
        e.setItem("hello", JSON.stringify(t));
      }(o), o || null;
    };
  }(), append: function append(e, t, n) {
    var i = "string" == typeof e ? document.createElement(e) : e;if ("object" == (typeof t === "undefined" ? "undefined" : _typeof(t))) if ("tagName" in t) n = t;else for (var o in t) {
      if (t.hasOwnProperty(o)) if ("object" == _typeof(t[o])) for (var a in t[o]) {
        t[o].hasOwnProperty(a) && (i[o][a] = t[o][a]);
      } else "html" === o ? i.innerHTML = t[o] : /^on/.test(o) ? i[o] = t[o] : i.setAttribute(o, t[o]);
    }return "body" === n ? function e() {
      document.body ? document.body.appendChild(i) : setTimeout(e, 16);
    }() : "object" == (typeof n === "undefined" ? "undefined" : _typeof(n)) ? n.appendChild(i) : "string" == typeof n && document.getElementsByTagName(n)[0].appendChild(i), i;
  }, iframe: function iframe(e) {
    this.append("iframe", { src: e, style: { position: "absolute", left: "-1000px", bottom: 0, height: "1px", width: "1px" } }, "body");
  }, merge: function merge() {
    var e = Array.prototype.slice.call(arguments);return e.unshift({}), this.extend.apply(null, e);
  }, args: function args(e, t) {
    var n = {},
        i = 0,
        o = null,
        a = null;for (a in e) {
      if (e.hasOwnProperty(a)) break;
    }if (1 === t.length && "object" == _typeof(t[0]) && "o!" != e[a]) for (a in t[0]) {
      if (e.hasOwnProperty(a) && a in e) return t[0];
    }for (a in e) {
      if (e.hasOwnProperty(a)) if (o = _typeof(t[i]), "function" == typeof e[a] && e[a].test(t[i]) || "string" == typeof e[a] && (e[a].indexOf("s") > -1 && "string" === o || e[a].indexOf("o") > -1 && "object" === o || e[a].indexOf("i") > -1 && "number" === o || e[a].indexOf("a") > -1 && "object" === o || e[a].indexOf("f") > -1 && "function" === o)) n[a] = t[i++];else if ("string" == typeof e[a] && e[a].indexOf("!") > -1) return !1;
    }return n;
  }, url: function url(e) {
    if (e) {
      if (window.URL && URL instanceof Function && 0 !== URL.length) return new URL(e, window.location);var t = document.createElement("a");return t.href = e, t.cloneNode(!1);
    }return window.location;
  }, diff: function diff(e, t) {
    return t.filter(function (t) {
      return -1 === e.indexOf(t);
    });
  }, diffKey: function diffKey(e, t) {
    if (e || !t) {
      var n = {};for (var i in e) {
        i in t || (n[i] = e[i]);
      }return n;
    }return e;
  }, unique: function unique(e) {
    return Array.isArray(e) ? e.filter(function (t, n) {
      return e.indexOf(t) === n;
    }) : [];
  }, isEmpty: function isEmpty(e) {
    if (!e) return !0;if (Array.isArray(e)) return !e.length;if ("object" == (typeof e === "undefined" ? "undefined" : _typeof(e))) for (var t in e) {
      if (e.hasOwnProperty(t)) return !1;
    }return !0;
  }, Promise: function () {
    var e = function e(t) {
      if (!(this instanceof e)) return new e(t);this.id = "Thenable/1.0.6", this.state = 0, this.fulfillValue = void 0, this.rejectReason = void 0, this.onFulfilled = [], this.onRejected = [], this.proxy = { then: this.then.bind(this) }, "function" == typeof t && t.call(this, this.fulfill.bind(this), this.reject.bind(this));
    };e.prototype = { fulfill: function fulfill(e) {
        return t(this, 1, "fulfillValue", e);
      }, reject: function reject(e) {
        return t(this, 2, "rejectReason", e);
      }, then: function then(t, i) {
        var a = new e();return this.onFulfilled.push(o(t, a, "fulfill")), this.onRejected.push(o(i, a, "reject")), n(this), a.proxy;
      } };var t = function t(e, _t, i, o) {
      return 0 === e.state && (e.state = _t, e[i] = o, n(e)), e;
    },
        n = function n(e) {
      1 === e.state ? i(e, "onFulfilled", e.fulfillValue) : 2 === e.state && i(e, "onRejected", e.rejectReason);
    },
        i = function i(e, t, n) {
      if (0 !== e[t].length) {
        var i = e[t];e[t] = [];var o = function o() {
          for (var e = 0; e < i.length; e++) {
            i[e](n);
          }
        };"object" == (typeof process === "undefined" ? "undefined" : _typeof(process)) && "function" == typeof process.nextTick ? process.nextTick(o) : "function" == typeof setImmediate ? setImmediate(o) : setTimeout(o, 0);
      }
    },
        o = function o(e, t, n) {
      return function (i) {
        if ("function" != typeof e) t[n].call(t, i);else {
          var o;try {
            o = e(i);
          } catch (e) {
            return void t.reject(e);
          }a(t, o);
        }
      };
    },
        a = function a(e, t) {
      if (e !== t && e.proxy !== t) {
        var n;if ("object" == (typeof t === "undefined" ? "undefined" : _typeof(t)) && null !== t || "function" == typeof t) try {
          n = t.then;
        } catch (t) {
          return void e.reject(t);
        }if ("function" != typeof n) e.fulfill(t);else {
          var i = !1;try {
            n.call(t, function (n) {
              i || (i = !0, n === t ? e.reject(new TypeError("circular thenable chain")) : a(e, n));
            }, function (t) {
              i || (i = !0, e.reject(t));
            });
          } catch (t) {
            i || e.reject(t);
          }
        }
      } else e.reject(new TypeError("cannot resolve promise with itself"));
    };return e;
  }(), Event: function Event() {
    var e = /[\s\,]+/;return this.parent = { events: this.events, findEvents: this.findEvents, parent: this.parent, utils: this.utils }, this.events = {}, this.on = function (t, n) {
      if (n && "function" == typeof n) for (var i = t.split(e), o = 0; o < i.length; o++) {
        this.events[i[o]] = [n].concat(this.events[i[o]] || []);
      }return this;
    }, this.off = function (e, t) {
      return this.findEvents(e, function (e, n) {
        t && this.events[e][n] !== t || (this.events[e][n] = null);
      }), this;
    }, this.emit = function (e) {
      var t = Array.prototype.slice.call(arguments, 1);t.push(e);for (var n = function n(_n, i) {
        t[t.length - 1] = "*" === _n ? e : _n, this.events[_n][i].apply(this, t);
      }, i = this; i && i.findEvents;) {
        i.findEvents(e + ",*", n), i = i.parent;
      }return this;
    }, this.emitAfter = function () {
      var e = this,
          t = arguments;return setTimeout(function () {
        e.emit.apply(e, t);
      }, 0), this;
    }, this.findEvents = function (t, n) {
      var i = t.split(e);for (var o in this.events) {
        if (this.events.hasOwnProperty(o) && i.indexOf(o) > -1) for (var a = 0; a < this.events[o].length; a++) {
          this.events[o][a] && n.call(this, o, a);
        }
      }
    }, this;
  }, globalEvent: function globalEvent(e, t) {
    return t = t || "_hellojs_" + parseInt(1e12 * Math.random(), 10).toString(36), window[t] = function () {
      try {
        e.apply(this, arguments) && delete window[t];
      } catch (e) {
        console.error(e);
      }
    }, t;
  }, popup: function popup(e, t, n) {
    var i = document.documentElement;if (n.height) {
      var o = void 0 !== window.screenTop ? window.screenTop : screen.top,
          a = screen.height || window.innerHeight || i.clientHeight;n.top = n.top ? n.top : parseInt((a - n.height) / 2, 10) + o;
    }if (n.width) {
      var r = void 0 !== window.screenLeft ? window.screenLeft : screen.left,
          s = screen.width || window.innerWidth || i.clientWidth;n.left = n.left ? n.left : parseInt((s - n.width) / 2, 10) + r;
    }var l = [];Object.keys(n).forEach(function (e) {
      var t = n[e];l.push(e + (null !== t ? "=" + t : ""));
    }), -1 !== navigator.userAgent.indexOf("Safari") && -1 === navigator.userAgent.indexOf("Chrome") && (e = t + "#oauth_redirect=" + encodeURIComponent(encodeURIComponent(e)));var u = window.open(e, "_blank", l.join(","));return u && u.focus && u.focus(), u;
  }, responseHandler: function responseHandler(e, t) {
    function n(e, t, n) {
      var a = e.callback,
          s = e.network;if (r.store(s, e), !("display" in e && "page" === e.display)) {
        if (n && a && a in n) {
          try {
            delete e.callback;
          } catch (e) {}r.store(s, e);var l = JSON.stringify(e);try {
            i(n, a)(l);
          } catch (e) {}
        }o();
      }
    }function i(e, t) {
      return 0 !== t.indexOf("_hellojs_") ? function () {
        throw "Could not execute callback " + t;
      } : e[t];
    }function o() {
      if (e.frameElement) t.document.body.removeChild(e.frameElement);else {
        try {
          e.close();
        } catch (e) {}e.addEventListener && e.addEventListener("load", function () {
          e.close();
        });
      }
    }var a,
        r = this,
        s = e.location;if ((a = r.param(s.search)) && a.state && (a.code || a.oauth_token)) {
      var l = JSON.parse(a.state);a.redirect_uri = l.redirect_uri || s.href.replace(/[\?\#].*$/, "");var u = r.qs(l.oauth_proxy, a);s.assign(u);
    } else if ((a = r.merge(r.param(s.search || ""), r.param(s.hash || ""))) && "state" in a) {
      try {
        var c = JSON.parse(a.state);r.extend(a, c);
      } catch (e) {
        var f = decodeURIComponent(a.state);try {
          var d = JSON.parse(f);r.extend(a, d);
        } catch (e) {
          console.error("Could not decode state parameter");
        }
      }if ("access_token" in a && a.access_token && a.network) a.expires_in && 0 !== parseInt(a.expires_in, 10) || (a.expires_in = 0), a.expires_in = parseInt(a.expires_in, 10), a.expires = new Date().getTime() / 1e3 + (a.expires_in || 31536e3), n(a, 0, t);else if ("error" in a && a.error && a.network) a.error = { code: a.error, message: a.error_message || a.error_description }, n(a, 0, t);else if (a.callback && a.callback in t) {
        var p = !!("result" in a && a.result) && JSON.parse(a.result);i(t, a.callback)(p), o();
      }a.page_uri && s.assign(a.page_uri);
    } else if ("oauth_redirect" in a) return void s.assign(decodeURIComponent(a.oauth_redirect));
  } }), hello.utils.Event.call(hello), function (e) {
  var t = {},
      n = {};e.on("auth.login, auth.logout", function (n) {
    n && "object" == (typeof n === "undefined" ? "undefined" : _typeof(n)) && n.network && (t[n.network] = e.utils.store(n.network) || {});
  }), function i() {
    var o = new Date().getTime() / 1e3,
        a = function a(t) {
      e.emit("auth." + t, { network: r, authResponse: s });
    };for (var r in e.services) {
      if (e.services.hasOwnProperty(r)) {
        if (!e.services[r].id) continue;var s = e.utils.store(r) || {},
            l = e.services[r],
            u = t[r] || {};if (s && "callback" in s) {
          var c = s.callback;try {
            delete s.callback;
          } catch (e) {}e.utils.store(r, s);try {
            window[c](s);
          } catch (e) {}
        }if (s && "expires" in s && s.expires < o) {
          var f = l.refresh || s.refresh_token;!f || r in n && !(n[r] < o) ? f || r in n || (a("expired"), n[r] = !0) : (e.emit("notice", r + " has expired trying to resignin"), e.login(r, { display: "none", force: !1 }), n[r] = o + 600);continue;
        }if (u.access_token === s.access_token && u.expires === s.expires) continue;!s.access_token && u.access_token ? a("logout") : s.access_token && !u.access_token ? a("login") : s.expires !== u.expires && a("update"), t[r] = s, r in n && delete n[r];
      }
    }setTimeout(i, 1e3);
  }();
}(hello), hello.api = function () {
  function e(e) {
    (e = e.replace(/\@\{([a-z\_\-]+)(\|.*?)?\}/gi, function (e, t, a) {
      var r = a ? a.replace(/^\|/, "") : "";return t in o.query ? (r = o.query[t], delete o.query[t]) : o.data && t in o.data ? (r = o.data[t], delete o.data[t]) : a || i.reject(n("missing_attribute", "The attribute " + t + " is missing from the request")), r;
    })).match(/^https?:\/\//) || (e = l.base + e), o.url = e, t.request(o, function (e, n) {
      if (o.formatResponse) {
        if (!0 === e ? e = { success: !0 } : e || (e = {}), "delete" === o.method && (e = !e || t.isEmpty(e) ? { success: !0 } : e), l.wrap && (o.path in l.wrap || "default" in l.wrap)) {
          var a = o.path in l.wrap ? o.path : "default",
              r = (new Date().getTime(), l.wrap[a](e, n, o));r && (e = r);
        }e && "paging" in e && e.paging.next && ("?" === e.paging.next[0] ? e.paging.next = o.path + e.paging.next : e.paging.next += "#" + o.path), !e || "error" in e ? i.reject(e) : i.fulfill(e);
      } else ("object" == (typeof n === "undefined" ? "undefined" : _typeof(n)) ? n.statusCode >= 400 : "object" == (typeof e === "undefined" ? "undefined" : _typeof(e)) && "error" in e) ? i.reject(e) : i.fulfill(e);
    });
  }var t = this.utils,
      n = t.error,
      i = t.Promise(),
      o = t.args({ path: "s!", query: "o", method: "s", data: "o", timeout: "i", callback: "f" }, arguments);o.method = (o.method || "get").toLowerCase(), o.headers = o.headers || {}, o.query = o.query || {}, "get" !== o.method && "delete" !== o.method || (t.extend(o.query, o.data), o.data = {});var a = o.data = o.data || {};if (i.then(o.callback, o.callback), !o.path) return i.reject(n("invalid_path", "Missing the path parameter from the request"));o.path = o.path.replace(/^\/+/, "");var r = (o.path.split(/[\/\:]/, 2) || [])[0].toLowerCase();if (r in this.services) {
    o.network = r;var s = new RegExp("^" + r + ":?/?");o.path = o.path.replace(s, "");
  }o.network = this.settings.default_service = o.network || this.settings.default_service;var l = this.services[o.network];if (!l) return i.reject(n("invalid_network", "Could not match the service requested: " + o.network));if (o.method in l && o.path in l[o.method] && !1 === l[o.method][o.path]) return i.reject(n("invalid_path", "The provided path is not available on the selected network"));o.oauth_proxy || (o.oauth_proxy = this.settings.oauth_proxy), "proxy" in o || (o.proxy = o.oauth_proxy && l.oauth && 1 === parseInt(l.oauth.version, 10)), "timeout" in o || (o.timeout = this.settings.timeout), "formatResponse" in o || (o.formatResponse = !0), o.authResponse = this.getAuthResponse(o.network), o.authResponse && o.authResponse.access_token && (o.query.access_token = o.authResponse.access_token);var u,
      c = o.path;o.options = t.clone(o.query), o.data = t.clone(a);var f = l[{ delete: "del" }[o.method] || o.method] || {};if ("get" === o.method) {
    var d = c.split(/[\?#]/)[1];d && (t.extend(o.query, t.param(d)), c = c.replace(/\?.*?(#|$)/, "$1"));
  }return (u = c.match(/#(.+)/, "")) ? (c = c.split("#")[0], o.path = u[1]) : c in f ? (o.path = c, c = f[c]) : "default" in f && (c = f.default), o.redirect_uri = this.settings.redirect_uri, o.xhr = l.xhr, o.jsonp = l.jsonp, o.form = l.form, "function" == typeof c ? c(o, e) : e(c), i.proxy;
}, hello.utils.extend(hello.utils, { request: function request(e, t) {
    function n(e, t) {
      var n;e.authResponse && e.authResponse.oauth && 1 === parseInt(e.authResponse.oauth.version, 10) && (n = e.query.access_token, delete e.query.access_token, e.proxy = !0), !e.data || "get" !== e.method && "delete" !== e.method || (i.extend(e.query, e.data), e.data = null);var o = i.qs(e.url, e.query);e.proxy && (o = i.qs(e.oauth_proxy, { path: o, access_token: n || "", then: e.proxy_response_type || ("get" === e.method.toLowerCase() ? "redirect" : "proxy"), method: e.method.toLowerCase(), suppress_response_codes: !0 })), t(o);
    }var i = this,
        o = i.error;i.isEmpty(e.data) || "FileList" in window || !i.hasBinary(e.data) || (e.xhr = !1, e.jsonp = !1);if (this.request_cors(function () {
      return void 0 === e.xhr || e.xhr && ("function" != typeof e.xhr || e.xhr(e, e.query));
    })) n(e, function (n) {
      var o = i.xhr(e.method, n, e.headers, e.data, t);o.onprogress = e.onprogress || null, o.upload && e.onuploadprogress && (o.upload.onprogress = e.onuploadprogress);
    });else {
      var a = e.query;if (e.query = i.clone(e.query), e.callbackID = i.globalEvent(), !1 !== e.jsonp) {
        if (e.query.callback = e.callbackID, "function" == typeof e.jsonp && e.jsonp(e, e.query), "get" === e.method) return void n(e, function (n) {
          i.jsonp(n, t, e.callbackID, e.timeout);
        });e.query = a;
      }if (!1 !== e.form) {
        e.query.redirect_uri = e.redirect_uri, e.query.state = JSON.stringify({ callback: e.callbackID });var r;if ("function" == typeof e.form && (r = e.form(e, e.query)), "post" === e.method && !1 !== r) return void n(e, function (n) {
          i.post(n, e.data, r, t, e.callbackID, e.timeout);
        });
      }t(o("invalid_request", "There was no mechanism for handling this request"));
    }
  }, request_cors: function request_cors(e) {
    return "withCredentials" in new XMLHttpRequest() && e();
  }, domInstance: function domInstance(e, t) {
    var n = "HTML" + (e || "").replace(/^[a-z]/, function (e) {
      return e.toUpperCase();
    }) + "Element";return !!t && (window[n] ? t instanceof window[n] : window.Element ? t instanceof window.Element && (!e || t.tagName && t.tagName.toLowerCase() === e) : !(t instanceof Object || t instanceof Array || t instanceof String || t instanceof Number) && t.tagName && t.tagName.toLowerCase() === e);
  }, clone: function clone(e) {
    if (null === e || "object" != (typeof e === "undefined" ? "undefined" : _typeof(e)) || e instanceof Date || "nodeName" in e || this.isBinary(e) || "function" == typeof FormData && e instanceof FormData) return e;if (Array.isArray(e)) return e.map(this.clone.bind(this));var t = {};for (var n in e) {
      t[n] = this.clone(e[n]);
    }return t;
  }, xhr: function xhr(e, t, n, i, o) {
    var a = new XMLHttpRequest(),
        r = this.error,
        s = !1;"blob" === e && (s = e, e = "GET"), e = e.toUpperCase(), a.onload = function (t) {
      var n = a.response;try {
        n = JSON.parse(a.responseText);
      } catch (e) {
        401 === a.status && (n = r("access_denied", a.statusText));
      }var i = function (e) {
        for (var t, n = {}, i = /([a-z\-]+):\s?(.*);?/gi; t = i.exec(e);) {
          n[t[1]] = t[2];
        }return n;
      }(a.getAllResponseHeaders());i.statusCode = a.status, o(n || ("GET" === e ? r("empty_response", "Could not get resource") : {}), i);
    }, a.onerror = function (e) {
      var t = a.responseText;try {
        t = JSON.parse(a.responseText);
      } catch (e) {}o(t || r("access_denied", "Could not get resource"));
    };var l;if ("GET" === e || "DELETE" === e) i = null;else if (i && "string" != typeof i && !(i instanceof FormData) && !(i instanceof File) && !(i instanceof Blob)) {
      var u = new FormData();for (l in i) {
        i.hasOwnProperty(l) && (i[l] instanceof HTMLInputElement ? "files" in i[l] && i[l].files.length > 0 && u.append(l, i[l].files[0]) : i[l] instanceof Blob ? u.append(l, i[l], i.name) : u.append(l, i[l]));
      }i = u;
    }if (a.open(e, t, !0), s && ("responseType" in a ? a.responseType = s : a.overrideMimeType("text/plain; charset=x-user-defined")), n) for (l in n) {
      a.setRequestHeader(l, n[l]);
    }return a.send(i), a;
  }, jsonp: function jsonp(e, t, n, i) {
    var o,
        a = this.error,
        r = 0,
        s = document.getElementsByTagName("head")[0],
        l = a("server_error", "server_error"),
        u = function u() {
      r++ || window.setTimeout(function () {
        t(l), s.removeChild(c);
      }, 0);
    };n = this.globalEvent(function (e) {
      return l = e, !0;
    }, n), e = e.replace(new RegExp("=\\?(&|$)"), "=" + n + "$1");var c = this.append("script", { id: n, name: n, src: e, async: !0, onload: u, onerror: u, onreadystatechange: function onreadystatechange() {
        /loaded|complete/i.test(this.readyState) && u();
      } });window.navigator.userAgent.toLowerCase().indexOf("opera") > -1 && (o = this.append("script", { text: "document.getElementById('" + n + "').onerror();" }), c.async = !1), i && window.setTimeout(function () {
      l = a("timeout", "timeout"), u();
    }, i), s.appendChild(c), o && s.appendChild(o);
  }, post: function post(e, t, n, i, o, a) {
    var r,
        s = this.error,
        l = document,
        u = null,
        c = [],
        f = 0,
        d = null,
        p = 0,
        h = function h(e) {
      p++ || i(e);
    };this.globalEvent(h, o);var m;try {
      m = l.createElement('<iframe name="' + o + '">');
    } catch (e) {
      m = l.createElement("iframe");
    }if (m.name = o, m.id = o, m.style.display = "none", n && n.callbackonload && (m.onload = function () {
      h({ response: "posted", message: "Content was posted" });
    }), a && setTimeout(function () {
      h(s("timeout", "The post operation timed out"));
    }, a), l.body.appendChild(m), this.domInstance("form", t)) {
      for (u = t.form, f = 0; f < u.elements.length; f++) {
        u.elements[f] !== t && u.elements[f].setAttribute("disabled", !0);
      }t = u;
    }if (this.domInstance("form", t)) for (u = t, f = 0; f < u.elements.length; f++) {
      u.elements[f].disabled || "file" !== u.elements[f].type || (u.encoding = u.enctype = "multipart/form-data", u.elements[f].setAttribute("name", "file"));
    } else {
      for (d in t) {
        t.hasOwnProperty(d) && this.domInstance("input", t[d]) && "file" === t[d].type && ((u = t[d].form).encoding = u.enctype = "multipart/form-data");
      }u || (u = l.createElement("form"), l.body.appendChild(u), r = u);var g;for (d in t) {
        if (t.hasOwnProperty(d)) {
          var v = this.domInstance("input", t[d]) || this.domInstance("textArea", t[d]) || this.domInstance("select", t[d]);if (v && t[d].form === u) v && t[d].name !== d && (t[d].setAttribute("name", d), t[d].name = d);else {
            var y = u.elements[d];if (g) for (y instanceof NodeList || (y = [y]), f = 0; f < y.length; f++) {
              y[f].parentNode.removeChild(y[f]);
            }(g = l.createElement("input")).setAttribute("type", "hidden"), g.setAttribute("name", d), v ? g.value = t[d].value : this.domInstance(null, t[d]) ? g.value = t[d].innerHTML || t[d].innerText : g.value = t[d], u.appendChild(g);
          }
        }
      }for (f = 0; f < u.elements.length; f++) {
        (g = u.elements[f]).name in t || !0 === g.getAttribute("disabled") || (g.setAttribute("disabled", !0), c.push(g));
      }
    }u.setAttribute("method", "POST"), u.setAttribute("target", o), u.target = o, u.setAttribute("action", e), setTimeout(function () {
      u.submit(), setTimeout(function () {
        try {
          r && r.parentNode.removeChild(r);
        } catch (e) {
          try {
            console.error("HelloJS: could not remove iframe");
          } catch (e) {}
        }for (var e = 0; e < c.length; e++) {
          c[e] && (c[e].setAttribute("disabled", !1), c[e].disabled = !1);
        }
      }, 0);
    }, 100);
  }, hasBinary: function hasBinary(e) {
    for (var t in e) {
      if (e.hasOwnProperty(t) && this.isBinary(e[t])) return !0;
    }return !1;
  }, isBinary: function isBinary(e) {
    return e instanceof Object && (this.domInstance("input", e) && "file" === e.type || "FileList" in window && e instanceof window.FileList || "File" in window && e instanceof window.File || "Blob" in window && e instanceof window.Blob);
  }, toBlob: function toBlob(e) {
    var t = /^data\:([^;,]+(\;charset=[^;,]+)?)(\;base64)?,/i,
        n = e.match(t);if (!n) return e;for (var i = atob(e.replace(t, "")), o = [], a = 0; a < i.length; a++) {
      o.push(i.charCodeAt(a));
    }return new Blob([new Uint8Array(o)], { type: n[1] });
  } }), function (e) {
  var t = e.api,
      n = e.utils;n.extend(n, { dataToJSON: function dataToJSON(e) {
      var t = window,
          n = e.data;if (this.domInstance("form", n) ? n = this.nodeListToJSON(n.elements) : "NodeList" in t && n instanceof NodeList ? n = this.nodeListToJSON(n) : this.domInstance("input", n) && (n = this.nodeListToJSON([n])), ("File" in t && n instanceof t.File || "Blob" in t && n instanceof t.Blob || "FileList" in t && n instanceof t.FileList) && (n = { file: n }), !("FormData" in t && n instanceof t.FormData)) for (var i in n) {
        if (n.hasOwnProperty(i)) if ("FileList" in t && n[i] instanceof t.FileList) 1 === n[i].length && (n[i] = n[i][0]);else {
          if (this.domInstance("input", n[i]) && "file" === n[i].type) continue;this.domInstance("input", n[i]) || this.domInstance("select", n[i]) || this.domInstance("textArea", n[i]) ? n[i] = n[i].value : this.domInstance(null, n[i]) && (n[i] = n[i].innerHTML || n[i].innerText);
        }
      }return e.data = n, n;
    }, nodeListToJSON: function nodeListToJSON(e) {
      for (var t = {}, n = 0; n < e.length; n++) {
        var i = e[n];!i.disabled && i.name && ("file" === i.type ? t[i.name] = i : t[i.name] = i.value || i.innerHTML);
      }return t;
    } }), e.api = function () {
    var e = n.args({ path: "s!", method: "s", data: "o", timeout: "i", callback: "f" }, arguments);return e.data && n.dataToJSON(e), t.call(this, e);
  };
}(hello), hello.utils.responseHandler(window, window.opener || window.parent), "object" == (typeof chrome === "undefined" ? "undefined" : _typeof(chrome)) && "object" == _typeof(chrome.identity) && chrome.identity.launchWebAuthFlow && function () {
  function e(t, n) {
    var i = { closed: !1 };return chrome.identity.launchWebAuthFlow({ url: t, interactive: n }, function (t) {
      if (void 0 !== t) {
        var n = hello.utils.url(t),
            o = { location: { assign: function assign(t) {
              e(t, !1);
            }, search: n.search, hash: n.hash, href: n.href }, close: function close() {} };hello.utils.responseHandler(o, window);
      } else i.closed = !0;
    }), i;
  }hello.utils.popup = function (t) {
    return e(t, !0);
  }, hello.utils.iframe = function (t) {
    e(t, !1);
  }, hello.utils.request_cors = function (e) {
    return e(), !0;
  };var t = {};chrome.storage.local.get("hello", function (e) {
    t = e.hello || {};
  }), hello.utils.store = function (e, n) {
    return 0 === arguments.length ? t : 1 === arguments.length ? t[e] || null : n ? (t[e] = n, chrome.storage.local.set({ hello: t }), n) : null === n ? (delete t[e], chrome.storage.local.set({ hello: t }), null) : void 0;
  };
}(), function () {
  if (/^file:\/{3}[^\/]/.test(window.location.href) && window.cordova) {
    hello.utils.iframe = function (e, t) {
      hello.utils.popup(e, t, { hidden: "yes" });
    };var e = hello.utils.popup;hello.utils.popup = function (t, n, i) {
      var o = e.call(this, t, n, i);try {
        if (o && o.addEventListener) {
          var a = hello.utils.url(n),
              r = a.origin || a.protocol + "//" + a.hostname;o.addEventListener("loadstart", function (e) {
            var t = e.url;if (0 === t.indexOf(r)) {
              var n = hello.utils.url(t),
                  i = { location: { assign: function assign(e) {
                    o.executeScript({ code: 'window.location.href = "' + e + ';"' });
                  }, search: n.search, hash: n.hash, href: n.href }, close: function close() {
                  if (o.close) {
                    o.close();try {
                      o.closed = !0;
                    } catch (e) {}
                  }
                } };hello.utils.responseHandler(i, window);
            }
          });
        }
      } catch (e) {}return o;
    };
  }
}(), function (e) {
  function t(e) {
    e && "error" in e && (e.error = { code: "server_error", message: e.error.message || e.error });
  }function n(t, n, i) {
    if (!("object" != (typeof t === "undefined" ? "undefined" : _typeof(t)) || "undefined" != typeof Blob && t instanceof Blob || "undefined" != typeof ArrayBuffer && t instanceof ArrayBuffer || "error" in t)) {
      var o = ("app_folder" !== t.root ? t.root : "") + t.path.replace(/\&/g, "%26");o = o.replace(/^\//, ""), t.thumb_exists && (t.thumbnail = i.oauth_proxy + "?path=" + encodeURIComponent("https://api-content.dropbox.com/1/thumbnails/auto/" + o + "?format=jpeg&size=m") + "&access_token=" + i.options.access_token), t.type = t.is_dir ? "folder" : t.mime_type, t.name = t.path.replace(/.*\//g, ""), t.is_dir ? t.files = o.replace(/^\//, "") : (t.downloadLink = e.settings.oauth_proxy + "?path=" + encodeURIComponent("https://api-content.dropbox.com/1/files/auto/" + o) + "&access_token=" + i.options.access_token, t.file = "https://api-content.dropbox.com/1/files/auto/" + o), t.id || (t.id = t.path.replace(/^\//, ""));
    }
  }function i(e) {
    return function (t, n) {
      delete t.query.limit, n(e);
    };
  }var o = { version: "1.0", auth: "https://www.dropbox.com/1/oauth/authorize", request: "https://api.dropbox.com/1/oauth/request_token", token: "https://api.dropbox.com/1/oauth/access_token" },
      a = { version: 2, auth: "https://www.dropbox.com/1/oauth2/authorize", grant: "https://api.dropbox.com/1/oauth2/token" };e.init({ dropbox: { name: "Dropbox", oauth: a, login: function login(t) {
        t.qs.scope = "";var n = decodeURIComponent(t.qs.redirect_uri);0 === n.indexOf("http:") && 0 !== n.indexOf("http://localhost/") ? e.services.dropbox.oauth = o : e.services.dropbox.oauth = a, t.options.popup.width = 1e3, t.options.popup.height = 1e3;
      }, base: "https://api.dropbox.com/1/", root: "sandbox", get: { me: "account/info", "me/files": i("metadata/auto/@{parent|}"), "me/folder": i("metadata/auto/@{id}"), "me/folders": i("metadata/auto/"), default: function _default(e, t) {
          e.path.match("https://api-content.dropbox.com/1/files/") && (e.method = "blob"), t(e.path);
        } }, post: { "me/files": function meFiles(t, n) {
          var i = t.data.parent,
              o = t.data.name;t.data = { file: t.data.file }, "string" == typeof t.data.file && (t.data.file = e.utils.toBlob(t.data.file)), n("https://api-content.dropbox.com/1/files_put/auto/" + i + "/" + o);
        }, "me/folders": function meFolders(t, n) {
          var i = t.data.name;t.data = {}, n("fileops/create_folder?root=@{root|sandbox}&" + e.utils.param({ path: i }));
        } }, del: { "me/files": "fileops/delete?root=@{root|sandbox}&path=@{id}", "me/folder": "fileops/delete?root=@{root|sandbox}&path=@{id}" }, wrap: { me: function me(e) {
          if (t(e), !e.uid) return e;e.name = e.display_name;var n = e.name.split(" ");return e.first_name = n.shift(), e.last_name = n.join(" "), e.id = e.uid, delete e.uid, delete e.display_name, e;
        }, default: function _default(e, i, o) {
          return t(e), e.is_dir && e.contents && (e.data = e.contents, delete e.contents, e.data.forEach(function (t) {
            t.root = e.root, n(t, 0, o);
          })), n(e, 0, o), e.is_deleted && (e.success = !0), e;
        } }, xhr: function xhr(e) {
        if (e.data && e.data.file) {
          var t = e.data.file;t && (t.files ? e.data = t.files[0] : e.data = t);
        }return "delete" === e.method && (e.method = "post"), !0;
      }, form: function form(e, t) {
        delete t.state, delete t.redirect_uri;
      } } });
}(hello), function (e) {
  function t(e) {
    return e.id && (e.thumbnail = e.picture = "https://graph.facebook.com/" + e.id + "/picture"), e;
  }function n(e) {
    return "data" in e && e.data.forEach(t), e;
  }function i(e, t, n) {
    if ("boolean" == typeof e && (e = { success: e }), e && "data" in e) {
      var i = n.query.access_token;if (!(e.data instanceof Array)) {
        var a = e.data;delete e.data, e.data = [a];
      }e.data.forEach(function (e) {
        e.picture && (e.thumbnail = e.picture), e.pictures = (e.images || []).sort(function (e, t) {
          return e.width - t.width;
        }), e.cover_photo && e.cover_photo.id && (e.thumbnail = o + e.cover_photo.id + "/picture?access_token=" + i), "album" === e.type && (e.files = e.photos = o + e.id + "/photos"), e.can_upload && (e.upload_location = o + e.id + "/photos");
      });
    }return e;
  }e.init({ facebook: { name: "Facebook", oauth: { version: 2, auth: "https://www.facebook.com/v2.9/dialog/oauth/", grant: "https://graph.facebook.com/oauth/access_token" }, scope: { basic: "public_profile", email: "email", share: "user_posts", birthday: "user_birthday", events: "user_events", photos: "user_photos", videos: "user_videos", friends: "user_friends", files: "user_photos,user_videos", publish_files: "user_photos,user_videos,publish_actions", publish: "publish_actions", offline_access: "" }, refresh: !1, login: function login(e) {
        e.options.force && (e.qs.auth_type = "reauthenticate"), e.qs.display = e.options.display || "popup";
      }, logout: function logout(t, n) {
        var i = e.utils.globalEvent(t),
            o = encodeURIComponent(e.settings.redirect_uri + "?" + e.utils.param({ callback: i, result: JSON.stringify({ force: !0 }), state: "{}" })),
            a = (n.authResponse || {}).access_token;if (e.utils.iframe("https://www.facebook.com/logout.php?next=" + o + "&access_token=" + a), !a) return !1;
      }, base: "https://graph.facebook.com/v2.9/", get: { me: "me?fields=email,first_name,last_name,name,timezone,verified", "me/friends": "me/friends", "me/following": "me/friends", "me/followers": "me/friends", "me/share": "me/feed", "me/like": "me/likes", "me/files": "me/albums", "me/albums": "me/albums?fields=cover_photo,name", "me/album": "@{id}/photos?fields=picture", "me/photos": "me/photos", "me/photo": "@{id}", "friend/albums": "@{id}/albums", "friend/photos": "@{id}/photos" }, post: { "me/share": "me/feed", "me/photo": "@{id}" }, wrap: { me: t, "me/friends": n, "me/following": n, "me/followers": n, "me/albums": i, "me/photos": i, "me/files": i, default: i }, xhr: function xhr(t, n) {
        return "get" !== t.method && "post" !== t.method || (n.suppress_response_codes = !0), "post" === t.method && t.data && "string" == typeof t.data.file && (t.data.file = e.utils.toBlob(t.data.file)), !0;
      }, jsonp: function jsonp(t, n) {
        var i = t.method;"get" === i || e.utils.hasBinary(t.data) ? "delete" === t.method && (n.method = "delete", t.method = "post") : (t.data.method = i, t.method = "get");
      }, form: function form(e) {
        return { callbackonload: !0 };
      } } });var o = "https://graph.facebook.com/";
}(hello), function (e) {
  function t(t, n, i) {
    var o = (i ? "" : "flickr:") + "?method=" + t + "&api_key=" + e.services.flickr.id + "&format=json";for (var a in n) {
      n.hasOwnProperty(a) && (o += "&" + a + "=" + n[a]);
    }return o;
  }function n(n, i) {
    return i || (i = {}), function (o, a) {
      !function (t) {
        var n = e.getAuthResponse("flickr");t(n && n.user_nsid ? n.user_nsid : null);
      }(function (e) {
        i.user_id = e, a(t(n, i, !0));
      });
    };
  }function i(e, t) {
    var n = "https://www.flickr.com/images/buddyicon.gif";return e.nsid && e.iconserver && e.iconfarm && (n = "https://farm" + e.iconfarm + ".staticflickr.com/" + e.iconserver + "/buddyicons/" + e.nsid + (t ? "_" + t : "") + ".jpg"), n;
  }function o(e, t, n, i, o) {
    return o = o ? "_" + o : "", "https://farm" + t + ".staticflickr.com/" + n + "/" + e + "_" + i + o + ".jpg";
  }function a(e) {
    e && e.stat && "ok" != e.stat.toLowerCase() && (e.error = { code: "invalid_request", message: e.message });
  }function r(e) {
    if (e.photoset || e.photos) {
      u(e = s(e, "photoset" in e ? "photoset" : "photos")), e.data = e.photo, delete e.photo;for (var t = 0; t < e.data.length; t++) {
        var n = e.data[t];n.name = n.title, n.picture = o(n.id, n.farm, n.server, n.secret, ""), n.pictures = function (e, t, n, i) {
          return [{ id: "t", max: 100 }, { id: "m", max: 240 }, { id: "n", max: 320 }, { id: "", max: 500 }, { id: "z", max: 640 }, { id: "c", max: 800 }, { id: "b", max: 1024 }, { id: "h", max: 1600 }, { id: "k", max: 2048 }, { id: "o", max: 2048 }].map(function (a) {
            return { source: o(e, t, n, i, a.id), width: a.max, height: a.max };
          });
        }(n.id, n.farm, n.server, n.secret), n.source = o(n.id, n.farm, n.server, n.secret, "b"), n.thumbnail = o(n.id, n.farm, n.server, n.secret, "m");
      }
    }return e;
  }function s(e, t) {
    return t in e ? e = e[t] : "error" in e || (e.error = { code: "invalid_request", message: e.message || "Failed to get data from Flickr" }), e;
  }function l(e) {
    if (a(e), e.contacts) {
      u(e = s(e, "contacts")), e.data = e.contact, delete e.contact;for (var t = 0; t < e.data.length; t++) {
        var n = e.data[t];n.id = n.nsid, n.name = n.realname || n.username, n.thumbnail = i(n, "m");
      }
    }return e;
  }function u(e) {
    e.page && e.pages && e.page !== e.pages && (e.paging = { next: "?page=" + ++e.page });
  }e.init({ flickr: { name: "Flickr", oauth: { version: "1.0a", auth: "https://www.flickr.com/services/oauth/authorize?perms=read", request: "https://www.flickr.com/services/oauth/request_token", token: "https://www.flickr.com/services/oauth/access_token" }, base: "https://api.flickr.com/services/rest", get: { me: n("flickr.people.getInfo"), "me/friends": n("flickr.contacts.getList", { per_page: "@{limit|50}" }), "me/following": n("flickr.contacts.getList", { per_page: "@{limit|50}" }), "me/followers": n("flickr.contacts.getList", { per_page: "@{limit|50}" }), "me/albums": n("flickr.photosets.getList", { per_page: "@{limit|50}" }), "me/album": n("flickr.photosets.getPhotos", { photoset_id: "@{id}" }), "me/photos": n("flickr.people.getPhotos", { per_page: "@{limit|50}" }) }, wrap: { me: function me(e) {
          if (a(e), (e = s(e, "person")).id) {
            if (e.realname) {
              e.name = e.realname._content;var t = e.name.split(" ");e.first_name = t.shift(), e.last_name = t.join(" ");
            }e.thumbnail = i(e, "l"), e.picture = i(e, "l");
          }return e;
        }, "me/friends": l, "me/followers": l, "me/following": l, "me/albums": function meAlbums(e) {
          return a(e), e = s(e, "photosets"), u(e), e.photoset && (e.data = e.photoset, e.data.forEach(function (e) {
            e.name = e.title._content, e.photos = "https://api.flickr.com/services/rest" + t("flickr.photosets.getPhotos", { photoset_id: e.id }, !0);
          }), delete e.photoset), e;
        }, "me/photos": function mePhotos(e) {
          return a(e), r(e);
        }, default: function _default(e) {
          return a(e), r(e);
        } }, xhr: !1, jsonp: function jsonp(e, t) {
        "get" == e.method && (delete t.callback, t.jsoncallback = e.callbackID);
      } } });
}(hello), function (e) {
  function t(e) {
    !e.meta || 400 !== e.meta.code && 401 !== e.meta.code || (e.error = { code: "access_denied", message: e.meta.errorDetail });
  }function n(e) {
    e && e.id && (e.thumbnail = e.photo.prefix + "100x100" + e.photo.suffix, e.name = e.firstName + " " + e.lastName, e.first_name = e.firstName, e.last_name = e.lastName, e.contact && e.contact.email && (e.email = e.contact.email));
  }function i(e, t) {
    var n = t.access_token;return delete t.access_token, t.oauth_token = n, t.v = 20121125, !0;
  }hello.init({ foursquare: { name: "Foursquare", oauth: { version: 2, auth: "https://foursquare.com/oauth2/authenticate", grant: "https://foursquare.com/oauth2/access_token" }, refresh: !0, base: "https://api.foursquare.com/v2/", get: { me: "users/self", "me/friends": "users/self/friends", "me/followers": "users/self/friends", "me/following": "users/self/friends" }, wrap: { me: function me(e) {
          return t(e), e && e.response && n(e = e.response.user), e;
        }, default: function _default(e) {
          return t(e), e && "response" in e && "friends" in e.response && "items" in e.response.friends && (e.data = e.response.friends.items, e.data.forEach(n), delete e.response), e;
        } }, xhr: i, jsonp: i } });
}(), function (e) {
  function t(e, t) {
    var n = t ? t.statusCode : e && "meta" in e && "status" in e.meta && e.meta.status;401 !== n && 403 !== n || (e.error = { code: "access_denied", message: e.message || (e.data ? e.data.message : "Could not get response") }, delete e.message);
  }function n(e) {
    e.id && (e.thumbnail = e.picture = e.avatar_url, e.name = e.login);
  }hello.init({ github: { name: "GitHub", oauth: { version: 2, auth: "https://github.com/login/oauth/authorize", grant: "https://github.com/login/oauth/access_token", response_type: "code" }, scope: { email: "user:email" }, base: "https://api.github.com/", get: { me: "user", "me/friends": "user/following?per_page=@{limit|100}", "me/following": "user/following?per_page=@{limit|100}", "me/followers": "user/followers?per_page=@{limit|100}", "me/like": "user/starred?per_page=@{limit|100}" }, wrap: { me: function me(e, i) {
          return t(e, i), n(e), e;
        }, default: function _default(e, i, o) {
          return t(e, i), Array.isArray(e) && (e = { data: e }), e.data && (!function (e, t, n) {
            if (e.data && e.data.length && t && t.Link) {
              var i = t.Link.match(/<(.*?)>;\s*rel=\"next\"/);i && (e.paging = { next: i[1] });
            }
          }(e, i), e.data.forEach(n)), e;
        } }, xhr: function xhr(e) {
        return "get" !== e.method && e.data && (e.headers = e.headers || {}, e.headers["Content-Type"] = "application/json", "object" == _typeof(e.data) && (e.data = JSON.stringify(e.data))), !0;
      } } });
}(), function (e) {
  function t(e) {
    return parseInt(e, 10);
  }function n(e) {
    return u(e), e.data = e.items, delete e.items, e;
  }function i(e) {
    if (!e.error) return e.name || (e.name = e.title || e.message), e.picture || (e.picture = e.thumbnailLink), e.thumbnail || (e.thumbnail = e.thumbnailLink), "application/vnd.google-apps.folder" === e.mimeType && (e.type = "folder", e.files = "https://www.googleapis.com/drive/v2/files?q=%22" + e.id + "%22+in+parents"), e;
  }function o(e) {
    return { source: e.url, width: e.width, height: e.height };
  }function a(e) {
    if (u(e), "feed" in e && "entry" in e.feed) e.data = e.feed.entry.map(l), delete e.feed;else {
      if ("entry" in e) return l(e.entry);"items" in e ? (e.data = e.items.map(i), delete e.items) : i(e);
    }return e;
  }function r(e) {
    e.name = e.displayName || e.name, e.picture = e.picture || (e.image ? e.image.url : null), e.thumbnail = e.picture;
  }function s(e, t, n) {
    u(e);if ("feed" in e && "entry" in e.feed) {
      for (var i = n.query.access_token, o = 0; o < e.feed.entry.length; o++) {
        var a = e.feed.entry[o];if (a.id = a.id.$t, a.name = a.title.$t, delete a.title, a.gd$email && (a.email = a.gd$email && a.gd$email.length > 0 ? a.gd$email[0].address : null, a.emails = a.gd$email, delete a.gd$email), a.updated && (a.updated = a.updated.$t), a.link) {
          var r = a.link.length > 0 ? a.link[0].href : null;r && a.link[0].gd$etag && (r += (r.indexOf("?") > -1 ? "&" : "?") + "access_token=" + i, a.picture = r, a.thumbnail = r), delete a.link;
        }a.category && delete a.category;
      }e.data = e.feed.entry, delete e.feed;
    }return e;
  }function l(e) {
    var t,
        n = e.media$group,
        i = n.media$content.length ? n.media$content[0] : {},
        a = n.media$content || [],
        r = n.media$thumbnail || [],
        s = a.concat(r).map(o).sort(function (e, t) {
      return e.width - t.width;
    }),
        l = 0,
        u = { id: e.id.$t, name: e.title.$t, description: e.summary.$t, updated_time: e.updated.$t, created_time: e.published.$t, picture: i ? i.url : null, pictures: s, images: [], thumbnail: i ? i.url : null, width: i.width, height: i.height };if ("link" in e) for (l = 0; l < e.link.length; l++) {
      var c = e.link[l];if (c.rel.match(/\#feed$/)) {
        u.upload_location = u.files = u.photos = c.href;break;
      }
    }if ("category" in e && e.category.length) for (t = e.category, l = 0; l < t.length; l++) {
      t[l].scheme && t[l].scheme.match(/\#kind$/) && (u.type = t[l].term.replace(/^.*?\#/, ""));
    }return "media$thumbnail" in n && n.media$thumbnail.length && (t = n.media$thumbnail, u.thumbnail = t[0].url, u.images = t.map(o)), (t = n.media$content) && t.length && u.images.push(o(t[0])), u;
  }function u(e) {
    if ("feed" in e && e.feed.openSearch$itemsPerPage) {
      var n = t(e.feed.openSearch$itemsPerPage.$t),
          i = t(e.feed.openSearch$startIndex.$t);i + n < t(e.feed.openSearch$totalResults.$t) && (e.paging = { next: "?start=" + (i + n) });
    } else "nextPageToken" in e && (e.paging = { next: "?pageToken=" + e.nextPageToken });
  }function c(e, t) {
    var n = {};e.data && "undefined" != typeof HTMLInputElement && e.data instanceof HTMLInputElement && (e.data = { file: e.data }), !e.data.name && Object(Object(e.data.file).files).length && "post" === e.method && (e.data.name = e.data.file.files[0].name), "post" === e.method ? e.data = { title: e.data.name, parents: [{ id: e.data.parent || "root" }], file: e.data.file } : (n = e.data, e.data = {}, n.parent && (e.data.parents = [{ id: e.data.parent || "root" }]), n.file && (e.data.file = n.file), n.name && (e.data.title = n.name));var i;if ("file" in e.data && (i = e.data.file, delete e.data.file, "object" == (typeof i === "undefined" ? "undefined" : _typeof(i)) && "files" in i && (i = i.files), !i || !i.length)) t({ error: { code: "request_invalid", message: "There were no files attached with this request to upload" } });else {
      var o = new function () {
        function e(e) {
          var n = new FileReader();n.onload = function (n) {
            t(btoa(n.target.result), e.type + a + "Content-Transfer-Encoding: base64");
          }, n.readAsBinaryString(e);
        }function t(e, t) {
          n.push(a + "Content-Type: " + t + a + a + e), o--, s();
        }var n = [],
            i = (1e10 * Math.random()).toString(32),
            o = 0,
            a = "\r\n",
            r = a + "--" + i,
            s = function s() {},
            l = /^data\:([^;,]+(\;charset=[^;,]+)?)(\;base64)?,/i;this.append = function (n, i) {
          "string" != typeof n && "length" in Object(n) || (n = [n]);for (var r = 0; r < n.length; r++) {
            o++;var s = n[r];if ("undefined" != typeof File && s instanceof File || "undefined" != typeof Blob && s instanceof Blob) e(s);else if ("string" == typeof s && s.match(l)) {
              var u = s.match(l);t(s.replace(l, ""), u[1] + a + "Content-Transfer-Encoding: base64");
            } else t(s, i);
          }
        }, this.onready = function (e) {
          (s = function s() {
            0 === o && (n.unshift(""), n.push("--"), e(n.join(r), i), n = []);
          })();
        };
      }();o.append(JSON.stringify(e.data), "application/json"), i && o.append(i), o.onready(function (i, o) {
        e.headers["content-type"] = 'multipart/related; boundary="' + o + '"', e.data = i, t("upload/drive/v2/files" + (n.id ? "/" + n.id : "") + "?uploadType=multipart");
      });
    }
  }var f = "https://www.google.com/m8/feeds/contacts/default/full?v=3.0&alt=json&max-results=@{limit|1000}&start-index=@{start|1}";e.init({ google: { name: "Google Plus", oauth: { version: 2, auth: "https://accounts.google.com/o/oauth2/auth", grant: "https://accounts.google.com/o/oauth2/token" }, scope: { basic: "https://www.googleapis.com/auth/plus.me profile", email: "email", birthday: "", events: "", photos: "https://picasaweb.google.com/data/", videos: "http://gdata.youtube.com", friends: "https://www.google.com/m8/feeds, https://www.googleapis.com/auth/plus.login", files: "https://www.googleapis.com/auth/drive.readonly", publish: "", publish_files: "https://www.googleapis.com/auth/drive", share: "", create_event: "", offline_access: "" }, scope_delim: " ", login: function login(e) {
        "code" === e.qs.response_type && (e.qs.access_type = "offline"), e.options.force && (e.qs.approval_prompt = "force");
      }, base: "https://www.googleapis.com/", get: { me: "plus/v1/people/me", "me/friends": "plus/v1/people/me/people/visible?maxResults=@{limit|100}", "me/following": f, "me/followers": f, "me/contacts": f, "me/share": "plus/v1/people/me/activities/public?maxResults=@{limit|100}", "me/feed": "plus/v1/people/me/activities/public?maxResults=@{limit|100}", "me/albums": "https://picasaweb.google.com/data/feed/api/user/default?alt=json&max-results=@{limit|100}&start-index=@{start|1}", "me/album": function meAlbum(e, t) {
          var n = e.query.id;delete e.query.id, t(n.replace("/entry/", "/feed/"));
        }, "me/photos": "https://picasaweb.google.com/data/feed/api/user/default?alt=json&kind=photo&max-results=@{limit|100}&start-index=@{start|1}", "me/file": "drive/v2/files/@{id}", "me/files": "drive/v2/files?q=%22@{parent|root}%22+in+parents+and+trashed=false&maxResults=@{limit|100}", "me/folders": "drive/v2/files?q=%22@{id|root}%22+in+parents+and+mimeType+=+%22application/vnd.google-apps.folder%22+and+trashed=false&maxResults=@{limit|100}", "me/folder": "drive/v2/files?q=%22@{id|root}%22+in+parents+and+trashed=false&maxResults=@{limit|100}" }, post: { "me/files": c, "me/folders": function meFolders(e, t) {
          e.data = { title: e.data.name, parents: [{ id: e.data.parent || "root" }], mimeType: "application/vnd.google-apps.folder" }, t("drive/v2/files");
        } }, put: { "me/files": c }, del: { "me/files": "drive/v2/files/@{id}", "me/folder": "drive/v2/files/@{id}" }, patch: { "me/file": "drive/v2/files/@{id}" }, wrap: { me: function me(e) {
          return e.id && (e.last_name = e.family_name || (e.name ? e.name.familyName : null), e.first_name = e.given_name || (e.name ? e.name.givenName : null), e.emails && e.emails.length && (e.email = e.emails[0].value), r(e)), e;
        }, "me/friends": function meFriends(e) {
          return e.items && (u(e), e.data = e.items, e.data.forEach(r), delete e.items), e;
        }, "me/contacts": s, "me/followers": s, "me/following": s, "me/share": n, "me/feed": n, "me/albums": a, "me/photos": function mePhotos(e) {
          e.data = e.feed.entry.map(l), delete e.feed;
        }, default: a }, xhr: function xhr(t) {
        return "post" === t.method || "put" === t.method ? function (e) {
          if ("object" == _typeof(e.data)) try {
            e.data = JSON.stringify(e.data), e.headers["content-type"] = "application/json";
          } catch (e) {}
        }(t) : "patch" === t.method && (e.utils.extend(t.query, t.data), t.data = null), !0;
      }, form: !1 } });
}(hello), function (e) {
  function t(e) {
    return "string" == typeof e ? { error: { code: "invalid_request", message: e } } : (e && "meta" in e && "error_type" in e.meta && (e.error = { code: e.meta.error_type, message: e.meta.error_message }), e);
  }function n(e) {
    return o(e), e && "data" in e && e.data.forEach(i), e;
  }function i(e) {
    e.id && (e.thumbnail = e.profile_picture, e.name = e.full_name || e.username);
  }function o(e) {
    "pagination" in e && (e.paging = { next: e.pagination.next_url }, delete e.pagination);
  }hello.init({ instagram: { name: "Instagram", oauth: { version: 2, auth: "https://instagram.com/oauth/authorize/", grant: "https://api.instagram.com/oauth/access_token" }, refresh: !0, scope: { basic: "basic", photos: "", friends: "relationships", publish: "likes comments", email: "", share: "", publish_files: "", files: "", videos: "", offline_access: "" }, scope_delim: " ", base: "https://api.instagram.com/v1/", get: { me: "users/self", "me/feed": "users/self/feed?count=@{limit|100}", "me/photos": "users/self/media/recent?min_id=0&count=@{limit|100}", "me/friends": "users/self/follows?count=@{limit|100}", "me/following": "users/self/follows?count=@{limit|100}", "me/followers": "users/self/followed-by?count=@{limit|100}", "friend/photos": "users/@{id}/media/recent?min_id=0&count=@{limit|100}" }, post: { "me/like": function meLike(e, t) {
          var n = e.data.id;e.data = {}, t("media/" + n + "/likes");
        } }, del: { "me/like": "media/@{id}/likes" }, wrap: { me: function me(e) {
          return t(e), "data" in e && (e.id = e.data.id, e.thumbnail = e.data.profile_picture, e.name = e.data.full_name || e.data.username), e;
        }, "me/friends": n, "me/following": n, "me/followers": n, "me/photos": function mePhotos(e) {
          return t(e), o(e), "data" in e && (e.data = e.data.filter(function (e) {
            return "image" === e.type;
          }), e.data.forEach(function (e) {
            e.name = e.caption ? e.caption.text : null, e.thumbnail = e.images.thumbnail.url, e.picture = e.images.standard_resolution.url, e.pictures = Object.keys(e.images).map(function (t) {
              return function (e) {
                return { source: e.url, width: e.width, height: e.height };
              }(e.images[t]);
            }).sort(function (e, t) {
              return e.width - t.width;
            });
          })), e;
        }, default: function _default(e) {
          return e = t(e), o(e), e;
        } }, xhr: function xhr(e, t) {
        var n = e.method,
            i = "get" !== n;return i && ("post" !== n && "put" !== n || !e.query.access_token || (e.data.access_token = e.query.access_token, delete e.query.access_token), e.proxy = i), i;
      }, form: !1 } });
}(), function (e) {
  function t(e, t) {
    var n, i;return e && "Message" in e && (i = e.Message, delete e.Message, "ErrorCode" in e ? (n = e.ErrorCode, delete e.ErrorCode) : n = function (e) {
      switch (e.statusCode) {case 400:
          return "invalid_request";case 403:
          return "stale_token";case 401:
          return "invalid_token";case 500:default:
          return "server_error";}
    }(t), e.error = { code: n, message: i, details: e }), e;
  }hello.init({ joinme: { name: "join.me", oauth: { version: 2, auth: "https://secure.join.me/api/public/v1/auth/oauth2", grant: "https://secure.join.me/api/public/v1/auth/oauth2" }, refresh: !1, scope: { basic: "user_info", user: "user_info", scheduler: "scheduler", start: "start_meeting", email: "", friends: "", share: "", publish: "", photos: "", publish_files: "", files: "", videos: "", offline_access: "" }, scope_delim: " ", login: function login(e) {
        e.options.popup.width = 400, e.options.popup.height = 700;
      }, base: "https://api.join.me/v1/", get: { me: "user", meetings: "meetings", "meetings/info": "meetings/@{id}" }, post: { "meetings/start/adhoc": function meetingsStartAdhoc(e, t) {
          t("meetings/start");
        }, "meetings/start/scheduled": function meetingsStartScheduled(e, t) {
          var n = e.data.meetingId;e.data = {}, t("meetings/" + n + "/start");
        }, "meetings/schedule": function meetingsSchedule(e, t) {
          t("meetings");
        } }, patch: { "meetings/update": function meetingsUpdate(e, t) {
          t("meetings/" + e.data.meetingId);
        } }, del: { "meetings/delete": "meetings/@{id}" }, wrap: { me: function me(e, n) {
          return t(e, n), e.email ? (e.name = e.fullName, e.first_name = e.name.split(" ")[0], e.last_name = e.name.split(" ")[1], e.id = e.email, e) : e;
        }, default: function _default(e, n) {
          return t(e, n), e;
        } }, xhr: function xhr(e, t) {
        var n = t.access_token;return delete t.access_token, e.headers.Authorization = "Bearer " + n, "get" !== e.method && e.data && (e.headers["Content-Type"] = "application/json", "object" == _typeof(e.data) && (e.data = JSON.stringify(e.data))), "put" === e.method && (e.method = "patch"), !0;
      } } });
}(), function (e) {
  function t(e) {
    e && "errorCode" in e && (e.error = { code: e.status, message: e.message });
  }function n(e) {
    if (!e.error) return e.first_name = e.firstName, e.last_name = e.lastName, e.name = e.formattedName || e.first_name + " " + e.last_name, e.thumbnail = e.pictureUrl, e.email = e.emailAddress, e;
  }function i(e) {
    return t(e), o(e), e.values && (e.data = e.values.map(n), delete e.values), e;
  }function o(e) {
    "_count" in e && "_start" in e && e._count + e._start < e._total && (e.paging = { next: "?start=" + (e._start + e._count) + "&count=" + e._count });
  }function a(e) {
    e.access_token && (e.oauth2_access_token = e.access_token, delete e.access_token);
  }function r(e, t) {
    e.headers["x-li-format"] = "json";var n = e.data.id;e.data = ("delete" !== e.method).toString(), e.method = "put", t("people/~/network/updates/key=" + n + "/is-liked");
  }hello.init({ linkedin: { oauth: { version: 2, response_type: "code", auth: "https://www.linkedin.com/uas/oauth2/authorization", grant: "https://www.linkedin.com/uas/oauth2/accessToken" }, refresh: !0, scope: { basic: "r_basicprofile", email: "r_emailaddress", files: "", friends: "", photos: "", publish: "w_share", publish_files: "w_share", share: "", videos: "", offline_access: "" }, scope_delim: " ", base: "https://api.linkedin.com/v1/", get: { me: "people/~:(picture-url,first-name,last-name,id,formatted-name,email-address)", "me/share": "people/~/network/updates?count=@{limit|250}" }, post: { "me/share": function meShare(e, t) {
          var n = { visibility: { code: "anyone" } };e.data.id ? n.attribution = { share: { id: e.data.id } } : (n.comment = e.data.message, e.data.picture && e.data.link && (n.content = { "submitted-url": e.data.link, "submitted-image-url": e.data.picture })), e.data = JSON.stringify(n), t("people/~/shares?format=json");
        }, "me/like": r }, del: { "me/like": r }, wrap: { me: function me(e) {
          return t(e), n(e), e;
        }, "me/friends": i, "me/following": i, "me/followers": i, "me/share": function meShare(e) {
          return t(e), o(e), e.values && (e.data = e.values.map(n), e.data.forEach(function (e) {
            e.message = e.headline;
          }), delete e.values), e;
        }, default: function _default(e, n) {
          t(e), function (e, t) {
            "{}" === JSON.stringify(e) && 200 === t.statusCode && (e.success = !0);
          }(e, n), o(e);
        } }, jsonp: function jsonp(e, t) {
        a(t), "get" === e.method && (t.format = "jsonp", t["error-callback"] = e.callbackID);
      }, xhr: function xhr(e, t) {
        return "get" !== e.method && (a(t), e.headers["Content-Type"] = "application/json", e.headers["x-li-format"] = "json", e.proxy = !0, !0);
      } } });
}(), function (e) {
  function t(e, t) {
    var n = t.access_token;return delete t.access_token, t.oauth_token = n, t["_status_code_map[302]"] = 200, !0;
  }function n(e) {
    return e.id && (e.picture = e.avatar_url, e.thumbnail = e.avatar_url, e.name = e.username || e.full_name), e;
  }hello.init({ soundcloud: { name: "SoundCloud", oauth: { version: 2, auth: "https://soundcloud.com/connect", grant: "https://soundcloud.com/oauth2/token" }, base: "https://api.soundcloud.com/", get: { me: "me.json", "me/friends": "me/followings.json", "me/followers": "me/followers.json", "me/following": "me/followings.json", default: function _default(e, t) {
          t(e.path + ".json");
        } }, wrap: { me: function me(e) {
          return n(e), e;
        }, default: function _default(e) {
          return Array.isArray(e) && (e = { data: e.map(n) }), function (e) {
            "next_href" in e && (e.paging = { next: e.next_href });
          }(e), e;
        } }, xhr: t, jsonp: t } });
}(), function (e) {
  function t(e) {
    return e.id && (e.name = e.display_name, e.thumbnail = e.images.length ? e.images[0].url : null, e.picture = e.thumbnail), e;
  }function n(e) {
    e && "next" in e && (e.paging = { next: e.next }, delete e.next);
  }hello.init({ spotify: { name: "Spotify", oauth: { version: 2, auth: "https://accounts.spotify.com/authorize", grant: "https://accounts.spotify.com/api/token" }, scope_delim: " ", scope: { basic: "", photos: "", friends: "user-follow-read", publish: "user-library-read", email: "user-read-email", share: "", publish_files: "", files: "", videos: "", offline_access: "" }, base: "https://api.spotify.com", get: { me: "/v1/me", "me/following": "/v1/me/following?type=artist", "me/like": "/v1/me/tracks" }, wrap: { me: t, "me/following": function meFollowing(e) {
          return n(e), e && "artists" in e && (e.data = e.artists.items.forEach(t)), e;
        }, "me/like": function meLike(e) {
          return n(e), e.data = e.items, e;
        } }, xhr: function xhr(e, t) {
        var n = t.access_token;return delete t.access_token, e.headers.Authorization = "Bearer " + n, !0;
      }, jsonp: !1 } });
}(), function (e) {
  function t(e) {
    if (e.id) {
      if (e.name) {
        var t = e.name.split(" ");e.first_name = t.shift(), e.last_name = t.join(" ");
      }e.thumbnail = e.profile_image_url_https || e.profile_image_url;
    }return e;
  }function n(e) {
    return i(e), o(e), e.users && (e.data = e.users.map(t), delete e.users), e;
  }function i(e) {
    if (e.errors) {
      var t = e.errors[0];e.error = { code: "request_failed", message: t.message };
    }
  }function o(e) {
    "next_cursor_str" in e && (e.paging = { next: "?cursor=" + e.next_cursor_str });
  }var a = "https://api.twitter.com/";e.init({ twitter: { oauth: { version: "1.0a", auth: a + "oauth/authenticate", request: a + "oauth/request_token", token: a + "oauth/access_token" }, login: function login(e) {
        var t = "?force_login=true";this.oauth.auth = this.oauth.auth.replace(t, "") + (e.options.force ? t : "");
      }, base: a + "1.1/", get: { me: "account/verify_credentials.json", "me/friends": "friends/list.json?count=@{limit|200}", "me/following": "friends/list.json?count=@{limit|200}", "me/followers": "followers/list.json?count=@{limit|200}", "me/share": "statuses/user_timeline.json?count=@{limit|200}", "me/like": "favorites/list.json?count=@{limit|200}" }, post: { "me/share": function meShare(t, n) {
          var i = t.data;t.data = null;var o = [];i.message && (o.push(i.message), delete i.message), i.link && (o.push(i.link), delete i.link), i.picture && (o.push(i.picture), delete i.picture), o.length && (i.status = o.join(" ")), i.file ? (i["media[]"] = i.file, delete i.file, t.data = i, n("statuses/update_with_media.json")) : "id" in i ? n("statuses/retweet/" + i.id + ".json") : (e.utils.extend(t.query, i), n("statuses/update.json?include_entities=1"));
        }, "me/like": function meLike(e, t) {
          var n = e.data.id;e.data = null, t("favorites/create.json?id=" + n);
        } }, del: { "me/like": function meLike() {
          p.method = "post";var e = p.data.id;p.data = null, callback("favorites/destroy.json?id=" + e);
        } }, wrap: { me: function me(e) {
          return i(e), t(e), e;
        }, "me/friends": n, "me/followers": n, "me/following": n, "me/share": function meShare(e) {
          return i(e), o(e), !e.error && "length" in e ? { data: e } : e;
        }, default: function _default(e) {
          return e = function (e) {
            return Array.isArray(e) ? { data: e } : e;
          }(e), o(e), e;
        } }, xhr: function xhr(e) {
        return "get" !== e.method;
      } } });
}(hello), function (e) {
  hello.init({ vk: { name: "Vk", oauth: { version: 2, auth: "https://oauth.vk.com/authorize", grant: "https://oauth.vk.com/access_token" }, scope: { email: "email", friends: "friends", photos: "photos", videos: "video", share: "share", offline_access: "offline" }, refresh: !0, login: function login(e) {
        e.qs.display = window.navigator && window.navigator.userAgent && /ipad|phone|phone|android/.test(window.navigator.userAgent.toLowerCase()) ? "mobile" : "popup";
      }, base: "https://api.vk.com/method/", get: { me: function me(e, t) {
          e.query.fields = "id,first_name,last_name,photo_max", t("users.get");
        } }, wrap: { me: function me(e, t, n) {
          return function (e) {
            if (e.error) {
              var t = e.error;e.error = { code: t.error_code, message: t.error_msg };
            }
          }(e), function (e, t) {
            return null !== e && "response" in e && null !== e.response && e.response.length && ((e = e.response[0]).id = e.uid, e.thumbnail = e.picture = e.photo_max, e.name = e.first_name + " " + e.last_name, t.authResponse && null !== t.authResponse.email && (e.email = t.authResponse.email)), e;
          }(e, n);
        } }, xhr: !1, jsonp: !0, form: !1 } });
}(), function (e) {
  function t(e) {
    return "data" in e && e.data.forEach(function (e) {
      e.picture && (e.thumbnail = e.picture), e.images && (e.pictures = e.images.map(n).sort(function (e, t) {
        return e.width - t.width;
      }));
    }), e;
  }function n(e) {
    return { width: e.width, height: e.height, source: e.source };
  }function i(e, t, n) {
    if (e.id) {
      var i = n.query.access_token;if (e.emails && (e.email = e.emails.preferred), !1 !== e.is_friend) {
        var o = e.user_id || e.id;e.thumbnail = e.picture = "https://apis.live.net/v5.0/" + o + "/picture?access_token=" + i;
      }
    }return e;
  }function o(e, t, n) {
    return "data" in e && e.data.forEach(function (e) {
      i(e, 0, n);
    }), e;
  }e.init({ windows: { name: "Windows live", oauth: { version: 2, auth: "https://login.live.com/oauth20_authorize.srf", grant: "https://login.live.com/oauth20_token.srf" }, refresh: !0, logout: function logout() {
        return "http://login.live.com/oauth20_logout.srf?ts=" + new Date().getTime();
      }, scope: { basic: "wl.signin,wl.basic", email: "wl.emails", birthday: "wl.birthday", events: "wl.calendars", photos: "wl.photos", videos: "wl.photos", friends: "wl.contacts_emails", files: "wl.skydrive", publish: "wl.share", publish_files: "wl.skydrive_update", share: "wl.share", create_event: "wl.calendars_update,wl.events_create", offline_access: "wl.offline_access" }, base: "https://apis.live.net/v5.0/", get: { me: "me", "me/friends": "me/friends", "me/following": "me/contacts", "me/followers": "me/friends", "me/contacts": "me/contacts", "me/albums": "me/albums", "me/album": "@{id}/files", "me/photo": "@{id}", "me/files": "@{parent|me/skydrive}/files", "me/folders": "@{id|me/skydrive}/files", "me/folder": "@{id|me/skydrive}/files" }, post: { "me/albums": "me/albums", "me/album": "@{id}/files/", "me/folders": "@{id|me/skydrive/}", "me/files": "@{parent|me/skydrive}/files" }, del: { "me/album": "@{id}", "me/photo": "@{id}", "me/folder": "@{id}", "me/files": "@{id}" }, wrap: { me: i, "me/friends": o, "me/contacts": o, "me/followers": o, "me/following": o, "me/albums": function meAlbums(e) {
          return "data" in e && e.data.forEach(function (e) {
            e.photos = e.files = "https://apis.live.net/v5.0/" + e.id + "/photos";
          }), e;
        }, "me/photos": t, default: t }, xhr: function xhr(t) {
        return "get" === t.method || "delete" === t.method || e.utils.hasBinary(t.data) || ("string" == typeof t.data.file ? t.data.file = e.utils.toBlob(t.data.file) : (t.data = JSON.stringify(t.data), t.headers = { "Content-Type": "application/json" })), !0;
      }, jsonp: function jsonp(t) {
        "get" === t.method || e.utils.hasBinary(t.data) || (t.data.method = t.method, t.method = "get");
      } } });
}(hello), function (e) {
  function t(e) {
    e && "meta" in e && "error_type" in e.meta && (e.error = { code: e.meta.error_type, message: e.meta.error_message });
  }function n(e, n, a) {
    t(e), o(e, n, a);return e.query && e.query.results && e.query.results.contact && (e.data = e.query.results.contact, delete e.query, Array.isArray(e.data) || (e.data = [e.data]), e.data.forEach(i)), e;
  }function i(e) {
    e.id = null, !e.fields || e.fields instanceof Array || (e.fields = [e.fields]), (e.fields || []).forEach(function (t) {
      "email" === t.type && (e.email = t.value), "name" === t.type && (e.first_name = t.value.givenName, e.last_name = t.value.familyName, e.name = t.value.givenName + " " + t.value.familyName), "yahooid" === t.type && (e.id = t.value);
    });
  }function o(e, t, n) {
    return e.query && e.query.count && n.options && (e.paging = { next: "?start=" + (e.query.count + (+n.options.start || 1)) }), e;
  }function a(e) {
    return "https://query.yahooapis.com/v1/yql?q=" + (e + " limit @{limit|100} offset @{start|0}").replace(/\s/g, "%20") + "&format=json";
  }hello.init({ yahoo: { oauth: { version: "1.0a", auth: "https://api.login.yahoo.com/oauth/v2/request_auth", request: "https://api.login.yahoo.com/oauth/v2/get_request_token", token: "https://api.login.yahoo.com/oauth/v2/get_token" }, login: function login(e) {
        e.options.popup.width = 560;try {
          delete e.qs.state.scope;
        } catch (e) {}
      }, base: "https://social.yahooapis.com/v1/", get: { me: a("select * from social.profile(0) where guid=me"), "me/friends": a("select * from social.contacts(0) where guid=me"), "me/following": a("select * from social.contacts(0) where guid=me") }, wrap: { me: function me(e) {
          if (t(e), e.query && e.query.results && e.query.results.profile) {
            (e = e.query.results.profile).id = e.guid, e.last_name = e.familyName, e.first_name = e.givenName || e.nickname;var n = [];e.first_name && n.push(e.first_name), e.last_name && n.push(e.last_name), e.name = n.join(" "), e.email = e.emails && e.emails[0] ? e.emails[0].handle : null, e.thumbnail = e.image ? e.image.imageUrl : null;
          }return e;
        }, "me/friends": n, "me/following": n, default: o } } });
}(), "function" == typeof define && define.amd && define(function () {
  return hello;
}), "object" == (typeof module === "undefined" ? "undefined" : _typeof(module)) && module.exports && (module.exports = hello);
},{"process":6}],34:[function(require,module,exports) {

var global = (1, eval)('this');
var OldModule = module.bundle.Module;
function Module(moduleName) {
  OldModule.call(this, moduleName);
  this.hot = {
    accept: function (fn) {
      this._acceptCallback = fn || function () {};
    },
    dispose: function (fn) {
      this._disposeCallback = fn;
    }
  };
}

module.bundle.Module = Module;

var parent = module.bundle.parent;
if ((!parent || !parent.isParcelRequire) && typeof WebSocket !== 'undefined') {
  var hostname = '' || location.hostname;
  var protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  var ws = new WebSocket(protocol + '://' + hostname + ':' + '58533' + '/');
  ws.onmessage = function (event) {
    var data = JSON.parse(event.data);

    if (data.type === 'update') {
      data.assets.forEach(function (asset) {
        hmrApply(global.require, asset);
      });

      data.assets.forEach(function (asset) {
        if (!asset.isNew) {
          hmrAccept(global.require, asset.id);
        }
      });
    }

    if (data.type === 'reload') {
      ws.close();
      ws.onclose = function () {
        location.reload();
      };
    }

    if (data.type === 'error-resolved') {
      console.log('[parcel] ??? Error resolved');
    }

    if (data.type === 'error') {
      console.error('[parcel] ????  ' + data.error.message + '\n' + 'data.error.stack');
    }
  };
}

function getParents(bundle, id) {
  var modules = bundle.modules;
  if (!modules) {
    return [];
  }

  var parents = [];
  var k, d, dep;

  for (k in modules) {
    for (d in modules[k][1]) {
      dep = modules[k][1][d];
      if (dep === id || Array.isArray(dep) && dep[dep.length - 1] === id) {
        parents.push(+k);
      }
    }
  }

  if (bundle.parent) {
    parents = parents.concat(getParents(bundle.parent, id));
  }

  return parents;
}

function hmrApply(bundle, asset) {
  var modules = bundle.modules;
  if (!modules) {
    return;
  }

  if (modules[asset.id] || !bundle.parent) {
    var fn = new Function('require', 'module', 'exports', asset.generated.js);
    asset.isNew = !modules[asset.id];
    modules[asset.id] = [fn, asset.deps];
  } else if (bundle.parent) {
    hmrApply(bundle.parent, asset);
  }
}

function hmrAccept(bundle, id) {
  var modules = bundle.modules;
  if (!modules) {
    return;
  }

  if (!modules[id] && bundle.parent) {
    return hmrAccept(bundle.parent, id);
  }

  var cached = bundle.cache[id];
  if (cached && cached.hot._disposeCallback) {
    cached.hot._disposeCallback();
  }

  delete bundle.cache[id];
  bundle(id);

  cached = bundle.cache[id];
  if (cached && cached.hot && cached.hot._acceptCallback) {
    cached.hot._acceptCallback();
    return true;
  }

  return getParents(global.require, id).some(function (id) {
    return hmrAccept(global.require, id);
  });
}
},{}]},{},[34,5])
//# sourceMappingURL=/dist/224c2fc58a53ef446883b1d32c9be2fe.map