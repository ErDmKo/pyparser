'use strict';

angular
  .module('pyparserApp', [
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
        resolve: {load: 'loginRequired'}
      });
  });
