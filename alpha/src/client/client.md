This is v1.0 client backend.

The contract version is different and not related. 

Current client version only adds clients, securities, and contracts. It returns clientID and clientSecret that are used for identification and signing JWT tokens for operations.

Note that this version does not verify a user, simply adds the contract via the API. It might not be exposed in prod or when used against services which are used for internal operations and the client is expected.