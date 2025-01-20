import asyncio
from twikit import Client
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv('username')
EMAIL = os.getenv('email')
PASSWORD = os.getenv('password')
LIST_ID = os.getenv('list_id')

client = Client("pt-BR")

def print_formated_tweet(tweet):
    print(
        f'id: {tweet.id}',
        f'text {tweet.text}',
        f'favorite count: {tweet.favorite_count}',
        f'media: {tweet.media}',
        sep='\n'
    ) 

async def get_tweet_by_id(id):
    tweet = await client.get_tweet_by_id(id)

    print_formated_tweet(tweet)

async def main():
    # await client.login(
    #     auth_info_1=USERNAME,
    #     auth_info_2=EMAIL,
    #     password=PASSWORD
    # )
    # client.save_cookies("cookies.json")
    client.load_cookies('cookies.json')

    tweets = await client.get_list_tweets(LIST_ID)
    for tweet in tweets:
        print_formated_tweet(tweet)
    
asyncio.run(main())