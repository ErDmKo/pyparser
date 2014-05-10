'use strict';

angular.module('pyparserApp')
  .factory('AuthService', function ($http, Session) {
    return {
      login: function (form) {
        return $http
            .post('server/auth/login', form)
            .then(function (res) {
                Session.create(res.id, res.userid, res.role);
            });
        },
    };
  });
