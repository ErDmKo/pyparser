'use strict';

angular.module('pyparserApp')
    .controller('LoginController', function ($scope, $rootScope, AUTH_EVENTS, AuthService) {
        $scope.login = function() {
            var form =$scope.login_form;
            $scope.error = {};
            if(form.$invalid) {
                form.$setDirty();
            } else {
                AuthService.login($scope.user).then(function(info){
                    $scope.error = {};
                    console.log(info);
                    $rootScope.$broadcast(AUTH_EVENTS.loginSuccess);
                },
                function(info){
                    for ( var field  in info.data) if (info.data.hasOwnProperty(field))
                        {
                        $scope.error[field] = info.data[field];
                        }
                    $rootScope.$broadcast(AUTH_EVENTS.loginFailed);
                });
            }

        }
    });
