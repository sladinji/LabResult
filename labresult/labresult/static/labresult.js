var app = angular.module('LabApp', 
                ['ui.bootstrap', 'ui.bootstrap.tpls','ui.router', 'ngTouch', 'angular-carousel']
                )
app.config(function($stateProvider, $urlRouterProvider){
    $urlRouterProvider.otherwise("/");
    $stateProvider
        .state('labos',{
            url:'/labos',
            templateUrl: '../static/labos.html',
            controller: 'LaboCtrl',
            data: {}
        })
        .state('images',{
            url:'/images',
            templateUrl: '../static/images.html',
            controller: 'CarouselDemoCtrl',
            data: {}
        });
});

app.factory('windowAlert', [
        '$window',
        function($window) {
            return $window.alert;
        }
    ]);


app.controller('LaboCtrl', [
        '$scope',
        '$http',
        'windowAlert',
        function($scope, $http, windowAlert) {
            $scope.state = {};
            $scope.state.labos = []
            $scope.retrieveLabos = function() {
                $http
                    .get('/api/v1.0/labos')
                    .success(function(data, status, headers, config) {
                        if (data.success) {
                            $scope.state.labos = data.labos;
                        } else {
                            windowAlert('Impossible de récupérer la liste de laboratoires');
                        }
                    })
                    .error(function(data, status, headers, config) {
                        windowAlert("Impossible d'accéder à la liste des laboratoires");
                    });
            };
            var init = function () {
                $scope.retrieveLabos();
                       };
            init();
        }

    ]);

app.controller('CarouselDemoCtrl',[
    '$scope',
    function($scope) {
      $scope.myInterval = 5000;
      var slides = $scope.slides = [];
      $scope.addSlide = function() {
        var newWidth = 600 + slides.length;
        slides.push({
          image: '/api/v1.0/file?id=53c904af7edeff380cb29fb3&format=svg',
          text: ['More','Extra','Lots of','Surplus'][slides.length % 4] + ' ' +
            ['Cats', 'Kittys', 'Felines', 'Cutes'][slides.length % 4]
        });
      };
      for (var i=0; i<4; i++) {
        $scope.addSlide();
      }
    }
]);

app.controller('ImagesModalCtrl',[
    '$scope', '$modal', '$log', '$http', 'windowAlert',
    function($scope, $modal, $log, $http, windowAlert) {
        $scope.show_modal_images = function(doc_id) {
            $http
                .get('/api/v1.0/documents/?ids=' + doc_id)
                .success(function(data, status, headers, config) {
                    $scope.data = data.items[0];
                    var modalInstance = $modal.open({
                        templateUrl: '../static/modal_images.html',
                        controller: ModalImgInstanceCtrl,
                        windowClass: 'modal-fullscreen',
                        resolve :{
                            doc: function(){
                                return $scope.data
                            }
                         }
                    });
                })
                .error(function(data, status, headers, config) {
                    windowAlert("Impossible d'afficher le document (erreur lors de sa conversion).");
                    location.reload();
                });
        };
    }
]);

var ModalImgInstanceCtrl = function($scope, $modalInstance, doc){
          $scope.doc = doc
          $scope.close = function () {
            $modalInstance.close();
          };
      }

app.controller('WarningModalCtrl',[
    '$scope', '$modal', '$http','windowAlert',
    function($scope, $modal, $http, windowAlert) {
        $scope.show_modal_errors = function (doc_id) {
            $http
                .get('/api/v1.0/documents/?ids=' + doc_id)
                .success(function(data, status, headers, config) {
                    $scope.doc = data['items'][0];
                    var modalInstance = $modal.open({
                        templateUrl: '../static/modal_warnings.html',
                        controller: ModalWarnInstanceCtrl,
                        size : "lg",
                        resolve :{
                            doc: function(){
                                return $scope.doc
                            }
                         }
                    });

                })
                .error(function(data, status, headers, config) {
                    windowAlert("Impossible de récupérer les informations sur le document.");
                });
        };
    }
]);

var ModalWarnInstanceCtrl = function($scope, $sce, $modalInstance,$injector, doc){
          $scope.doc = doc;
          $scope.doc.traceback = $sce.trustAsHtml($scope.doc.traceback);
          $scope.close = function () {
            $modalInstance.close();
          };
      }

