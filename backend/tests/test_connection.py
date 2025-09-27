import praw
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create Reddit instance
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Test the connection
try:
    # Try to get a subreddit
    subreddit = reddit.subreddit("python")
    print(f"✅ Connected to Reddit successfully!")
    print(f"Subreddit: r/{subreddit.display_name}")
    print(f"Subscribers: {subreddit.subscribers:,}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
