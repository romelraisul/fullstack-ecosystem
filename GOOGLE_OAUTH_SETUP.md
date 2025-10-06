# How to get Google OAuth Credentials

To use Google as your OAuth provider, you need to create a project in the Google Cloud Console and generate OAuth 2.0 credentials.

## 1. Create a Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project drop-down and select **New Project**.
3. Give your project a name and click **Create**.

## 2. Enable the Google People API

1. In the Cloud Console, go to **APIs & Services > Library**.
2. Search for "Google People API" and enable it.

## 3. Configure the OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**.
2. Choose **External** and click **Create**.
3. Fill in the required fields:
    * **App name:** A descriptive name for your application.
    * **User support email:** Your email address.
    * **Developer contact information:** Your email address.
4. Click **Save and Continue**.
5. On the **Scopes** page, click **Add or Remove Scopes**.
6. Select the following scopes:
    * `.../auth/userinfo.email`
    * `.../auth/userinfo.profile`
    * `openid`
7. Click **Update**, then **Save and Continue**.
8. On the **Test users** page, add your Google account to the list of test users.
9. Click **Save and Continue**, then **Back to Dashboard**.

## 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select **Web application** as the application type.
4. Give your client a name.
5. Under **Authorized redirect URIs**, add the following URI:
    * `https://localhost:8444/oauth2/callback`
6. Click **Create**.
7. A dialog will appear with your **Client ID** and **Client Secret**. Copy these values.

## 5. Configure the `.env` File

1. Copy the `.env.sample` file to a new file named `.env`.
2. Paste your **Client ID** and **Client Secret** into the `.env` file:

    ```
    OAUTH2_PROXY_CLIENT_ID=your-client-id
    OAUTH2_PROXY_CLIENT_SECRET=your-client-secret
    ```

3. Generate a random cookie secret and add it to the `.env` file. You can use the following command:

    ```bash
    python -c 'import os, base64; print(base64.b64encode(os.urandom(32)).decode("utf-8"))'
    ```

    Your final `.env` file should look something like this:

    ```
    OAUTH2_PROXY_COOKIE_SECRET=your-random-cookie-secret
    OAUTH2_PROXY_CLIENT_ID=your-client-id
    OAUTH2_PROXY_CLIENT_SECRET=your-client-secret
    ```

You are now ready to start the services with Google OAuth enabled.
