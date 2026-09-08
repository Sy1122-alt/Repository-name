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
__vue_options__.__file = "D:\\weex-hackernews-master\\src\\myweex.vue"
__vue_options__.render = __vue_template__.render
__vue_options__.staticRenderFns = __vue_template__.staticRenderFns
__vue_options__._scopeId = "data-v-5c7cfb67"
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
  "image": {
    "width": "700",
    "height": "700"
  },
  "slider": {
    "marginTop": "25",
    "marginLeft": "25",
    "width": "700",
    "height": "700",
    "borderWidth": "2",
    "borderStyle": "solid",
    "borderColor": "#41B883"
  },
  "title": {
    "position": "absolute",
    "top": "20",
    "left": "20",
    "paddingLeft": "20",
    "width": "200",
    "color": "#FFFFFF",
    "fontSize": "36",
    "lineHeight": "60",
    "backgroundColor": "rgba(0,0,0,0.3)"
  },
  "frame": {
    "width": "700",
    "height": "700",
    "position": "relative"
  },
  "indicator": {
    "width": "700",
    "height": "700",
    "itemColor": "#008000",
    "itemSelectedColor": "#FF0000",
    "itemSize": "50",
    "position": "absolute",
    "top": "200",
    "left": "200"
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
//
//
//
//
//
//
//
//
//


exports.default = {
  data: function data() {
    return {
      imageList: [{ title: 'item A', src: 'https://gd2.alicdn.com/bao/uploaded/i2/T14H1LFwBcXXXXXXXX_!!0-item_pic.jpg' }, { title: 'item B', src: 'https://gd1.alicdn.com/bao/uploaded/i1/TB1PXJCJFXXXXciXFXXXXXXXXXX_!!0-item_pic.jpg' }, { title: 'item C', src: 'https://gd3.alicdn.com/bao/uploaded/i3/TB1x6hYLXXXXXazXVXXXXXXXXXX_!!0-item_pic.jpg' }]
    };
  },

  methods: {

    pay: function pay() {
      weex.requireModule("moWX").pay(function (pay) {
        weex.requireModule("modal").toast({
          message: pay,
          duration: 0.8
        });
      });
    },

    onchange: function onchange(event) {
      console.log('changed:', event.index);
    },

    share: function share() {
      weex.requireModule("moWX").share(function (share) {
        console.log("share", share);
        weex.requireModule("modal").toast({
          message: share,
          duration: 5
        });
      });
    },

    login: function login() {
      weex.requireModule("moWX").login("这是登陆");
    }

  }
};

/***/ }),
/* 3 */
/***/ (function(module, exports) {

module.exports={render:function (){var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;
  return _c('scroller', [_c('div', [_c('text', {
    staticClass: ["text"],
    staticStyle: {
      fontSize: "80",
      padding: "20",
      color: "#F0F",
      textAlign: "right"
    },
    on: {
      "click": _vm.pay
    }
  }, [_vm._v("QQ好友")]), _c('text', {
    staticClass: ["text1"],
    staticStyle: {
      fontSize: "80",
      padding: "20",
      color: "red"
    },
    on: {
      "click": _vm.login
    }
  }, [_vm._v(" qq空间")]), _c('text', {
    staticClass: ["text2"],
    staticStyle: {
      fontSize: "80",
      padding: "20",
      color: "#0000"
    },
    on: {
      "click": _vm.share
    }
  }, [_vm._v("好友")]), _c('text', {
    staticClass: ["button"],
    staticStyle: {
      fontSize: "80",
      paddingTop: "10px",
      paddingLeft: "10px",
      color: "#0000",
      borderWidth: "2px",
      borderStyle: "solid",
      borderColor: "#BBB",
      width: "100px",
      height: "100px",
      marginTop: "20px",
      marginLeft: "20px",
      backgroundColor: "#EEE"
    }
  }, [_vm._v("按钮")]), _c('image', {
    staticStyle: {
      width: "400px",
      height: "200px",
      marginLeft: "20px",
      marginTop: "30px"
    },
    attrs: {
      "src": "http://imgs.52jiaoshi.com/15154926205a54950ca0943.jpg"
    }
  }), _c('slider', {
    staticClass: ["slider"],
    attrs: {
      "interval": "4500",
      "autoPlay": "true"
    },
    on: {
      "change": _vm.onchange
    }
  }, [_vm._l((_vm.imageList), function(img) {
    return _c('div', {
      staticClass: ["frame"]
    }, [_c('image', {
      staticClass: ["image"],
      attrs: {
        "resize": "cover",
        "src": img.src
      }
    }), _c('text', {
      staticClass: ["title"]
    }, [_vm._v(_vm._s(img.title))])])
  }), _c('indicator', {
    staticClass: ["indicator"]
  })], 2)])])
},staticRenderFns: []}
module.exports.render._withStripped = true

/***/ })
/******/ ]);