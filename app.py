import asyncio
from twikit import Client
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv('username')
EMAIL = os.getenv('email')
PASSWORD = os.getenv('password')

client = Client("pt-BR")

async def get_tweet_by_id(id):
    tweet = await client.get_tweet_by_id(id)

    # Access tweet attributes
    print(
        f'id: {tweet.id}',
        f'text {tweet.text}',
        f'favorite count: {tweet.favorite_count}',
        f'media: {tweet.media}',
        sep='\n'
    )

async def main():
    # await client.login(
    #     auth_info_1=USERNAME,
    #     auth_info_2=EMAIL,
    #     password=PASSWORD
    # )
    # client.save_cookies("cookies.json")
    client.load_cookies('cookies.json')

    tweets = await client.get_list_tweets(os.getenv('list_id'))
    for tweet in tweets:
        print(tweet.id)
        print(
        f'id: {tweet.id}',
        f'text {tweet.text}',
        f'favorite count: {tweet.favorite_count}',
        f'media: {tweet.media}',
        sep='\n'
    )
    
asyncio.run(main())