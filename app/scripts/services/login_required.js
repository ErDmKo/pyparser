'use strict';

angular.module('pyparserApp')
  .factory('loginRequired', function ($q, $location, AuthService) {
    var defer = $q.defer();
    AuthService.isAuthenticated().then(function(auth_info){
        if(!auth_info){
            $location.path('/auth');
            defer.reject("not_logged_in");
            }
        else
            defer.resolve();
        });
    return defer.promise
  });
