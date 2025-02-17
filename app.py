import os
import asyncio
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

from twikit import Client
from pymongo import MongoClient

load_dotenv()

USERNAME = os.getenv('USERNAME')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
LIST_ID = os.getenv('LIST_ID')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
TWEET_ID = os.getenv('TWEET_ID')

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['twitter_db']
tweets_collection = db['tweets']
tweets_zico_collection = db['tweets_zico']
posted_tweets_zico_collection = db['posted_tweets_zico']

client = Client("pt-BR")

def print_formated_tweet(tweet):
    print(
        f'id: {tweet.id}',
        f'username: {tweet.user.name}',
        f'user image: {tweet.user.profile_image_url}',
        f'text: {tweet.text}',
        f'urls: {tweet.urls}',
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
    
def save_posted_tweet_to_db(tweet):
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

    posted_tweets_zico_collection.update_one(
        {'tweet_id': tweet.id},
        {'$set': tweet_data},
        upsert=True
    )
    print(f'Tweet {tweet.id} saved to database')
    
def get_new_tweet():
    tweet_data = tweets_zico_collection.find_one({'posted': False}, sort=[('created_at_datetime', -1)])
    
    if not tweet_data:
        print('No unposted tweets found in tweets_zico_collection')
        return None
        
    for part in tweet_data.get('parts', []):
        existing_posted_tweet = posted_tweets_zico_collection.find_one({'text': part})
        if existing_posted_tweet:
            print(f'Part "{part[:30]}..." already exists in posted_tweets_zico_collection. Skipping tweet...')
            tweets_zico_collection.update_one(
                {'_id': tweet_data['_id']},
                {'$set': {'posted': True}}
            )
            return None
    
    formatted_parts = []
    for i, part in enumerate(tweet_data.get('parts', [])):
        header = "Zico1000x AI here 🤩 this is what leading AI agents said today on X:"
        if i > 0:
            header = "Continuing..."
            
        formatted_part = f"{header}\n\n{part}"
        formatted_parts.append(formatted_part)
    
    return {
        'parts': formatted_parts,
        'tweet_id': tweet_data['_id']
    }

async def get_tweet_by_id(id):
    tweet = await client.get_tweet_by_id(id)

    print_formated_tweet(tweet)
    return tweet

async def post_intro_tweet_job():
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
        
    intro_tweet = "Hello I'm ZICO1000x - PanoramaBlock 1st AI agent following other leading AI agents on X and summarizing content - so you don't have to follow 20+ crazy agents - #JustFollowMe"
        
    new_tweet = await client.create_tweet(intro_tweet)
    save_posted_tweet_to_db(new_tweet)
    print(f'Intro tweet {new_tweet.id} posted')
            
async def post_summary_tweet_job():
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

    try:
        tweet_data = get_new_tweet()
        
    
        if tweet_data:
            for part in tweet_data['parts']:
                new_tweet = await client.create_tweet(part)
                save_posted_tweet_to_db(new_tweet)
                print('Tweet part posted successfully')
                await asyncio.sleep(3)
            
            tweets_zico_collection.update_one(
                {'_id': tweet_data['tweet_id']},
                {'$set': {'posted': True}}
            )
            
    except Exception as e:
        print(f"Error in tweet job: {e}")

async def hourly_job():
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
            
    try:
        list_tweets = await client.get_list_tweets(os.getenv('LIST_ID'))
            
        for tweet in list_tweets:
            save_tweet_to_db(tweet)
                
    except Exception as e:
        print(f"Error in hourly job: {e}")
        await asyncio.sleep(5)

async def main():
    load_dotenv()
    
    schedule.every().day.at("12:00").do(lambda: asyncio.run(post_intro_tweet_job()))
    schedule.every().day.at("15:00").do(lambda: asyncio.run(post_summary_tweet_job()))
    
    schedule.every().hour.do(lambda: asyncio.run(hourly_job()))
    
    # await post_intro_tweet_job()
    # await post_summary_tweet_job()
    
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())