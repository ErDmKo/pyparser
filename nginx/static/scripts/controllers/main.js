'use strict';


angular.module('pyparserApp')
    .controller('MainControler', function (ranking, $scope) {
    ranking.get().$promise.then(function(images_list){
        $scope.images = images_list.info_list.images;
        });
    });
