'use strict';

angular.module('pyparserApp')
  .factory('loginRequired', function ($q, $location, AuthService) {
    var defer = $q.defer();
    if (!AuthService.isAuthenticated()){
        $location.path('/auth');
        defer.reject("not_logged_in");
        }
    else
        defer.resolve();
    return defer.promise
  });
