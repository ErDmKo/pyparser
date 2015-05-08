'use strict';

angular.module('pyparserApp')
    .controller('LoginController', function ($location, $scope, $rootScope, AUTH_EVENTS, AuthService) {
        $scope.login = function() {
            var form =$scope.login_form;
            $scope.error = {};
            if(form.$invalid) {
                form.$setDirty();
            } else {
                AuthService.login($scope.user).then(function(info){
                    $scope.error = {};
                    $rootScope.$broadcast(AUTH_EVENTS.loginSuccess);
                    $location.path('/')
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
