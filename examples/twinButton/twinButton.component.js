angular.
  module('twinButton').
  component('twinbutton', {
    templateUrl: 'partials/twinButton.html',
    controller: function ($scope) {
        $scope.counter = {
            value: 1,
            max: 10,
            min: 1,
            interval: 1,
            do: function(n) {
                this.value += n
                if (this.value > this.max) {
                    this.value = this.max;
                } else if (this.value < this.min) {
                    this.value = this.min
                }
            }
        }
    }
  });