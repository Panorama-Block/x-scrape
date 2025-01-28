import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from twikit import Client
from pymongo import MongoClient

load_dotenv()

USERNAME = os.getenv('username')
EMAIL = os.getenv('email')
PASSWORD = os.getenv('password')
LIST_ID = os.getenv('list_id')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['twitter_db']
tweets_collection = db['tweets']

client = Client("pt-BR")

def print_formated_tweet(tweet):
    print(
        f'id: {tweet.id}',
        f'username: {tweet.user.name}',
        f'user image: {tweet.user.profile_image_url}',
        f'text {tweet.text}',
        f'favorite count: {tweet.favorite_count}',
        f'media: {tweet.media}',
        f'created_at: {tweet.created_at}',
        f'created_at_datetime: {tweet.created_at_datetime}',
        sep='\n'
    )

def save_tweet_to_db(tweet):
    tweet_data = {
        'tweet_id': tweet.id,
        'username': tweet.user.name,
        'user_image': tweet.user.profile_image_url,
        'text': tweet.text,
        'favorite_count': tweet.favorite_count,
        'media': tweet.media,
        'created_at': tweet.created_at,
        'created_at_datetime': tweet.created_at_datetime
    }
    
    tweets_collection.update_one(
        {'tweet_id': tweet.id},
        {'$set': tweet_data},
        upsert=True
    )
    print(f'Tweet {tweet.id} saved to database')

async def get_tweet_by_id(id):
    tweet = await client.get_tweet_by_id(id)

    print_formated_tweet(tweet)

async def main():
    try:
        client.load_cookies("cookies.json")
    except:
        print("cookies not found, login first")
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        client.save_cookies("cookies.json")

    while True:
        print("\nFetching tweets...")
        tweets = await client.get_list_tweets(LIST_ID)
        for tweet in tweets:
            print_formated_tweet(tweet)
            save_tweet_to_db(tweet)
        
        print("\nWaiting for 1 hour before next fetch...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram stopped by user")