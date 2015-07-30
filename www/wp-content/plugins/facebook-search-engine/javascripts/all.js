var application = angular.module('application', []);

application.config(function ($httpProvider) {
    $httpProvider.defaults.headers.post[
        'Content-Type'
    ] = 'application/x-www-form-urlencoded';
});

application.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[!').endSymbol('!]');
});

application.controller(
    'dashboard',
    [
        '$attrs',
        '$http',
        '$scope',
        function ($attrs, $http, $scope) {
            $scope.data = {};
            $scope.spinner = false;

            $scope.refresh = function() {
                $scope.data = {};
                $scope.spinner = true;
                $http({
                    'cache': false,
                    'params': {
                        'action': 'dashboard',
                        'security': $attrs.security
                    },
                    'method': 'GET',
                    'url': ajaxurl
                }).then(
                    function (response) {
                        $scope.data = response.data;
                        $scope.spinner = false;
                    },
                    function () {
                        $scope.spinner = false;
                        $scope.refresh();
                    }
                );
            };

            $scope.refresh();
        }
    ]
);

application.controller(
    'reports',
    [
        '$attrs',
        '$http',
        '$scope',
        function ($attrs, $http, $scope) {
            $scope.data = {};
            $scope.spinner = false;

            $scope.refresh = function() {
                $scope.data = {};
                $scope.spinner = true;
                $http({
                    'cache': false,
                    'method': 'GET',
                    'params': {
                        'action': 'reports',
                        'name': $attrs.name,
                        'security': $attrs.security
                    },
                    'url': ajaxurl
                }).then(
                    function (response) {
                        $scope.data = response.data;
                        $scope.spinner = false;
                    },
                    function () {
                        $scope.spinner = false;
                        $scope.refresh();
                    }
                );
            };

            $scope.refresh();
        }
    ]
);

application.controller(
    'status',
    [
        '$attrs',
        '$http',
        '$scope',
        function ($attrs, $http, $scope) {
            $scope.data = {};
            $scope.spinner = false;

            $scope.refresh = function() {
                $scope.data = {};
                $scope.spinner = true;
                $http({
                    'cache': false,
                    'params': {
                        'action': 'status',
                        'security': $attrs.security
                    },
                    'method': 'GET',
                    'url': ajaxurl
                }).then(
                    function (response) {
                        $scope.data = response.data;
                        $scope.spinner = false;
                    },
                    function () {
                        $scope.spinner = false;
                        $scope.refresh();
                    }
                );
            };

            $scope.refresh();
        }
    ]
);
