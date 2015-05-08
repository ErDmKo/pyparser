angular.module('pyparserApp')
    .factory('ranking', function ($resource) {
    var rankings = $resource('/server/');
    return rankings;
    });
