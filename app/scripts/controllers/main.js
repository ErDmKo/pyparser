'use strict';

angular.module('pyparserApp')
    .controller('MainCtrl', function ($scope) {
        $scope.login = function() {
            var form =$scope.login_form;
            if(form.$invalid) {
                form.$setDirty();
            } else {
                ;
            }

        }
    });
