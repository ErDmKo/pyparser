'use strict';

angular.module('pyparserApp')
    .controller('MainControler', function (ranking, $scope) {
    ranking.get().$promise.then(function(images_list){
        console.log(images_list);
        });
    });
