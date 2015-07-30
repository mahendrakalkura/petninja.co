(function (window, _, jQuery, angular) {
    var context = jQuery('#facebook-search-engine');
    var hostname = context.attr('data-hostname');
    var plan = context.attr('data-plan');

    var get_template_url = function (name) {
        return 'http://' + hostname + '/templates/views/' + name;
    };

    jQuery.noConflict();

    jQuery(function (){
        context.tooltip({
            'selector': '[data-toggle="tooltip"]'
        });
    });

    var application = angular.module('application', [
        'ngRoute', 'restangular'
    ]);

    application.config(function (
        $httpProvider,
        $interpolateProvider,
        $routeProvider,
        $sceDelegateProvider,
        RestangularProvider
    ) {
        $httpProvider.defaults.headers.common[
            'User-Id'
        ] = context.attr('data-user-id');
        $httpProvider.defaults.headers.common[
            'User-Signature'
        ] = context.attr('data-user-signature');
        $httpProvider.interceptors.push('interceptor');
        $interpolateProvider.startSymbol('[!').endSymbol('!]');
        $sceDelegateProvider.resourceUrlWhitelist([
            'self',
            'http://' + hostname + '/**'
        ]);
        $routeProvider.when('/searches/overview', {
            'controller': 'searches_overview',
            'templateUrl': 'http://' + hostname + '/searches/overview'
        }).when('/watchlists/overview', {
            'controller': 'watchlists_overview',
            'templateUrl': 'http://' + hostname + '/watchlists/overview'
        }).otherwise({
            'redirectTo': '/searches/overview'
        });
        RestangularProvider.addRequestInterceptor(
            function (element, operation) {
                if (operation == 'remove') {
                    return undefined;
                }
                return element;
            }
        );
        RestangularProvider.addResponseInterceptor(
            function (response, operation, element, url) {
                if (operation == 'post') {
                    return [response.result, response.status];
                }
                if (operation == 'put') {
                    return [response.result, response.status];
                }
                if (operation == 'remove') {
                    return [response.result, response.status];
                }
                if (element == 'profiles') {
                    if (operation == 'get') {
                        return [response.result, response.status];
                    }
                    return [response.profiles, response.pager];
                }
                return response.output;
            }
        );
        RestangularProvider.setBaseUrl('http://' + hostname + '/restangular');
    });

    application.controller('modal', [
        '$compile',
        '$http',
        '$rootScope',
        '$scope',
        function ($compile, $http, $rootScope, $scope) {
            $scope.element = null;

            $scope.close = function () {
                $scope.element.remove();
                $scope.$emit('modal');
            };

            $http.get(get_template_url('modal.html')).then(
                function (response) {
                    $scope.element = angular.element(
                        $compile(response.data)($scope)
                    );
                    context.append($scope.element);
                    $scope.element.modal({});
                }
            );
        }
    ]);

    application.controller('searches_add', [
        '$compile',
        '$http',
        '$rootScope',
        '$scope',
        'Restangular',
        'modal',
        function ($compile, $http, $rootScope, $scope, Restangular, modal) {
            if (['Pro'].indexOf(plan) == -1) {
                return;
            }

            $scope.element = null;

            $scope.close = function () {
                $scope.element.remove();
            };

            $scope.submit = function () {
                var title = 'Add - ' + $scope.search.name;
                Restangular.all('searches').post($scope.search).then(
                    function (response) {
                        $scope.element.remove();
                        if (response[1]) {
                            $rootScope.$broadcast(
                                'searches_add', $scope.search.name
                            );
                        }
                        modal.open(response[0], response[1], title);
                    },
                    function () {
                        $scope.alert = true;
                    }
                );
            };

            $http.get(get_template_url('searches_add.html')).then(
                function (response) {
                    $scope.element = angular.element(
                        $compile(response.data)($scope)
                    );
                    context.append($scope.element);
                    $scope.element.modal({});
                }
            );
        }
    ]);

    application.controller('searches_overview', [
        '$controller',
        '$http',
        '$q',
        '$rootScope',
        '$routeParams',
        '$scope',
        'Restangular',
        'modal',
        function (
            $controller,
            $http,
            $q,
            $rootScope,
            $routeParams,
            $scope,
            Restangular,
            modal
        ) {
            var profiles_get = function () {
                if (['Personal', 'Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.profile = null;
                return Restangular.one(
                    'profiles', $scope.search.contents.filter.profile_id
                ).get().then(
                    function (response) {
                        $scope.profile = response[0];
                    },
                    function () {
                        $scope.profile = null;
                    }
                );
            };

            var searches_get_list = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.searches = [];
                return Restangular.all('searches').getList().then(
                    function (response) {
                        $scope.searches = response;
                    },
                    function () {
                        $scope.searches = [];
                    }
                );
            };

            var watchlists_get_list = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.watchlists = [];
                return Restangular.all('watchlists').getList().then(
                    function (response) {
                        $scope.watchlists = response;
                    },
                    function () {
                        $scope.watchlists = [];
                    }
                );
            };

            var get_pager = function () {
                return {
                    'count': 0,
                    'first': 0,
                    'last': 0,
                    'next': 0,
                    'pages_1': [],
                    'pages_2': 0,
                    'previous': 0,
                };
            };

            var get_search = function (id) {
                if (id > 0) {
                    return _.find($scope.searches, function (search) {
                        return search.id == id;
                    });
                }
                return {
                    'id': 0,
                    'contents': {
                        'filter': {
                            'category': '',
                            'discussions_maximum': '100.00',
                            'discussions_minimum': '0.00',
                            'profile_id': '',
                            'likes_maximum': '1000000000',
                            'likes_minimum': '0',
                            'location': '',
                            'name': ''
                        },
                        'order_by': {
                            'column': 'name',
                            'direction': 'asc'
                        }
                    },
                    'name': ''
                };
            };

            var get_watchlist = function (profile) {
                return _.find($scope.watchlists, function (watchlist) {
                    return watchlist.profile.id == profile.id;
                });
            };

            $scope.exporting = false;
            $scope.searching = false;

            $scope.searches = [];
            $scope.watchlists = [];

            $scope.limit = 25;
            $scope.page = 1;
            $scope.pager = get_pager();
            $scope.search = get_search(0);

            $scope.profiles = [];
            $scope.profile = null;

            $scope.datasets_category = {
                'displayKey': 'value',
                'source': function (query, cb) {
                    $http.get('http://' + hostname + '/typeahead', {
                        'params': {
                            'attribute': 'category',
                            'query': query
                        }
                    }).then(
                        function (response) {
                            cb(response.data.options)
                        },
                        function () {
                        }
                    );
                }
            };
            $scope.datasets_location = {
                'displayKey': 'value',
                'source': function (query, cb) {
                    $http.get('http://' + hostname + '/typeahead', {
                        'params': {
                            'attribute': 'location',
                            'query': query
                        }
                    }).then(
                        function (response) {
                            cb(response.data.options)
                        },
                        function () {
                        }
                    );
                }
            };
            $scope.options_category = {
                'highlight': true
            };
            $scope.options_location = {
                'highlight': true
            };

            $scope.add_to_watchlist = function (profile) {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                profile.spinner = true;
                Restangular.all('watchlists').post({
                    'profile_id': profile.id
                }).then(
                    function () {
                        profile.spinner = false;
                        watchlists_get_list();
                    },
                    function () {
                        profile.spinner = false;
                        watchlists_get_list();
                    }
                );
            };

            $scope.delete = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                var scope = $rootScope.$new();
                scope.search = $scope.search;
                var controller = $controller('searches_delete', {
                    '$scope': scope
                });
                var reset = $scope.$on('searches_delete', function () {
                    delete controller;
                    scope.$destroy();
                    reset();
                    searches_get_list();
                    $scope.search = get_search(0);
                    $scope.profiles_get_list();
                });
            };

            $scope.export = function (profile) {
                $scope.exporting = true;
                $http.get('http://' + hostname + '/searches/export', {
                    'params': {
                        'filter': $scope.search.contents.filter,
                        'limit': $scope.limit,
                        'order_by': $scope.search.contents.order_by,
                        'page': $scope.page,
                    }
                }).then(
                    function (response) {
                        $scope.exporting = false;
                        var anchor = document.createElement('a');
                        anchor.textContent = 'Export';
                        anchor.download = 'export.csv';
                        anchor.href = 'data:text/csv;charset=utf-8,' + escape(
                            response.data
                        );
                        anchor.click();
                    },
                    function () {
                        $scope.exporting = false;
                        modal.open(
                            'An unknown error has occurred. Please try again.',
                            false,
                            title
                        );
                    }
                );
            };

            $scope.find_similar = function (profile) {
                if (['Personal', 'Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.search = get_search(0);
                $scope.search.contents.filter.profile_id = profile.id;
                $scope.profiles_get_list();
            };

            $scope.profiles_get_list = function () {
                $scope.searching = true;
                $scope.profiles = [];
                $scope.pager = get_pager();
                Restangular.all('profiles').getList({
                    'filter': $scope.search.contents.filter,
                    'limit': $scope.limit,
                    'order_by': $scope.search.contents.order_by,
                    'page': $scope.page
                }).then(
                    function (response) {
                        $scope.searching = false;
                        $scope.profiles = response[0];
                        $scope.pager = response[1];
                    }, function () {
                        $scope.searching = false;
                        $scope.profiles = [];
                        $scope.pager = get_pager();
                    }
                );
            };

            $scope.new = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.search = get_search(0);
                $scope.profiles_get_list();
            };

            $scope.old = function (search) {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                $scope.search = search;
                $scope.profiles_get_list();
            };

            $scope.remove_from_watchlist = function (profile) {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                profile.spinner = true;
                Restangular.all(
                    'watchlists/' + get_watchlist(profile).id
                ).remove().then(
                    function () {
                        profile.spinner = false;
                        watchlists_get_list();
                    },
                    function () {
                        profile.spinner = false;
                        watchlists_get_list();
                    }
                );
            };

            $scope.save = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                var scope = $rootScope.$new();
                scope.search = $scope.search;
                var controller = $controller('searches_add', {
                    '$scope': scope
                });
                var reset = $scope.$on(
                    'searches_add',
                    function (event, name) {
                        delete controller;
                        scope.$destroy();
                        reset();
                        $q.all([searches_get_list()]).then(
                            function () {
                                $scope.search = _.find(
                                    $scope.searches,
                                    function (search) {
                                        return search.name == name;
                                    }
                                );
                            },
                            function () {
                                $scope.search = get_search(0);
                            }
                        );
                    }
                );
            };

            $scope.update = function () {
                if (['Pro'].indexOf(plan) == -1) {
                    return;
                }

                var title = 'Update - ' + $scope.search.name;
                $scope.search.put().then(
                    function (response) {
                        searches_get_list();
                        modal.open(response[0], response[1], title);
                    },
                    function () {
                        searches_get_list();
                        modal.open(
                            'An unknown error has occurred. Please try again.',
                            false,
                            title
                        );
                    }
                );
            };

            $scope.get_number = function (index) {
                return (($scope.page - 1) * $scope.limit) + index + 1;
            };

            $scope.set_order_by_column = function (column) {
                $scope.search.contents.order_by.column = column;
                $scope.page = 1;
                $scope.profiles_get_list();
            };

            $scope.set_order_by_direction = function (direction) {
                $scope.search.contents.order_by.direction = direction;
                $scope.page = 1;
                $scope.profiles_get_list();
            };

            $scope.set_page = function (page) {
                if (['Personal', 'Pro'].indexOf(plan) == -1) {
                    page = 1;
                }

                $scope.page = page;
                $scope.profiles_get_list();
            };

            $scope.is_watched = function (profile) {
                if (['Pro'].indexOf(plan) == -1) {
                    return false;
                }

                if (get_watchlist(profile)) {
                    return true;
                }
                return false;
            };

            $scope.$watch('search', function(new_value, old_value) {
                if (new_value.contents.filter.profile_id) {
                    profiles_get();
                    return;
                }
                $scope.profile = null;
            }, true);

            $q.all([searches_get_list(), watchlists_get_list()]).then(
                function () {
                    $scope.page = typeof(
                        $routeParams.page
                    ) != 'undefined'? $routeParams.page: 1;
                    $scope.search = get_search(typeof(
                        $routeParams.id
                    ) != 'undefined'? $routeParams.id: 0);
                    $scope.profiles_get_list();
                },
                function () {
                    window.location.reload(true);
                }
            )
        }
    ]);

    application.controller('searches_delete', [
        '$compile',
        '$http',
        '$rootScope',
        '$scope',
        'Restangular',
        'modal',
        function ($compile, $http, $rootScope, $scope, Restangular, modal) {
            if (['Pro'].indexOf(plan) == -1) {
                return;
            }

            $scope.alert = false;
            $scope.element = null;

            $scope.no = function () {
                $scope.element.remove();
            };

            $scope.yes = function () {
                var title = 'Delete - ' + $scope.search.name;
                Restangular.all(
                    'searches/' + $scope.search.id
                ).remove().then(
                    function (response) {
                        $scope.element.remove();
                        if (response[1]) {
                            $rootScope.$broadcast('searches_delete');
                        }
                        modal.open(response[0], response[1], title);
                    },
                    function () {
                        $scope.alert = true;
                    }
                );
            };

            $http.get(get_template_url('searches_delete.html')).then(
                function (response) {
                    $scope.element = angular.element(
                        $compile(response.data)($scope)
                    );
                    context.append($scope.element);
                    $scope.element.modal({});
                }
            );
        }
    ]);

    application.controller('watchlists_delete', [
        '$compile',
        '$http',
        '$rootScope',
        '$scope',
        'Restangular',
        'modal',
        function ($compile, $http, $rootScope, $scope, Restangular, modal) {
            if (['Pro'].indexOf(plan) == -1) {
                return;
            }

            $scope.alert = false;
            $scope.element = null;

            $scope.no = function () {
                $scope.element.remove();
            };

            $scope.yes = function () {
                var title = 'Delete - ' + $scope.watchlist.profile.name;
                Restangular.all(
                    'watchlists/' + $scope.watchlist.id
                ).remove().then(
                    function (response) {
                        $scope.element.remove();
                        if (response[1]) {
                            $rootScope.$broadcast('watchlists_delete');
                        }
                        modal.open(response[0], response[1], title);
                    },
                    function () {
                        $scope.alert = true;
                    }
                );
            };

            $http.get(get_template_url('watchlists_delete.html')).then(
                function (response) {
                    $scope.element = angular.element(
                        $compile(response.data)($scope)
                    );
                    context.append($scope.element);
                    $scope.element.modal({});
                }
            );
        }
    ]);

    application.controller('watchlists_edit', [
        '$compile',
        '$http',
        '$rootScope',
        '$scope',
        'Restangular',
        'modal',
        function ($compile, $http, $rootScope, $scope, Restangular, modal) {
            if (['Pro'].indexOf(plan) == -1) {
                return;
            }

            $scope.alert = false;
            $scope.element = null;
            $scope.operands = [
                ['+', 'increases by'],
                ['-', 'decreases by']
            ];

            $scope.close = function () {
                $scope.element.remove();
            };

            $scope.submit = function () {
                var title = 'Edit - ' + $scope.watchlist.profile.name;
                $scope.watchlist.put().then(
                    function (response) {
                        $scope.element.remove();
                        if (response[1]) {
                            $rootScope.$broadcast('watchlists_edit');
                        }
                        modal.open(response[0], response[1], title);
                    },
                    function () {
                        $scope.alert = true;
                    }
                );
            };

            $http.get(get_template_url('watchlists_edit.html')).then(
                function (response) {
                    $scope.element = angular.element(
                        $compile(response.data)($scope)
                    );
                    context.append($scope.element);
                    $scope.element.modal({});
                }
            );
        }
    ]);

    application.controller('watchlists_overview', [
        '$controller',
        '$rootScope',
        '$scope',
        'Restangular',
        'modal',
        function ($controller, $rootScope, $scope, Restangular, modal) {
            if (['Pro'].indexOf(plan) == -1) {
                return;
            }

            $scope.spinner = false;
            $scope.watchlists = [];
            $scope.watchlist = {};

            var watchlists_get_list = function () {
                $scope.spinner = true;
                $scope.watchlists = [];
                Restangular.all('watchlists').getList().then(
                    function (response) {
                        $scope.spinner = false;
                        $scope.watchlists = response;
                    },
                    function () {
                        $scope.spinner = false;
                        $scope.watchlists = [];
                    }
                );
            };

            $scope.delete = function (watchlist) {
                var scope = $rootScope.$new();
                scope.watchlist = watchlist;
                var controller = $controller('watchlists_delete', {
                    '$scope': scope
                });
                var reset = $scope.$on('watchlists_delete', function () {
                    delete controller;
                    scope.$destroy();
                    reset();
                    watchlists_get_list();
                });
            };

            $scope.edit = function (watchlist) {
                var scope = $rootScope.$new();
                scope.watchlist = watchlist;
                var controller = $controller('watchlists_edit', {
                    '$scope': scope
                });
                var reset = $scope.$on('watchlists_edit', function () {
                    delete controller;
                    scope.$destroy();
                    reset();
                    watchlists_get_list();
                });
            };

            watchlists_get_list();
        }
    ]);

    application.directive('typeahead', function () {
        return {
            'link': function (scope, element) {
                function refresh (object, suggestion, dataset) {
                    var value = element.val();
                    scope.$apply(function () {
                        scope.value = suggestion;
                    });
                    element.val(value);
                }

                element.typeahead(scope.options, scope.datasets);

                element.bind(
                    'typeahead:selected',
                    function (object, suggestion, dataset) {
                        refresh(object, suggestion, dataset);
                        scope.$emit('typeahead:selected');
                    }
                );

                element.bind(
                    'typeahead:autocompleted',
                    function (object, suggestion, dataset) {
                        refresh(object, suggestion, dataset);
                        scope.$emit('typeahead:autocompleted');
                    }
                );

                element.bind('input', function () {
                    scope.$apply(function () {
                        var value = element.val();
                        scope.value = value;
                    });
                });
            },
            'restrict': 'A',
            'scope': {
                'datasets': '=',
                'options': '=',
                'value': '=ngModel'
            }
        };
    });

    application.factory('modal', [
        '$controller',
        '$rootScope',
        function ($controller, $rootScope) {
            return {
                'open': function (body, status, title) {
                    var scope = $rootScope.$new();
                    scope.body = body;
                    scope.status = status;
                    scope.title = title;
                    var controller = $controller('modal', {
                        '$scope': scope
                    });
                    var reset = $rootScope.$on(
                        'modal',
                        function () {
                            delete controller;
                            scope.$destroy();
                            reset();
                        }
                    );
                }
            };
        }
    ]);

    application.filter('truncate', function () {
        return function (url) {
            return url.replace(
                /https:\/\/www./, ''
            ).replace(
                /http:\/\/www./, ''
            ).replace(
                /http:\/\//, ''
            ).replace(
                /http:\/\//, ''
            );
        };
    });

    application.service('interceptor', function ($q) {
        return {
            'request': function (config) {
                context.find('.spinner').show();
                return config || $q.when(config);

            },
            'requestError': function (config) {
                context.find('.spinner').hide();
                return $q.reject(config);
            },
            'response': function (response) {
                context.find('.spinner').hide();
                return response || $q.when(response);
            },
            'responseError': function (response) {
                context.find('.spinner').hide();
                return $q.reject(response);
            }
        };
    });

    application.run();
})(window, _, jQuery, angular);
