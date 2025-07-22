import click
import json
from datetime import datetime
from strava_oauth import StravaOAuth

# main
@click.command()
@click.option("--client-id", help="Strava client id")
@click.option("--client-secret", help="Strava client secret")
@click.option("--access-token", help="Strava access token")
@click.option("--refresh-token", help="Strava refresh token")
@click.option("--code", help="Strava authorization code")
@click.option("--per-page", type=int, default=30, help="Number of items per page (default: 30)")
def main(client_id, client_secret, access_token, refresh_token, code, per_page):
    try:
        oauth = StravaOAuth(
            client_id=client_id,
            client_secret=client_secret
        )
        if code:
            # exchange the authorization code for tokens
            token_data = oauth.exchange_code_for_token(code)
            print(json.dumps(token_data))
            payload = oauth.make_authenticated_request(token_data['access_token'], 'GET', 'https://www.strava.com/api/v3/athlete')
            print(json.dumps(payload))
        elif refresh_token:
            # refresh the access token
            token_data = oauth.refresh_access_token(refresh_token)
            token_data['expires_at_iso'] = datetime.fromtimestamp(token_data.get('expires_at')).isoformat()
            print(json.dumps(token_data))
        elif access_token:
            # make a request with the provided access token
            endpoint = 'https://www.strava.com/api/v3/athlete/activities'
            activities = oauth.fetch_all_pages(access_token, endpoint, per_page)
            print(json.dumps(activities))
        else:
            # print the authorization URL for the user to visit
            auth_url = oauth.get_authorization_url()
            print(f"Please visit this URL to authorize: {auth_url}\n")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
