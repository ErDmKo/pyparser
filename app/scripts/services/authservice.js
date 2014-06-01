'use strict';

angular.module('pyparserApp')
  .factory('AuthService', function ($q, $http, Session) {
    var auth_url = 'server/auth/login';
    return {
      login: function (form) {
        return $http
            .post(auth_url, form)
            .then(function (res) {
                Session.create(res.data.login);
            });
        },
      isAuthenticated: function () {
        if (Session.id)
            return $q.defer().resolve(true).promise;
        else
            return $http
                .get(auth_url)
                .then(function (res) {
                    return res.data.status == "ok";
                });
        },
    };
  });
