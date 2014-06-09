'use strict';

angular.module('pyparserApp')
  .factory('loginRequired', function ($q, $location, AuthService, Session) {
    var self = this;
    self.defer = $q.defer();
    return {
        test: function(){
            if (!Session.id)
                {
                self.defer = $q.defer();
                AuthService.isAuthenticated().then(function(auth_info){
                    if(!auth_info){
                        $location.path('/auth');
                        self.defer.reject("not_logged_in");
                        }
                    else
                        self.defer.resolve();
                    });
                }
            return self.promise
            },
        promise: self.defer.promise,
    }
  });
