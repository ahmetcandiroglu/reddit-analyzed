# Implementation of Reddit API crawler for CS 425 Web-Scale Data Course Project
# The aim is to collect users and active subreddits they commented on.

# In order to be fair to all subreddits, crawler first picks a random subreddit and
# then a random post on that subreddit. The number of randomly picked posts can be changed.
# Finally, we get top 50 comments (if exists) and save the user, subreddit tuple into the database.

# Note: This module writes the data on a MySQL database because I ran it for 2 weeks on a remote machine.
# However, you can import your module instead of database module to use txt file or anything else.


import praw
from praw.exceptions import ClientException

import database
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT


# Connect to the database
connection = database.connect_db()
print('Connected to the database.')


# Init PRAW instance
# PRAW is a wrapper library for Reddit API. For detailed information visit following link.
# https://praw.readthedocs.io/en/latest/
reddit = praw.Reddit(user_agent=USER_AGENT, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)


# Loop until you collect enough data
while True:
    # Get a random subreddit
    try:
        subreddit = reddit.subreddit('random')

    except ClientException:
        print('There is some silly error, dunno why...')
        continue

    # Get a random post
    post = subreddit.random()
    post_id = post.id
    print(f'Random post ID: {post_id}')

    # Check the post has already been processed or has enough comments.
    # Try to find a new useful post 10 times then leave subreddit.
    exists = database.check_post(connection, post_id)

    comments = post.comments.list()
    comment_threshold = 1

    try_threshold = 10
    num_tries = 0
    while exists > 0 or len(comments) < comment_threshold:
        post = subreddit.random()
        post_id = post.id
        exists = database.check_post(connection, post_id)
        comments = post.comments.list()

        num_tries += 1
        if num_tries > try_threshold:
            print(f"Tried {num_tries} posts, now leaving the subreddit...")
            break

    if len(comments) < comment_threshold:
        continue

    # Get post details
    title = post.title
    sub_name = post.subreddit.display_name
    score = post.score
    nsfw = 1 if (post.over_18 is True) else 0
    post.comment_sort = 'top'

    try:
        username = post.author.name
    except AttributeError:
        username = "[deleted]"

    print(f"@{sub_name} - {title} [NSFW: {nsfw}] ({post_id})")

    # Insert the post
    database.insert_post(connection=connection,
                         post_id=post_id,
                         username=username,
                         sub_name=sub_name,
                         title=title,
                         score=score,
                         nsfw=nsfw)

    # Get top 100 comments of that post
    for comment in comments[:100]:
        try:
            username = comment.author.name
        except AttributeError:
            username = "[deleted]"

        comment_id = comment.id

        # Insert comment
        database.insert_comment(connection=connection,
                                comment_id=comment_id,
                                post_id=post_id,
                                username=username)

    # Commit the post and comments
    connection.commit()


# Close the connection at the end
connection.close()

