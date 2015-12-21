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
            $scope.ptype = resp.SearchedProductDetail.product_type;
            // $scope.ptype = 1;
        });
        $http({
            method: 'GET',
            url: '/api/v2.0/product/scene/listall',
            params : {PID: pid}
        }).success(function(resp){
            $scope.scene = resp;
            $scope.sceneParams = {
                PID: pid,
                SceneName: $scope.scene.DefaultScene.scene_name,
                SceneLocation: $scope.scene.DefaultScene.scene_locations,
                SceneTimeperiod: $scope.scene.DefaultScene.scene_timeperiod,
            };
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
        $scope.$watchCollection('sceneParams', function(newP, oldP){
            if (newP){
                  $http({
                    method: 'GET',
                    url: '/api/v2.0/product/scene/listall',
                    params : newP,
                }).success(function(resp){
                    $scope.scene = resp;
                });
            }
        }); 
        // get price range
        // $http({
        //     method: 'GET',
        //     url: '/api/v2.0/product/scene/queryprice',
        //     params: {
        //         PID: pinfo.product_id,
        //     }
        // }).success(function(resp){
        //     $scope.productPrice = resp.ProductPrice;
        // });
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
    app.directive('optionClick', [function(){
        return {
            // restrict: 'A', // E = Element, A = Attribute, C = Class, M = Comment
            link: function($scope, iElm, iAttrs, controller) {
                iElm.on('change', function(){
                    var opt = iAttrs.optionClick;
                    var P = $scope.sceneParams;
                    $scope.$apply(function(){
                        if (opt == 0){
                            $scope.sceneParams.SceneName = iElm.val();
                        }else if (opt ==1){
                            $scope.sceneParams.Scenelocation = iElm.val();
                        }else if (opt ==2){
                            $scope.sceneParams.SceneTimeperiod = iElm.val();
                        }
                    });
                    // console.log($scope.sceneParams);
                });              
            }
        };
    }]);
    app.config(['$routeProvider',function($routeProvider) {
        $routeProvider.when('/step1',{
            templateUrl: '/templates/product_order_step1',
            controller: 'productOrderStep01Ctrl',
        }).when('/step2', {
            templateUrl: '/templates/product_order_step2',
            controller: ['$scope', '$http', function($scope, $http){

            }],
            controllerAS: 'Step2Ctrl',
        }).when('/step3', {
            templateUrl: '/templates/product_order_step3',
            controller: function($scope){
            },
            controllerAS: 'Step3Ctrl',
        }).otherwise({
            redirectTo: '/step1',
        });
    }]);