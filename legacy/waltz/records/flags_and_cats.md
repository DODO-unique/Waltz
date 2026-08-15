Password:
    - FETCH_USER_CREDS_EMAIL
    - FETCH_USER_CREDS_UNAME


Note:
There would be one BOOLEAN RESULTS category, I tihnk.
In dev, I am coming across many results that basically just return bool.
Though it is not always for results- it can be a status of request as well. 
But status of request need to be resolved internally by rejecting the ticket itself.
You have to sort and plan the predicate results versus status pipes and handle the latter at the bus-level.

SO I have categorized the return types in four types:
| Category                  | Purpose                                                                  | Examples                                                   |
| ------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------- |
| **Predicate**             | Answers a yes/no question.                                               | `isUsernameAvailable()`, `hasPermission()`, `isVerified()` |
| **Result**                | Returns a payload representing the outcome.                              | `LoginResult`, `UserProfile`, `SessionInfo`                |
| **Status**                | Describes the execution state of the request. Internal to the framework. | `SUCCESS`, `REJECTED`, `TIMEOUT`, `HANDLER_NOT_FOUND`      |
| **Scalar**                | Returns a single piece of data rather than a structured result.          | `userId`, `token`, `email`, `count`, `datetime`            |

