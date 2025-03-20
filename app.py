from itertools import count
import os
import asyncio
import schedule
from datetime import datetime
from dotenv import load_dotenv
import random

from pymongo import MongoClient
import pytz

from twikit import Client

import logging
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

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
    
    parts = tweet_data.get('parts', [])
    
    return {
        'parts': parts,
        'tweet_id': tweet_data['_id']
    }

async def get_posted_tweets():
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
        zico_id = '1883142650175614976'
        tweets = await client.get_user_tweets(zico_id, 'Tweets')
        
        if tweets:
            for tweet in tweets:
                save_posted_tweet_to_db(tweet)
                print(tweet.text)
                print(f'Posted tweet {tweet.id} saved to database')

    except Exception as e:
        logging.error(f"Error in get_posted_tweets: {e}")
        await asyncio.sleep(5)

async def get_tweet_by_id(id):
    tweet = await client.get_tweet_by_id(id)

    print_formated_tweet(tweet)
    return tweet

async def post_intro_tweet_job():
    print("running intro tweet job")
    
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
    print("running summary tweet job")
    
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
            last_tweet_id = None
            for part in tweet_data['parts']:
                max_attempts = 3
                attempt = 0
                post_success = False
                
                while attempt < max_attempts and not post_success:
                    attempt += 1
                    try:
                        print(f"Posting tweet part (attempt {attempt}/{max_attempts})...")
                        new_tweet = await client.create_tweet(part, reply_to=last_tweet_id)
                        
                        if new_tweet and hasattr(new_tweet, 'id') and new_tweet.id:
                            last_tweet_id = new_tweet.id
                            print(f'Tweet part posted successfully (attempt {attempt})')
                            post_success = True
                        else:
                            print(f"Tweet post attempt {attempt} failed: No valid tweet ID returned")
                            if attempt < max_attempts:
                                print(f"Waiting 10 seconds before retry...")
                                await asyncio.sleep(10)
                    except Exception as e:
                        print(f"Error posting tweet (attempt {attempt}): {str(e)}")
                        if attempt < max_attempts:
                            print(f"Waiting 10 seconds before retry...")
                            await asyncio.sleep(10)
                
                if not post_success:
                    raise Exception(f"Failed to post tweet part after {max_attempts} attempts")
                
                human_delay = random.uniform(5, 10)
                print(f"Waiting {human_delay:.2f} seconds before next post...")
                await asyncio.sleep(human_delay)
            
            tweets_zico_collection.update_one(
                {'_id': tweet_data['tweet_id']},
                {'$set': {'posted': True}}
            )
            
            await get_posted_tweets()
            
    except Exception as e:
        print(f"Error in tweet job: {e}")

async def hourly_job():
    print("running hourly job")
    
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

def should_run_task(scheduled_utc_hour: int) -> bool:
    """
    Verifica se a task deve rodar baseado na hora UTC especificada
    """
    utc_now = datetime.now(pytz.UTC)
    return utc_now.hour == scheduled_utc_hour

async def main():
    running = True
    
    def signal_handler():
        nonlocal running
        running = False
        logging.info("Stopping scheduler...")
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)


    schedule.every().hour.at(":00").do(lambda: asyncio.create_task(hourly_job()))
    schedule.every().hour.at(":00").do(lambda: asyncio.create_task(get_posted_tweets()))
    schedule.every().hour.at(":30").do(lambda: should_run_task(6) and asyncio.create_task(post_summary_tweet_job()))
    schedule.every().hour.at(":30").do(lambda: should_run_task(12) and asyncio.create_task(post_summary_tweet_job()))
    schedule.every().hour.at(":30").do(lambda: should_run_task(18) and asyncio.create_task(post_summary_tweet_job()))
    schedule.every().hour.at(":30").do(lambda: should_run_task(22) and asyncio.create_task(post_summary_tweet_job()))
    await post_summary_tweet_job()
    
    while running:
        try:
            schedule.run_pending()
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())