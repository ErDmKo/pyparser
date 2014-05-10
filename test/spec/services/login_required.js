'use strict';

describe('Service: loginRequired', function () {

  // load the service's module
  beforeEach(module('webclientApp'));

  // instantiate service
  var loginRequired;
  beforeEach(inject(function (_loginRequired_) {
    loginRequired = _loginRequired_;
  }));

  it('should do something', function () {
    expect(!!loginRequired).toBe(true);
  });

});
