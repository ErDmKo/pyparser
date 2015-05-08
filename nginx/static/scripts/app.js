'use strict';

Array.prototype.chunk = function(chunkSize) {
    var array=this;
    return [].concat.apply([],
        array.map(function(elem,i) {
            return i%chunkSize ? [] : [array.slice(i,i+chunkSize)];
        })
    );
}

angular
  .module('pyparserApp', [
    'wu.masonry',
    'ngCookies',
    'ngResource',
    'ngSanitize',
    'ngRoute'
  ])
  .config(function ($routeProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/main.html',
        controller: 'MainControler',
        resolve: {load: ['loginRequired', function(lgR){return lgR.test()}]},
      })
      .when('/auth', {
        templateUrl: 'views/auth.html',
        controller: 'LoginController'
      })
      .otherwise({
        redirectTo: '/',
        resolve: {load: ['loginRequired', function(lgR){return lgR.test()}]},
      });
  });
