What is OAuth, really?
Imagine it like this:
In a usual registration, you take the information about a user from the user, store it as user data. 
In OAuth, you take the information about a user from Google. Store this as user data.

Now, when you first get a google request- a "new user" scenario- you get a code. You trade this code for tokens. These tokens come with a "sub" (subject)
**Tokens are the information** you want
**sub is the identity of the token**

So by analogy: 
1. Token is information you store about the user.
2. sub is the password hash that helps identify the token.

The user table then looks like:
| id | provider | password_hash | email                                     |
| -- | -------- | ------------- | ----------------------------------------- |
| 18 | local    | bcrypt...     | [bob@example.com](mailto:bob@example.com) |

And:

| id | provider | provider_subject | email                                     |
| -- | -------- | ---------------- | ----------------------------------------- |
| 17 | google   | 104928374928374  | [alice@gmail.com](mailto:alice@gmail.com) |



How does a OAuth work?

THe usual flow is: 
1. User tries to login with Google. Frontend contacts backend, gets a 'state', redirects to Google, something like:
    ```
    https://accounts.google.com/o/oauth2/v2/auth
        ?client_id=...
        &redirect_uri=...
        &response_type=code
        &scope=openid email profile
        &state=9fd182ab
    ```

2. The redirect_url is your backend's url. Once the user confirms login, Google responds to the redirect_url with the help of the Browser.
   
   This is generally done as a redirect, something like this:
    ```
      │ 302 Redirect
      │ Location:
      │ https://waltz.dev/auth/google/callback?code=abc...
    ```

   That is followed by the browser making a GET request to the backend:
    ```
    GET /auth/google/callback?code=abc...
    ```

3. Once backend gets the response, it compares the 'state' (This is important to prevent CSRF attacks).  
    The code is traded for tokens with google oauth api server to server by our backend.  
    You get what you requested in form of a Access Token, and ID Token. A ID token is a JWT token that we can unpack for information.   
    Tokens come with a provider_subject as well.

    A subject, or "sub" is a unique identity of the tokens. Generally, you use the sub to search for entries, like a ID.  
    Notice we don't need any kind of security problems here like 2FA, or Password hashes- this is because Google itself is responsible for that security. This is the perk of OAuth.

4. Now you have to simply store this and the next time you get the same sub, you would compare. 

    

Now, let's talk about the more interesting thing:

Waltz' OAuth. 

It would be dead simple, it would simply ask:
Name, email, profile picture

Rest is something we will add ourselves, like created_at, updated_at.