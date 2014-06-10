'use strict';

describe('Service: ranking', function () {

  // load the service's module
  beforeEach(module('webclientApp'));

  // instantiate service
  var ranking;
  beforeEach(inject(function (_ranking_) {
    ranking = _ranking_;
  }));

  it('should do something', function () {
    expect(!!ranking).toBe(true);
  });

});
