// { "framework": "Vue"} 

/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 0);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ (function(module, exports, __webpack_require__) {

var __vue_exports__, __vue_options__
var __vue_styles__ = []

/* styles */
__vue_styles__.push(__webpack_require__(1)
)

/* script */
__vue_exports__ = __webpack_require__(2)

/* template */
var __vue_template__ = __webpack_require__(3)
__vue_options__ = __vue_exports__ = __vue_exports__ || {}
if (
  typeof __vue_exports__.default === "object" ||
  typeof __vue_exports__.default === "function"
) {
if (Object.keys(__vue_exports__).some(function (key) { return key !== "default" && key !== "__esModule" })) {console.error("named exports are not supported in *.vue files.")}
__vue_options__ = __vue_exports__ = __vue_exports__.default
}
if (typeof __vue_options__ === "function") {
  __vue_options__ = __vue_options__.options
}
__vue_options__.__file = "D:\\weex-hackernews-master\\src\\test.vue"
__vue_options__.render = __vue_template__.render
__vue_options__.staticRenderFns = __vue_template__.staticRenderFns
__vue_options__._scopeId = "data-v-36c2ce4c"
__vue_options__.style = __vue_options__.style || {}
__vue_styles__.forEach(function (module) {
  for (var name in module) {
    __vue_options__.style[name] = module[name]
  }
})
if (typeof __register_static_styles__ === "function") {
  __register_static_styles__(__vue_options__._scopeId, __vue_styles__)
}

module.exports = __vue_exports__
module.exports.el = 'true'
new Vue(module.exports)


/***/ }),
/* 1 */
/***/ (function(module, exports) {

module.exports = {
  "mytext": {
    "marginTop": "150",
    "paddingLeft": "40",
    "fontFamily": "Verdana, Geneva, sans-serif",
    "fontSize": "32",
    "marginBottom": "15",
    "color": "#800080"
  },
  "mytext1": {
    "paddingLeft": "40",
    "fontFamily": "Verdana, Geneva, sans-serif",
    "fontSize": "32",
    "marginBottom": "15",
    "color": "#800080"
  },
  "mytext2": {
    "paddingLeft": "40",
    "fontFamily": "Verdana, Geneva, sans-serif",
    "fontSize": "32",
    "marginBottom": "15",
    "color": "#800080"
  },
  "mytext3": {
    "paddingLeft": "40",
    "fontFamily": "Verdana, Geneva, sans-serif",
    "fontSize": "32",
    "marginBottom": "15",
    "color": "#800080"
  },
  "image": {
    "width": "100",
    "height": "100"
  },
  "my": {
    "height": "1000",
    "width": "100"
  },
  "my1": {
    "height": "1000",
    "width": "100"
  }
}

/***/ }),
/* 2 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";


Object.defineProperty(exports, "__esModule", {
  value: true
});
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//


//const wxMo = weex.requireModule('WxCustomModule');

exports.default = {

  methods: {
    onclick: function onclick() {

      weex.requireModule('WxCustomModule').nativego(function (ret) {
        //回调执行
        var modal = weex.requireModule('modal');
        modal.toast({
          message: ret,
          duration: 0.35
        });
      });
    },
    jsbrigeOC: function jsbrigeOC(str) {

      weex.requireModule('WxCustomModule').jsBrigeOC(str, function (ret) {
        //回调执行
        var modal = weex.requireModule('modal');
        modal.toast({
          message: ret,
          duration: 0.35
        });
      });
    }
  }
};

/***/ }),
/* 3 */
/***/ (function(module, exports) {

module.exports={render:function (){var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;
  return _c('div', {
    staticClass: ["user-view"]
  }, [_c('scroller', [_c('text', {
    staticClass: ["mytext"],
    on: {
      "click": function($event) {
        _vm.jsbrigeOC('微信支付')
      }
    }
  }, [_vm._v("微信支付")]), _c('text', {
    staticClass: ["mytext1"],
    on: {
      "click": function($event) {
        _vm.jsbrigeOC('支付宝支付')
      }
    }
  }, [_vm._v("支付宝支付")]), _c('text', {
    staticClass: ["mytext2"],
    on: {
      "click": function($event) {
        _vm.jsbrigeOC('分享')
      }
    }
  }, [_vm._v("分享")]), _c('text', {
    staticClass: ["mytext3"],
    on: {
      "click": function($event) {
        _vm.jsbrigeOC('微信登录')
      }
    }
  }, [_vm._v("微信登录")]), _c('image', {
    staticStyle: {
      width: "200px",
      height: "200px"
    },
    attrs: {
      "src": "https://vuejs.org/images/logo.png"
    }
  }), _c('WxCustomView', {
    staticClass: ["my"],
    attrs: {
      "src": "https://tapi.jet.netkingol.com/bridge/index.js"
    }
  }), _c('WxCustomView', {
    staticClass: ["my1"],
    attrs: {
      "src": "https://tapi.jet.netkingol.com/bridge/index.js"
    }
  })], 1)])
},staticRenderFns: []}
module.exports.render._withStripped = true

/***/ })
/******/ ]);