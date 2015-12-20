  /**
    * productOrder Module
    *
    * Description
    */
    var app = angular.module('productOrder', ['ngRoute']);
    app.controller('productOrderStep01Ctrl', ['$http', '$scope', function($http, $scope){
        var pattern = /product\/(\d+)\/order/g;
        var matched = (window.location.href).match(pattern)[0];
        var pid = matched.split('/')[1];
        $http({
            method: 'GET',
            url: '/api/v2.0/product/searchdetail',
            params:{pid: pid},
        }).success(function(resp){
            $scope.productDetail = resp.SearchedProductDetail;
        });
        
        $scope.quantity = 1;
        $scope.maxquantity = 5;
        $scope.$watch('quantity', function(newValue, oldValue){
            if (newValue > $scope.maxquantity){
                $scope.quantity = $scope.maxquantity;
            } else if (newValue < 1){
                $scope.quantity = 1;
            } else if (isNaN(newValue)){
                $scope.quantity = oldValue;
            }
        });
    }]);
    //
    app.directive('quantityClick', ['$rootScope', function($rootScope){
        return {
            restrict: 'A', // E = Element, A = Attribute, C = Class, M = Comment
            link: function($scope, iElm, iAttrs, controller) {
                iElm.on('click', function(){
                    $scope.$apply(function(){
                        $scope.quantity += Number(iAttrs.quantityClick);
                    });
                });
            }
        };
    }]);
    app.config(['$routeProvider',function($routeProvider) {
        $routeProvider.when('/step:number',{
            templateUrl:function($routeParams){
                return '/templates/product_order_step'+ $routeParams.number;
                },
            controller:'productOrderStep01Ctrl',
        }).otherwise({
            templateUrl: '/templates/product_order_step1',
            controller:'productOrderStep01Ctrl',

        });
    }]);