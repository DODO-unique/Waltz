### Meta Notes: 
1. This is completely about how user interaction works via Waltz API. So this is a record of expected exchanges.
2. Payloads would be JSON-like; a `dict[str, str]`.


## Phase one

**Authentication** passes only identity (email or uname) in the payload and expects a hashed password (in a string and not bytes). 

For FETCH_USER_CREDS_EMAIL and FETCH_USER_CREDS_UNAME
Payload provided :
```
{'identity' : str(payload)}
```

Result expected :
```
{'password' : str(hashed_password_by_bcrypt)}
```

A few things to note here:
1. bcrypt password is something I won't optimize because Waltz creates bcrypt passwords only, sure it locks you, but you are supposed to be locked.
2. I would like to remove the json from the user's end entirely and let them simply pass the raw results. I hesitate now because then I would have to add that to the decorator logic- For that I would categorize all the flags into groups where similar results are expected. These groups would be used to process direct data.

So the new architecture is:

Result expected form the user:
```
(hashed_password_by_bcrypt)
```
It would be categorized into `password` return by checking relevant flags.
Another file would be to keep record of flags and the categories they fall into.

Implementation of the same would come after the entire documentation.


NOTE: Introducing client Pydantic schemas!
    These schemas would be used by devs to easily forge a expected return type for all decorators in: ![client_schemas](../client_schemas.py)